from __future__ import annotations

import argparse
import hashlib
import html
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTCollection, TTFont


PUNCT_MUST = [
    0x3001, 0x3002, 0x3008, 0x3009, 0x300A, 0x300B, 0x300C, 0x300D,
    0x300E, 0x300F, 0x3010, 0x3011, 0xFF01, 0xFF08, 0xFF09, 0xFF0C,
    0xFF1A, 0xFF1B, 0xFF1F, 0x2014, 0x2026, 0x00B7,
]

PUNCT_RECOMMENDED = [
    0x3014, 0x3015, 0x3016, 0x3017, 0xFF0E, 0xFF3B, 0xFF3D, 0xFF5E,
    0x2015, 0x2027, 0x30FB,
]

PUNCT_OPTIONAL = [
    0x301D, 0x301E, 0xFF5B, 0xFF5D, 0x2018, 0x2019, 0x201C, 0x201D,
]

VERTICAL_COMPAT = [
    0xFE30, 0xFE31, 0xFE32, 0xFE33, 0xFE35, 0xFE36, 0xFE37, 0xFE38,
    0xFE39, 0xFE3A, 0xFE3B, 0xFE3C, 0xFE3D, 0xFE3E, 0xFE3F, 0xFE40,
    0xFE41, 0xFE42, 0xFE43, 0xFE44, 0xFE4F,
]

BOPOMOFO_GROUPS = {
    "bopo.onset": [*range(0x3105, 0x3113), 0x312B, 0x31A0, 0x31A1, 0x31A2, 0x31A3],
    "bopo.empty_rhyme_onset": [*range(0x3113, 0x311A)],
    "bopo.medial": [0x3127, 0x3128, 0x3129],
    "bopo.rhyme": [
        *range(0x311A, 0x3127), 0x31A4, 0x31A5, 0x31A6, 0x31A7, 0x31A9, 0x31AA,
        0x31AB, 0x31AC, 0x31AD, 0x31AE, 0x31AF, 0x31B0, 0x31B1, 0x31B2,
    ],
    "bopo.tone_light": [0x02D9],
    "bopo.tone_mandarin": [0x02CA, 0x02C7, 0x02CB],
    "bopo.tone_dialect": [0x02EA, 0x02EB],
    "bopo.entering_coda": [0x31B4, 0x31B5, 0x31B7, 0x31BB],
    "bopo.yang_entering": [0x0307],
    "bopo.light_reading": [0x0358],
}

SECTIONS = [
    ("punct.must", PUNCT_MUST),
    ("punct.recommended", PUNCT_RECOMMENDED),
    ("punct.optional", PUNCT_OPTIONAL),
    ("punct.vertical", VERTICAL_COMPAT),
    *BOPOMOFO_GROUPS.items(),
]

PROBLEMATIC_FEATURES = ("halt", "palt", "vhal", "vpal")


@dataclass
class GlyphAction:
    codepoint: int
    category: str
    action: str
    target_name: str | None
    donor_name: str | None
    reason: str = ""


def flatten_unique(groups: Iterable[Iterable[int]]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for group in groups:
        for cp in group:
            if cp not in seen:
                seen.add(cp)
                ordered.append(cp)
    return ordered


ALL_CODEPOINTS = flatten_unique(codepoints for _, codepoints in SECTIONS)
CODEPOINT_TO_CATEGORY = {cp: category for category, group in SECTIONS for cp in group}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--donor-index", type=int, default=0)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--html-donor-font", type=Path)
    parser.add_argument("--max-err", type=float, default=1.0)
    return parser.parse_args()


def open_font(path: Path, index: int = 0) -> TTFont:
    if path.suffix.lower() in {".ttc", ".otc"}:
        return TTCollection(str(path)).fonts[index]
    return TTFont(str(path), recalcBBoxes=True, recalcTimestamp=False)


def outline_format(font: TTFont) -> str:
    if "glyf" in font:
        return "glyf"
    if "CFF " in font:
        return "CFF"
    if "CFF2" in font:
        return "CFF2"
    return "unknown"


def feature_tags(font: TTFont, table_tag: str) -> list[str]:
    if table_tag not in font or not getattr(font[table_tag].table, "FeatureList", None):
        return []
    unique: list[str] = []
    for record in font[table_tag].table.FeatureList.FeatureRecord:
        if record.FeatureTag not in unique:
            unique.append(record.FeatureTag)
    return unique


