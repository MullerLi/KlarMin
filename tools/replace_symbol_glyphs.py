import argparse
import copy
from pathlib import Path

from fontTools.ttLib import TTFont


DEFAULT_CODEPOINTS = [
    0x2026,  # …
    0x2013,  # –
    0x2014,  # —
    0x2105,  # ℅
    0x2190,  # ←
    0x2191,  # ↑
    0x2192,  # →
    0x2193,  # ↓
    0x2215,  # ∕
    0x221A,  # √
    0x221E,  # ∞
    0x222B,  # ∫
    0x2260,  # ≠
    0x201C,  # “
    0x201D,  # ”
    0x2018,  # ‘
    0x2019,  # ’
]


def parse_codepoints(raw_values):
    if not raw_values:
        return DEFAULT_CODEPOINTS
    codepoints = []
    for raw in raw_values:
        value = raw.strip().upper()
        if value.startswith("U+"):
            value = value[2:]
        codepoints.append(int(value, 16))
    return codepoints


def copy_glyph(target_font, donor_font, codepoint):
    target_cmap = target_font.getBestCmap()
    donor_cmap = donor_font.getBestCmap()

    if codepoint not in target_cmap:
        raise KeyError(f"Target font is missing U+{codepoint:04X}")
    if codepoint not in donor_cmap:
        raise KeyError(f"Donor font is missing U+{codepoint:04X}")

    target_name = target_cmap[codepoint]
    donor_name = donor_cmap[codepoint]

    target_font["glyf"][target_name] = copy.deepcopy(donor_font["glyf"][donor_name])
    target_font["hmtx"][target_name] = donor_font["hmtx"][donor_name]

    if "vmtx" in target_font and "vmtx" in donor_font:
        if donor_name in donor_font["vmtx"].metrics:
            target_font["vmtx"].metrics[target_name] = donor_font["vmtx"].metrics[donor_name]

    return target_name, donor_name


def main():
    parser = argparse.ArgumentParser(
        description="Replace selected symbol glyphs in a target font with donor glyphs."
    )
    parser.add_argument("--target", required=True, type=Path, help="Target TTF font")
    parser.add_argument("--donor", required=True, type=Path, help="Donor TTF font")
    parser.add_argument("--output", required=True, type=Path, help="Output TTF font")
    parser.add_argument(
        "--codepoint",
        action="append",
        help="Hex codepoint such as U+2026. Repeat to override the default list.",
    )
    args = parser.parse_args()

    codepoints = parse_codepoints(args.codepoint)
    target_font = TTFont(args.target, recalcBBoxes=True, recalcTimestamp=False)
    donor_font = TTFont(args.donor, recalcBBoxes=True, recalcTimestamp=False)

    print(f"Target: {args.target}")
    print(f"Donor: {args.donor}")
    print(f"Output: {args.output}")

    for codepoint in codepoints:
        target_name, donor_name = copy_glyph(target_font, donor_font, codepoint)
        print(f"U+{codepoint:04X}: {target_name} <- {donor_name}")

    target_font.save(args.output)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
