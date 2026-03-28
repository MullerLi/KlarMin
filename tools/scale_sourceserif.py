import argparse
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

def is_target_codepoint(cp: int) -> bool:
    if 0x0020 <= cp <= 0x007E: return True
    if 0x00A0 <= cp <= 0x024F: return True
    if 0x0370 <= cp <= 0x03FF: return True  # Greek
    if 0x0400 <= cp <= 0x04FF: return True  # Cyrillic
    if 0x1E00 <= cp <= 0x1EFF: return True  # Latin Extended Additional
    return False

def scale_generated_ttf(ttf_path: Path, codepoints: list[int], scale: float):
    print(f"Scaling '{ttf_path}' with factor {scale:.4f}...")
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
            
        # Scale coordinates
        if glyph.isComposite():
            for comp in glyph.components:
                comp.x = int(round(comp.x * scale))
                comp.y = int(round(comp.y * scale))
            glyph.recalcBounds(glyf_table)
        elif getattr(glyph, "numberOfContours", 0) > 0 and hasattr(glyph, "coordinates"):
            glyph.coordinates.scale((scale, scale))
            glyph.recalcBounds(glyf_table)
            
        # Scale advance width
        adv, lsb = hmtx_table[name]
        hmtx_table[name] = (int(round(adv * scale)), int(round(lsb * scale)))
        
        # Scale vertical metrics if any
        if vmtx_table and name in vmtx_table:
            v_adv, tsb = vmtx_table[name]
            vmtx_table[name] = (int(round(v_adv * scale)), int(round(tsb * scale)))
            
        scaled += 1
        processed.add(name)
        
    font.save(str(ttf_path))
    print(f"Successfully scaled {scaled} glyphs.")
    return scaled

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--font", type=Path, required=True, help="Target TTF file to scale inline")
    parser.add_argument("--scale", type=float, default=2.338806, help="Scale factor (1567 / 670)")
    args = parser.parse_args()
    
    # We collect the codepoints identically to is_target_codepoint 
    # (Actually we want to scale exactly what was copied, but just scanning targets is safe since only they were copied/exist with those mappings)
    # Wait, if we scan through our target list, we might accidentally scale existing BIZ UDPMincho characters if Source Serif 4 didn't have them?
    # Source Serif 4 definitely has Basic Latin and Latin-1. Latin Ext A/B are also very well covered. 
    # Just to be extremely precise, it's safer to only scale if we know it was copied, but running this on the already merged font means
    # those codepoints were overridden by Source Serif. So scaling them all is correct!
    
    target_cps = []
    # Let's read the cmap to find matching target codepoints that actually exist
    tt = TTFont(str(args.font))
    cmap = tt.getBestCmap()
    for cp in cmap:
        if is_target_codepoint(cp):
            target_cps.append(cp)
    tt.close()
    
    scale_generated_ttf(args.font, target_cps, args.scale)

if __name__ == "__main__":
    main()