def format_cp(codepoint: int) -> str:
    return f"U+{codepoint:04X}"


def new_glyph_name(codepoint: int, glyph_order: list[str]) -> str:
    base = f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"
    if base not in glyph_order:
        return base
    suffix = 1
    while f"{base}.{suffix}" in glyph_order:
        suffix += 1
    return f"{base}.{suffix}"


def update_cmap(font: TTFont, codepoint: int, glyph_name: str) -> None:
    for table in font["cmap"].tables:
        if table.isUnicode() and getattr(table, "format", None) != 14:
            table.cmap[codepoint] = glyph_name


def scaled_metrics(metrics: tuple[int, int], scale: float) -> tuple[int, int]:
    return (int(round(metrics[0] * scale)), int(round(metrics[1] * scale)))


def build_tt_glyph(donor: TTFont, donor_name: str, scale: float, max_err: float):
    donor_glyph_set = donor.getGlyphSet()
    recording = DecomposingRecordingPen(donor_glyph_set)
    donor_glyph_set[donor_name].draw(recording)
    tt_pen = TTGlyphPen(None)
    pen = tt_pen
    if outline_format(donor) in {"CFF", "CFF2"}:
        pen = Cu2QuPen(pen, max_err=max_err, reverse_direction=False)
    if scale != 1.0:
        pen = TransformPen(pen, (scale, 0, 0, scale, 0, 0))
    recording.replay(pen)
    return tt_pen.glyph()


def glyph_signature(font: TTFont, glyph_name: str) -> str:
    pen = RecordingPen()
    font.getGlyphSet()[glyph_name].draw(pen)
    payload = repr(
        [(op, tuple(round(v, 4) if isinstance(v, float) else v for v in vals)) for op, vals in pen.value]
    ).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def glyph_bounds(font: TTFont, glyph_name: str):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[glyph_name].draw(pen)
    return pen.bounds


def sample_text(codepoint: int) -> str:
    ch = chr(codepoint)
    if codepoint == 0x02D9:
        return f"{ch}\u311A"
    if codepoint in {0x02CA, 0x02C7, 0x02CB, 0x02EA, 0x02EB}:
        return f"\u311A{ch}"
    if codepoint == 0x0307:
        return f"\u31B4{ch}"
    if codepoint == 0x0358:
        return f"\u3105{ch}"
    punct_count = (
        len(PUNCT_MUST)
        + len(PUNCT_RECOMMENDED)
        + len(PUNCT_OPTIONAL)
        + len(VERTICAL_COMPAT)
    )
    if codepoint in ALL_CODEPOINTS[:punct_count]:
        return f"\u6E2C{ch}\u8A66"
    return ch


def relpath_for_html(html_file: Path, asset_file: Path) -> str:
    return Path(os.path.relpath(asset_file.resolve(), start=html_file.parent.resolve())).as_posix()


def apply_updates(target: TTFont, donor: TTFont, codepoints: list[int], max_err: float):
    scale = target["head"].unitsPerEm / donor["head"].unitsPerEm
    target_cmap = target.getBestCmap()
    donor_cmap = donor.getBestCmap()
    glyph_order = list(target.getGlyphOrder())
    actions: list[GlyphAction] = []

    for codepoint in codepoints:
        category = CODEPOINT_TO_CATEGORY[codepoint]
        donor_name = donor_cmap.get(codepoint)
        target_name = target_cmap.get(codepoint)
        if not donor_name:
            actions.append(GlyphAction(codepoint, category, "skipped", target_name, None, "donor_missing"))
            continue
        action = "replaced"
        if not target_name:
            target_name = new_glyph_name(codepoint, glyph_order)
            glyph_order.append(target_name)
            action = "added"
        target["glyf"][target_name] = build_tt_glyph(donor, donor_name, scale, max_err)
        target["hmtx"].metrics[target_name] = scaled_metrics(donor["hmtx"][donor_name], scale)
        if "vmtx" in target and "vmtx" in donor and donor_name in donor["vmtx"].metrics:
            target["vmtx"].metrics[target_name] = scaled_metrics(donor["vmtx"].metrics[donor_name], scale)
        update_cmap(target, codepoint, target_name)
        target_cmap[codepoint] = target_name
        actions.append(GlyphAction(codepoint, category, action, target_name, donor_name))

    target.setGlyphOrder(glyph_order)
    target["maxp"].numGlyphs = len(glyph_order)
    target["hhea"].numberOfHMetrics = len(target["hmtx"].metrics)
    if "vhea" in target and "vmtx" in target:
        target["vhea"].numberOfVMetrics = len(target["vmtx"].metrics)
    if "OS/2" in target:
        bmp = [cp for cp in target.getBestCmap() if cp <= 0xFFFF]
        target["OS/2"].usFirstCharIndex = min(bmp)
        target["OS/2"].usLastCharIndex = max(bmp)
    return actions


