# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import unicodedata as ud

from fontTools.ttLib import TTFont, TTCollection, TTLibFileIsCollectionError


DEFAULT_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-ItalicAlt-v2.ttf")
DEFAULT_REPORT = Path(r"D:\OneDrive\project\UDminchoModified\font_coverage_audit.txt")

DEFAULT_REFS = [
    ("GenKiMin2TW-R", r"D:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf", None),
    ("Merriweather-Regular", r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Regular.ttf", None),
    ("Merriweather-Italic", r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Italic.ttf", None),
    ("TRWUDMincho-R", r"D:\OneDrive\project\UDminchoModified\referenceFont\TRWUDMincho-R.ttf", None),
    ("GenYoMin2-R#0", r"D:\OneDrive\project\UDminchoModified\referenceFont\GenYoMin2-R.ttc", 0),
]

BLOCKS = [
    ("Latin Extended-B", 0x0180, 0x024F),
    ("Spacing Modifier Letters", 0x02B0, 0x02FF),
    ("Combining Diacritical Marks", 0x0300, 0x036F),
    ("Latin Extended Additional", 0x1E00, 0x1EFF),
    ("General Punctuation", 0x2000, 0x206F),
    ("Superscripts and Subscripts", 0x2070, 0x209F),
    ("Combining Marks for Symbols", 0x20D0, 0x20FF),
    ("Arrows", 0x2190, 0x21FF),
    ("Math Operators", 0x2200, 0x22FF),
    ("Dingbats", 0x2700, 0x27BF),
    ("Misc Symbols and Arrows", 0x2B00, 0x2BFF),
    ("Hangul Compatibility Jamo", 0x3130, 0x318F),
    ("Bopomofo Extended", 0x31A0, 0x31BF),
    ("CJK Unified Ideographs Ext A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("Hangul Syllables", 0xAC00, 0xD7AF),
    ("CJK Compatibility Ideographs", 0xF900, 0xFAFF),
]

LOW_PRIORITY_BLOCKS = {
    "CJK Unified Ideographs",
    "CJK Unified Ideographs Ext A",
    "Hangul Syllables",
    "Hangul Compatibility Jamo",
    "CJK Compatibility Ideographs",
    "Other",
}


@dataclass
class FontRef:
    label: str
    path: Path
    font_number: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit target font coverage against reference fonts.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def load_font(path: Path, font_number: int | None = None):
    if font_number is not None:
        return TTFont(str(path), fontNumber=font_number)
    try:
        return TTFont(str(path))
    except TTLibFileIsCollectionError:
        collection = TTCollection(str(path))
        return collection.fonts[0]


def block_name(codepoint: int) -> str:
    for name, start, end in BLOCKS:
        if start <= codepoint <= end:
            return name
    return "Other"


def is_printable(codepoint: int) -> bool:
    return not ud.category(chr(codepoint)).startswith("C")


def format_cp(codepoint: int) -> str:
    return f"U+{codepoint:04X}\t{ud.category(chr(codepoint))}\t{ud.name(chr(codepoint), 'UNNAMED')}"


def mapped_empty_glyphs(font: TTFont) -> list[tuple[int, str]]:
    cmap = font.getBestCmap()
    if "glyf" not in font:
        return []
    glyf_table = font["glyf"]
    empty = []
    for codepoint, glyph_name in cmap.items():
        glyph = glyf_table[glyph_name]
        if glyph.isComposite():
            continue
        contours = getattr(glyph, "numberOfContours", 0)
        coords = len(glyph.coordinates) if hasattr(glyph, "coordinates") else 0
        if contours == 0 and coords == 0:
            empty.append((codepoint, glyph_name))
    return empty


def summarize_missing(target_cmap: dict[int, str], ref_cmap: dict[int, str]) -> tuple[list[int], dict[str, int]]:
    missing = [cp for cp in sorted(set(ref_cmap) - set(target_cmap)) if is_printable(cp)]
    counts: dict[str, int] = {}
    for codepoint in missing:
        name = block_name(codepoint)
        counts[name] = counts.get(name, 0) + 1
    return missing, counts


def high_priority_candidates(missing: list[int]) -> list[int]:
    return [cp for cp in missing if block_name(cp) not in LOW_PRIORITY_BLOCKS]


def build_report(target_path: Path, target_font: TTFont, refs: list[FontRef]) -> str:
    lines: list[str] = []
    target_cmap = target_font.getBestCmap()

    lines.append(f"Target: {target_path}")
    lines.append(f"Unicode cmap count: {len(target_cmap)}")
    lines.append(f"Glyph count: {target_font['maxp'].numGlyphs}")
    lines.append("")

    empty = mapped_empty_glyphs(target_font)
    lines.append("Mapped empty glyphs:")
    if empty:
        for codepoint, glyph_name in empty:
            lines.append(f"  U+{codepoint:04X}\t{glyph_name}\t{ud.name(chr(codepoint), 'UNNAMED')}")
    else:
        lines.append("  none")
    lines.append("")

    union_missing: set[int] = set()
    for ref in refs:
        ref_font = load_font(ref.path, ref.font_number)
        missing, counts = summarize_missing(target_cmap, ref_font.getBestCmap())
        union_missing.update(missing)
        lines.append(f"[{ref.label}] printable chars present in ref but missing in target: {len(missing)}")
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]:
            lines.append(f"  {name}: {count}")
        candidates = high_priority_candidates(missing)
        if candidates:
            lines.append("  Sample high-priority addable chars:")
            for codepoint in candidates[:20]:
                lines.append(f"    {format_cp(codepoint)}")
        else:
            lines.append("  No obvious high-priority printable additions.")
        lines.append("")

    lines.append("[Union of all refs] high-priority candidate chars missing in target:")
    union_candidates = sorted(high_priority_candidates(sorted(union_missing)))
    if union_candidates:
        for codepoint in union_candidates[:80]:
            lines.append(f"  {format_cp(codepoint)}")
    else:
        lines.append("  none")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    refs = [FontRef(label, Path(path), font_number) for label, path, font_number in DEFAULT_REFS]
    target_font = load_font(args.target)
    report = build_report(args.target, target_font, refs)
    args.report.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report written to: {args.report}")


if __name__ == "__main__":
    main()
