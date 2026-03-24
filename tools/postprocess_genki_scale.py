# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import argparse
import unicodedata as ud

from fontTools.ttLib import TTFont


DEFAULT_GENKI = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf")
DEFAULT_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular.ttf")
DEFAULT_MERGED = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix.ttf")

GENKI_RANGES = [
    (0x2000, 0x206F),
    (0x2100, 0x214F),
    (0x2190, 0x22FF),
    (0x2300, 0x23FF),
    (0x2460, 0x24FF),
    (0x2500, 0x257F),
    (0x2580, 0x259F),
    (0x25A0, 0x25FF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
    (0x2E00, 0x2E7F),
    (0x3000, 0x303F),
    (0x3100, 0x312F),
    (0x31A0, 0x31BF),
    (0x3200, 0x32FF),
    (0xFE10, 0xFE1F),
    (0xFE30, 0xFE4F),
    (0xFF00, 0xFFEF),
]

GENKI_EXTRA_CODEPOINTS = {
    0x02CA,
    0x02CB,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scale GenKi-derived glyphs in merged KlarMin output")
    parser.add_argument("--genki", type=Path, default=DEFAULT_GENKI)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--merged", type=Path, default=DEFAULT_MERGED)
    parser.add_argument(
        "--codepoints-file",
        type=Path,
        default=None,
        help="Optional text file with one hexadecimal codepoint per line.",
    )
    return parser.parse_args()


def in_ranges(codepoint: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= codepoint <= end for start, end in ranges)


def is_genki_target(codepoint: int) -> bool:
    return codepoint in GENKI_EXTRA_CODEPOINTS or in_ranges(codepoint, GENKI_RANGES)


def collect_genki_codepoints(genki_path: Path) -> list[int]:
    genki_font = TTFont(str(genki_path))
    cmap = genki_font.getBestCmap()
    return sorted(cp for cp in cmap if is_genki_target(cp))


def load_codepoints_from_file(path: Path) -> list[int]:
    codepoints: list[int] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("u+"):
            line = line[2:]
        codepoints.append(int(line, 16))
    return sorted(set(codepoints))


def scale_glyphs_in_ttf(merged_path: Path, codepoints: list[int], scale: float) -> tuple[int, int]:
    font = TTFont(str(merged_path))
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

    font.save(str(merged_path))
    return scaled, skipped


def main() -> None:
    args = parse_args()
    genki_upm = TTFont(str(args.genki))["head"].unitsPerEm
    target_upm = TTFont(str(args.target))["head"].unitsPerEm
    scale = float(target_upm) / float(genki_upm)
    if args.codepoints_file:
        codepoints = load_codepoints_from_file(args.codepoints_file)
    else:
        codepoints = collect_genki_codepoints(args.genki)
    scaled, skipped = scale_glyphs_in_ttf(args.merged, codepoints, scale)
    print(f"Scale factor: {scale:.4f}")
    print(f"Codepoints requested: {len(codepoints)}")
    print(f"Scaled glyphs: {scaled}")
    print(f"Skipped glyphs: {skipped}")
    print(f"Output: {args.merged}")


if __name__ == "__main__":
    main()