def verify(original: TTFont, output_font: TTFont, donor: TTFont, actions: list[GlyphAction]) -> list[str]:
    original_cmap = original.getBestCmap()
    output_cmap = output_font.getBestCmap()
    donor_cmap = donor.getBestCmap()
    lines = []
    for action in actions:
        cp = action.codepoint
        output_name = output_cmap.get(cp)
        donor_name = donor_cmap.get(cp)
        original_name = original_cmap.get(cp)
        changed = True
        if output_name and original_name:
            changed = glyph_signature(original, original_name) != glyph_signature(output_font, output_name)
        lines.append(
            " ".join(
                [
                    format_cp(cp),
                    f"action={action.action}",
                    f"category={action.category}",
                    f"original={original_name or '-'}",
                    f"output={output_name or '-'}",
                    f"donor={donor_name or '-'}",
                    f"width={original['hmtx'][original_name][0] if original_name else '-'}->{output_font['hmtx'][output_name][0] if output_name else '-'}",
                    f"changed={'yes' if changed else 'no'}",
                    f"bounds={glyph_bounds(output_font, output_name) if output_name else '-'}",
                ]
            )
        )
    return lines


def write_report(path: Path, target_path: Path, donor_path: Path, donor_index: int, original: TTFont, donor: TTFont, output_font: TTFont, actions: list[GlyphAction], verification_lines: list[str]) -> None:
    gs_tags = feature_tags(output_font, "GSUB")
    gp_tags = feature_tags(output_font, "GPOS")
    risky = [tag for tag in PROBLEMATIC_FEATURES if tag in gs_tags or tag in gp_tags]
    lines = [
        f"Target: {target_path}",
        f"Donor: {donor_path}",
        f"Donor index: {donor_index}",
        "Preflight",
        f"  target_upm={original['head'].unitsPerEm}",
        f"  donor_upm={donor['head'].unitsPerEm}",
        f"  target_outline={outline_format(original)}",
        f"  donor_outline={outline_format(donor)}",
        f"  target_yMinMax={original['head'].yMin}/{original['head'].yMax}",
        f"  donor_yMinMax={donor['head'].yMin}/{donor['head'].yMax}",
        "Feature check",
        f"  GSUB={gs_tags}",
        f"  GPOS={gp_tags}",
        f"  problematic_spacing_features={risky if risky else 'none'}",
        "Summary",
        f"  replaced={sum(1 for a in actions if a.action == 'replaced')}",
        f"  added={sum(1 for a in actions if a.action == 'added')}",
        f"  skipped={sum(1 for a in actions if a.action == 'skipped')}",
        "Per-codepoint result",
    ]
    for action in actions:
        lines.append(
            f"{format_cp(action.codepoint)} char={chr(action.codepoint)} category={action.category} "
            f"action={action.action} target={action.target_name or '-'} donor={action.donor_name or '-'} reason={action.reason or '-'}"
        )
    lines.extend(["Verification", *verification_lines])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, output_font_path: Path, target_font_path: Path, display_donor_font: Path | None, actions: list[GlyphAction], original: TTFont, output_font: TTFont) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_href = relpath_for_html(path, output_font_path)
    target_href = relpath_for_html(path, target_font_path)
    donor_href = relpath_for_html(path, display_donor_font) if display_donor_font else None
    original_cmap = original.getBestCmap()
    output_cmap = output_font.getBestCmap()
    rows = []
    for action in actions:
        cp = action.codepoint
        sample = sample_text(cp)
        rows.append(
            "<tr>"
            f"<td>{format_cp(cp)}</td>"
            f"<td>{html.escape(action.category)}</td>"
            f"<td>{html.escape(unicodedata.name(chr(cp), 'UNNAMED'))}</td>"
            f"<td>{html.escape(action.action)}</td>"
            f"<td>{html.escape(sample)}</td>"
            f"<td class=\"out\">{html.escape(sample) if cp in output_cmap else 'missing'}</td>"
            f"<td class=\"orig{' missing' if cp not in original_cmap else ''}\">{html.escape(sample) if cp in original_cmap else 'missing'}</td>"
            + (f"<td class=\"donor\">{html.escape(sample)}</td>" if donor_href else "")
            + "</tr>"
        )
    donor_header = "<th>Display Donor</th>" if donor_href else ""
    donor_face = f"@font-face {{ font-family: 'DisplayDonor'; src: url('{donor_href}'); }}\n" if donor_href else ""
    donor_css = ".donor { font-family: 'DisplayDonor'; font-size: 28px; }\n" if donor_href else ""
    html_text = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>BIZ UD TW Verification</title>
