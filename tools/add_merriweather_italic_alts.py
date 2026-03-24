# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import argparse
import unicodedata as ud

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont


DEFAULT_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix.ttf")
DEFAULT_ITALIC = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Italic.ttf")
DEFAULT_OUTPUT = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-ItalicAlt.ttf")

LATIN_BLOCKS = [
    (0x0041, 0x005A),  # Latin uppercase
    (0x0061, 0x007A),  # Latin lowercase
    (0x00C0, 0x00FF),  # Latin-1 Supplement letters
    (0x0100, 0x017F),  # Latin Extended-A
    (0x0180, 0x024F),  # Latin Extended-B
]

WESTERN_SYMBOL_BLOCKS = [
    (0x0021, 0x007E),  # Basic Latin printable ASCII
    (0x00A1, 0x00BF),  # Latin-1 punctuation/symbols
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Merriweather italic Latin alternates into a merged KlarMin font."
    )
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--italic", type=Path, default=DEFAULT_ITALIC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--feature-tag", default="ss20")
    parser.add_argument("--suffix", default=".merriitalic")
    return parser.parse_args()


def in_ranges(codepoint: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= codepoint <= end for start, end in ranges)


def is_latin_letter(codepoint: int) -> bool:
    if not in_ranges(codepoint, LATIN_BLOCKS):
        return False
    return ud.category(chr(codepoint)).startswith("L")


def is_italic_alt_target(codepoint: int) -> bool:
    category = ud.category(chr(codepoint))
    if is_latin_letter(codepoint):
        return True
    if 0x0030 <= codepoint <= 0x0039:
        return True
    if in_ranges(codepoint, WESTERN_SYMBOL_BLOCKS) and (category.startswith("P") or category.startswith("S")):
        return True
    return False


def unique_glyph_name(font: TTFont, preferred: str) -> str:
    existing = set(font.getGlyphOrder())
    if preferred not in existing:
        return preferred
    index = 2
    while True:
        candidate = f"{preferred}.{index}"
        if candidate not in existing:
            return candidate
        index += 1


def ensure_tables(dst: TTFont, src: TTFont) -> None:
    if "glyf" not in dst or "hmtx" not in dst:
        raise ValueError("Target font must contain glyf and hmtx tables.")
    if "vmtx" not in dst and "vmtx" in src:
        dst["vmtx"] = deepcopy(src["vmtx"])
        dst["vhea"] = deepcopy(src["vhea"])


def copy_glyph_recursive(
    src: TTFont,
    dst: TTFont,
    src_name: str,
    rename_map: dict[str, str],
    suffix: str,
) -> str:
    if src_name in rename_map:
        return rename_map[src_name]

    preferred_name = f"{src_name}{suffix}"
    dst_name = unique_glyph_name(dst, preferred_name)
    rename_map[src_name] = dst_name

    src_glyph = deepcopy(src["glyf"][src_name])
    if src_glyph.isComposite():
        for component in src_glyph.components:
            component.glyphName = copy_glyph_recursive(
                src, dst, component.glyphName, rename_map, suffix
            )

    dst["glyf"][dst_name] = src_glyph
    dst["hmtx"].metrics[dst_name] = src["hmtx"].metrics[src_name]

    if "vmtx" in dst and "vmtx" in src and src_name in src["vmtx"].metrics:
        dst["vmtx"].metrics[dst_name] = src["vmtx"].metrics[src_name]

    return dst_name


def collect_substitutions(target: TTFont, italic: TTFont, suffix: str) -> tuple[list[tuple[str, str]], int]:
    target_cmap = target.getBestCmap()
    italic_cmap = italic.getBestCmap()
    rename_map: dict[str, str] = {}
    substitutions: list[tuple[str, str]] = []

    for codepoint in sorted(set(target_cmap) & set(italic_cmap)):
        if not is_italic_alt_target(codepoint):
            continue

        base_name = target_cmap[codepoint]
        italic_name = italic_cmap[codepoint]
        alt_name = copy_glyph_recursive(italic, target, italic_name, rename_map, suffix)
        substitutions.append((base_name, alt_name))

    return substitutions, len(rename_map)


def build_feature_text(feature_tag: str, substitutions: list[tuple[str, str]]) -> str:
    lines = [f"feature {feature_tag} {{"]
    for base_name, alt_name in substitutions:
        lines.append(f"    sub {base_name} by {alt_name};")
    lines.append(f"}} {feature_tag};")
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    target = TTFont(str(args.target))
    italic = TTFont(str(args.italic))
    ensure_tables(target, italic)

    substitutions, glyphs_added = collect_substitutions(target, italic, args.suffix)
    if not substitutions:
        raise SystemExit("No matching Latin glyphs found for italic alternates.")

    feature_text = build_feature_text(args.feature_tag, substitutions)
    addOpenTypeFeaturesFromString(target, feature_text)

    target.save(str(args.output))
    print(f"Feature tag: {args.feature_tag}")
    print(f"Substitutions added: {len(substitutions)}")
    print(f"Glyphs added: {glyphs_added}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
