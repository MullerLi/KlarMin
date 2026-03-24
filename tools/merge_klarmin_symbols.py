# -*- coding: utf-8 -*-
"""
Merge punctuation/symbol glyphs into KlarMinTC-Regular.ttf.

Pass 1:
    Replace CJK punctuation, bopomofo, and symbol-related blocks in the base
    font with glyphs from GenKiMin2TW-R.otf.

Pass 2:
    Replace non-CJK punctuation/symbol code points in the base font with
    glyphs from Merriweather-Regular.ttf.

This script prefers FontForge's Python API because it can safely copy glyphs
between fonts and regenerate a working font file. Run it with either:

    python merge_klarmin_symbols.py

or:

    fontforge -lang=py -script merge_klarmin_symbols.py
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import unicodedata as ud

try:
    import fontforge
except ImportError:
    raise SystemExit(
        "Cannot import fontforge.\n"
        "Run this script with FontForge:\n"
        "  fontforge -lang=py -script merge_klarmin_symbols.py\n"
        "or install a Python environment that can import fontforge."
    )

try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None


DEFAULT_GENKI = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf")
DEFAULT_MERRI = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Regular.ttf")
DEFAULT_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular.ttf")

GENKI_RANGES = [
    (0x2000, 0x206F),  # General Punctuation
    (0x2100, 0x214F),  # Letterlike Symbols
    (0x2190, 0x22FF),  # Arrows + Math Operators
    (0x2300, 0x23FF),  # Misc Technical
    (0x2460, 0x24FF),  # Enclosed Alphanumerics
    (0x2500, 0x257F),  # Box Drawing
    (0x2580, 0x259F),  # Block Elements
    (0x25A0, 0x25FF),  # Geometric Shapes
    (0x2600, 0x26FF),  # Misc Symbols
    (0x2700, 0x27BF),  # Dingbats
    (0x2E00, 0x2E7F),  # Supplemental Punctuation
    (0x3000, 0x303F),  # CJK Symbols and Punctuation
    (0x3100, 0x312F),  # Bopomofo
    (0x31A0, 0x31BF),  # Bopomofo Extended
    (0x3200, 0x32FF),  # Enclosed CJK Letters and Months
    (0xFE10, 0xFE1F),  # Vertical Forms
    (0xFE30, 0xFE4F),  # CJK Compatibility Forms
    (0xFF00, 0xFFEF),  # Halfwidth and Fullwidth Forms
]

GENKI_EXTRA_CODEPOINTS = {
    0x02CA,  # MODIFIER LETTER ACUTE ACCENT
    0x02CB,  # MODIFIER LETTER GRAVE ACCENT
}

CJK_SPECIFIC_RANGES = [
    (0x3000, 0x303F),
    (0x3100, 0x312F),
    (0x31A0, 0x31BF),
    (0x3200, 0x32FF),
    (0xFE10, 0xFE4F),
    (0xFF00, 0xFFEF),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge symbol and punctuation glyphs into KlarMinTC-Regular.ttf"
    )
    parser.add_argument("--genki", type=Path, default=DEFAULT_GENKI)
    parser.add_argument("--merri", type=Path, default=DEFAULT_MERRI)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output font path. Default: <target stem>-GenKiMerriMix.ttf",
    )
    parser.add_argument(
        "--sfd-output",
        type=Path,
        default=None,
        help="Optional SFD backup path. Default: <target stem>-GenKiMerriMix.sfd",
    )
    parser.add_argument(
        "--log-output",
        type=Path,
        default=None,
        help="Optional log path. Default: <target stem>-GenKiMerriMix-log.txt",
    )
    return parser.parse_args()


def in_ranges(codepoint: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= codepoint <= end for start, end in ranges)


def is_genki_target(codepoint: int) -> bool:
    return codepoint in GENKI_EXTRA_CODEPOINTS or in_ranges(codepoint, GENKI_RANGES)


def is_cjk_specific(codepoint: int) -> bool:
    return in_ranges(codepoint, CJK_SPECIFIC_RANGES)


def is_western_punct_or_symbol(codepoint: int) -> bool:
    if codepoint < 0 or is_cjk_specific(codepoint):
        return False
    category = ud.category(chr(codepoint))
    return category.startswith("P") or category.startswith("S")


def validate_paths(*paths: Path) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing font file(s):\n" + "\n".join(missing))


def output_paths(target_path: Path, output: Path | None, sfd_output: Path | None, log_output: Path | None) -> tuple[Path, Path, Path]:
    stem = target_path.stem + "-GenKiMerriMix"
    font_output = output or target_path.with_name(stem + ".ttf")
    sfd_backup = sfd_output or target_path.with_name(stem + ".sfd")
    log_path = log_output or target_path.with_name(stem + "-log.txt")
    return font_output, sfd_backup, log_path


def select_unicode(font, codepoint: int) -> None:
    font.selection.none()
    font.selection.select(("unicode",), codepoint)


def first_selected_glyph(font):
    for glyph in font.selection.byGlyphs:
        return glyph
    return None


def ensure_char(dst_font, codepoint: int):
    glyph_name = fontforge.nameFromUnicode(codepoint)
    if not glyph_name:
        glyph_name = f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:X}"
    return dst_font.createChar(codepoint, glyph_name)


def prepare_source_font(src_font) -> None:
    src_font.selection.none()
    src_font.selection.all()
    src_font.unlinkReferences()
    src_font.selection.none()


def copy_unicode_glyph(src_font, dst_font, codepoint: int) -> tuple[bool, str]:
    if src_font.findEncodingSlot(codepoint) == -1:
        return False, "source-missing"

    ensure_char(dst_font, codepoint)

    select_unicode(src_font, codepoint)
    src_glyph = first_selected_glyph(src_font)
    if src_glyph is None:
        return False, "source-selection-empty"

    src_font.copy()

    select_unicode(dst_font, codepoint)
    dst_font.paste()
    dst_glyph = first_selected_glyph(dst_font)
    if dst_glyph is None:
        return False, "paste-failed"

    try:
        dst_glyph.width = src_glyph.width
    except Exception:
        pass

    try:
        dst_glyph.vwidth = src_glyph.vwidth
    except Exception:
        pass

    return True, "ok"


def collect_genki_codepoints(font) -> list[int]:
    codepoints = set()
    for glyph in font.glyphs():
        if glyph.unicode >= 0 and is_genki_target(glyph.unicode):
            codepoints.add(glyph.unicode)
    for codepoint in GENKI_EXTRA_CODEPOINTS:
        if font.findEncodingSlot(codepoint) != -1:
            codepoints.add(codepoint)
    return sorted(codepoints)


def collect_merri_codepoints(font) -> list[int]:
    codepoints = set()
    for glyph in font.glyphs():
        if glyph.unicode >= 0 and is_western_punct_or_symbol(glyph.unicode):
            codepoints.add(glyph.unicode)
    return sorted(codepoints)


def rename_output_font(font) -> None:
    for attr, suffix in (
        ("fontname", "-GenKiMerriMix"),
        ("familyname", " GenKiMerriMix"),
        ("fullname", " GenKiMerriMix"),
    ):
        try:
            setattr(font, attr, getattr(font, attr) + suffix)
        except Exception:
            pass


def scale_generated_ttf(
    ttf_path: Path,
    codepoints: list[int],
    scale: float,
    log_lines: list[str],
) -> tuple[int, int]:
    if TTFont is None:
        log_lines.append("POST\tfontTools unavailable, skipped generated TTF scaling")
        return 0, len(codepoints)

    if scale == 1.0:
        log_lines.append("POST\tNo scaling needed for generated TTF")
        return 0, 0

    font = TTFont(str(ttf_path))
    cmap = font.getBestCmap()
    glyf_table = font["glyf"]
    hmtx_table = font["hmtx"].metrics
    vmtx_table = font["vmtx"].metrics if "vmtx" in font else None

    scaled = 0
    skipped = 0
    processed_names: set[str] = set()

    for codepoint in codepoints:
        glyph_name = cmap.get(codepoint)
        if not glyph_name or glyph_name in processed_names:
            continue

        glyph = glyf_table[glyph_name]

        if glyph.isComposite():
            for component in glyph.components:
                component.x = int(round(component.x * scale))
                component.y = int(round(component.y * scale))
            glyph.recalcBounds(glyf_table)
        elif getattr(glyph, "numberOfContours", 0) > 0 and hasattr(glyph, "coordinates"):
            glyph.coordinates.scale((scale, scale))
            glyph.recalcBounds(glyf_table)
        else:
            skipped += 1
            log_lines.append(f"POST\tU+{codepoint:04X}\t{glyph_name}\tskipped-empty")
            processed_names.add(glyph_name)
            continue

        advance_width, left_side_bearing = hmtx_table[glyph_name]
        hmtx_table[glyph_name] = (
            int(round(advance_width * scale)),
            int(round(left_side_bearing * scale)),
        )

        if vmtx_table and glyph_name in vmtx_table:
            advance_height, top_side_bearing = vmtx_table[glyph_name]
            vmtx_table[glyph_name] = (
                int(round(advance_height * scale)),
                int(round(top_side_bearing * scale)),
            )

        scaled += 1
        processed_names.add(glyph_name)
        log_lines.append(f"POST\tU+{codepoint:04X}\t{glyph_name}\tscaled-x{scale:.4f}")

    font.save(str(ttf_path))
    return scaled, skipped


def run_pass(pass_name: str, source_font, target_font, codepoints: list[int], log_lines: list[str]) -> int:
    copied = 0
    log_lines.append(pass_name)
    for codepoint in codepoints:
        ok, status = copy_unicode_glyph(source_font, target_font, codepoint)
        display = chr(codepoint) if codepoint <= sys.maxunicode else ""
        source_label = "GENKI" if "GenKi" in pass_name else "MERRI"
        log_lines.append(f"{source_label}\tU+{codepoint:04X}\t{display}\t{status}")
        if ok:
            copied += 1
    log_lines.append("")
    return copied


def main() -> None:
    args = parse_args()
    validate_paths(args.genki, args.merri, args.target)
    out_ttf, out_sfd, out_log = output_paths(args.target, args.output, args.sfd_output, args.log_output)

    print("Opening fonts...")
    genki = fontforge.open(str(args.genki))
    merri = fontforge.open(str(args.merri))
    target = fontforge.open(str(args.target))

    prepare_source_font(genki)
    prepare_source_font(merri)
    rename_output_font(target)

    genki_codepoints = collect_genki_codepoints(genki)
    merri_codepoints = collect_merri_codepoints(merri)

    log_lines: list[str] = []
    genki_copied = run_pass(
        "=== PASS 1: GenKiMin2TW-R.otf -> CJK punctuation / symbols / bopomofo ===",
        genki,
        target,
        genki_codepoints,
        log_lines,
    )
    merri_copied = run_pass(
        "=== PASS 2: Merriweather-Regular.ttf -> non-CJK punctuation / symbols ===",
        merri,
        target,
        merri_codepoints,
        log_lines,
    )

    print(f"Saving SFD backup -> {out_sfd}")
    target.save(str(out_sfd))

    print(f"Generating merged font -> {out_ttf}")
    target.generate(str(out_ttf), flags=("opentype", "dummy-dsig", "round"))

    genki_scale = float(target.em) / float(genki.em) if genki.em and target.em else 1.0
    post_scaled, post_skipped = scale_generated_ttf(out_ttf, genki_codepoints, genki_scale, log_lines)

    summary = [
        "=== SUMMARY ===",
        f"GenKi pass copied: {genki_copied}/{len(genki_codepoints)}",
        f"Merri pass copied: {merri_copied}/{len(merri_codepoints)}",
        f"Post-scale applied: {post_scaled}, skipped: {post_skipped}, factor: {genki_scale:.4f}",
        f"Output TTF: {out_ttf}",
        f"Output SFD: {out_sfd}",
    ]
    log_lines.extend(summary)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print("\n".join(summary))
    print(f"Log file -> {out_log}")

    genki.close()
    merri.close()
    target.close()


if __name__ == "__main__":
    main()