<style>
@font-face {{ font-family: 'OutputFont'; src: url('{output_href}'); }}
@font-face {{ font-family: 'OriginalFont'; src: url('{target_href}'); }}
{donor_face}body {{ font-family: 'Segoe UI', sans-serif; margin: 24px; color: #222; }}
table {{ border-collapse: collapse; width: 100%; table-layout: fixed; }}
th, td {{ border: 1px solid #ccc; padding: 6px 8px; word-break: break-word; }}
th {{ background: #f4f4f4; }}
.out {{ font-family: 'OutputFont'; font-size: 28px; }}
.orig {{ font-family: 'OriginalFont'; font-size: 28px; color: #666; }}
.missing {{ font-size: 14px; color: #999; }}
{donor_css}</style>
</head>
<body>
<h1>BIZ UD TW Verification</h1>
<p>Output vs original target for punctuation, vertical forms, and bopomofo.</p>
<table>
<tr><th>Codepoint</th><th>Category</th><th>Name</th><th>Action</th><th>Sample</th><th>Output</th><th>Original</th>{donor_header}</tr>
{''.join(rows)}
</table>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    original = TTFont(str(args.target), recalcBBoxes=True, recalcTimestamp=False)
    target = TTFont(str(args.target), recalcBBoxes=True, recalcTimestamp=False)
    donor = open_font(args.donor, args.donor_index)
    actions = apply_updates(target, donor, ALL_CODEPOINTS, args.max_err)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    target.save(str(args.output))
    target.close()
    output_font = TTFont(str(args.output), recalcBBoxes=True, recalcTimestamp=False)
    verification_lines = verify(original, output_font, donor, actions)
    if args.report:
        write_report(args.report, args.target, args.donor, args.donor_index, original, donor, output_font, actions, verification_lines)
    if args.html:
        display_donor = args.html_donor_font
        if display_donor is None and args.donor.suffix.lower() not in {".ttc", ".otc"}:
            display_donor = args.donor
        write_html(args.html, args.output, args.target, display_donor, actions, original, output_font)
    replaced = sum(1 for a in actions if a.action == "replaced")
    added = sum(1 for a in actions if a.action == "added")
    risky = [tag for tag in PROBLEMATIC_FEATURES if tag in feature_tags(output_font, "GSUB") or tag in feature_tags(output_font, "GPOS")]
    print(f"Target: {args.target}")
    print(f"Donor: {args.donor}#{args.donor_index}")
    print(f"Output: {args.output}")
    print(f"Preflight: target_upm={original['head'].unitsPerEm} donor_upm={donor['head'].unitsPerEm} target_outline={outline_format(original)} donor_outline={outline_format(donor)}")
    print(f"Summary: replaced={replaced} added={added} skipped={sum(1 for a in actions if a.action == 'skipped')}")
    print("Feature check: " + (",".join(risky) if risky else "none"))
    if args.report:
        print(f"Report: {args.report}")
    if args.html:
        print(f"HTML: {args.html}")
    output_font.close()
    original.close()
    donor.close()


if __name__ == "__main__":
    main()
