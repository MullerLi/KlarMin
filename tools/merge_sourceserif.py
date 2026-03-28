# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import fontforge
except ImportError:
    raise SystemExit("Please run this script with a python that has fontforge installed.")

try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None


def parse_args():
    parser = argparse.ArgumentParser(description="Merge Source Serif 4 Latin into BIZ UDP Mincho")
    parser.add_argument("--source", type=Path, required=True, help="Source Serif 4 font file")
    parser.add_argument("--target", type=Path, required=True, help="BIZ UDP Mincho font file")
    parser.add_argument("--output", type=Path, required=True, help="Output font file")
    parser.add_argument("--scale", type=float, default=2.338806, help="Scale factor (1567 / 670)")
    return parser.parse_args()


# We only copy Latin, Greek, Cyrillic, and ASCII punctuation.
# We skip general punctuation (0x2000+) to avoid breaking CJK ellipsis, quotes, etc.
def is_target_codepoint(cp: int) -> bool:
    if 0x0020 <= cp <= 0x007E: return True
    if 0x00A0 <= cp <= 0x024F: return True
    if 0x0370 <= cp <= 0x03FF: return True  # Greek
    if 0x0400 <= cp <= 0x04FF: return True  # Cyrillic
    if 0x1E00 <= cp <= 0x1EFF: return True  # Latin Extended Additional
    return False


def copy_unicode_glyph(src_font, dst_font, codepoint: int) -> bool:
    if src_font.findEncodingSlot(codepoint) == -1:
        return False

    glyph_name = fontforge.nameFromUnicode(codepoint)
    if not glyph_name:
        glyph_name = f"uni{codepoint:04X}"
    dst_font.createChar(codepoint, glyph_name)

    src_font.selection.none()
    src_font.selection.select(("unicode",), codepoint)
    if not list(src_font.selection.byGlyphs):
        return False

    src_font.copy()

    dst_font.selection.none()
    dst_font.selection.select(("unicode",), codepoint)
    dst_font.paste()

    return True


def scale_generated_ttf(ttf_path: Path, codepoints: list[int], scale: float):
    font = TTFont(str(ttf_path))
    cmap = font.getBestCmap()
    glyf_table = font["glyf"]
    hmtx_table = font["hmtx"].metrics
    vmtx_table = font["vmtx"].metrics if "vmtx" in font else None
    
    scaled = 0
    processed = set()
    
    for cp in codepoints:
        name = cmap.get(cp)
        if not name or name in processed:
            continue
            
        glyph = glyf_table.get(name)
        if not glyph:
            continue
            
        if glyph.isComposite():
            for comp in glyph.components:
                comp.x = int(round(comp.x * scale))
                comp.y = int(round(comp.y * scale))
            glyph.recalcBounds(glyf_table)
        elif getattr(glyph, "numberOfContours", 0) > 0 and hasattr(glyph, "coordinates"):
            glyph.coordinates.scale((scale, scale))
            glyph.recalcBounds(glyf_table)
            
        adv, lsb = hmtx_table[name]
        hmtx_table[name] = (int(round(adv * scale)), int(round(lsb * scale)))
        
        if vmtx_table and name in vmtx_table:
            v_adv, tsb = vmtx_table[name]
            vmtx_table[name] = (int(round(v_adv * scale)), int(round(tsb * scale)))
            
        scaled += 1
        processed.add(name)
        
    font.save(str(ttf_path))
    return scaled


def main():
    args = parse_args()

    print(f"Opening target: {args.target}")
    target = fontforge.open(str(args.target))
    print(f"Opening source: {args.source}")
    source = fontforge.open(str(args.source))

    # Unlink references so we copy outlines cleanly
    source.selection.all()
    source.unlinkReferences()
    source.selection.none()

    codepoints_to_scale = []
    
    print("Collecting glyphs...")
    target_cps = []
    for glyph in source.glyphs():
        cp = glyph.unicode
        if cp >= 0 and is_target_codepoint(cp):
            target_cps.append(cp)

    print(f"Found {len(target_cps)} target codepoints. Copying glyphs...")
    count = 0
    for cp in target_cps:
        if copy_unicode_glyph(source, target, cp):
            codepoints_to_scale.append(cp)
            count += 1

    print(f"Copied {count} glyphs. Generating intermediate TTF...")
    
    # Generate directly to output
    target.generate(str(args.output), flags=("opentype", "dummy-dsig", "round"))
    target.close()
    source.close()

    if TTFont and args.scale != 1.0:
        print(f"Scaling copied glyphs by factor {args.scale:.4f}...")
        scaled_cnt = scale_generated_ttf(args.output, codepoints_to_scale, args.scale)
        print(f"Finished scaling {scaled_cnt} glyphs.")
    else:
        print("Scaling skipped.")

    print(f"Done! Output is at {args.output}")

if __name__ == "__main__":
    main()
