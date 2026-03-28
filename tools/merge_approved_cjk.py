from __future__ import annotations
import sys
import json
import os
from pathlib import Path

try:
    import fontforge
except ImportError:
    print("This script must be run in an environment that has the `fontforge` python module.")
    sys.exit(1)

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("This script requires `fonttools`.")
    sys.exit(1)

def scale_glyphs(ttf_path: str, codepoints: list[int], scale: float):
    print(f"Applying FontTools post-scale x{scale:.4f} to the generated TTF...")
    font = TTFont(ttf_path)
    cmap = font.getBestCmap()
    glyf_table = font["glyf"]
    hmtx_table = font["hmtx"].metrics
    vmtx_table = font["vmtx"].metrics if "vmtx" in font else None

    scaled = 0
    skipped = 0
    processed_names = set()

    for codepoint in codepoints:
        glyph_name = cmap.get(codepoint)
        if not glyph_name or glyph_name in processed_names:
            continue

        glyph = glyf_table[glyph_name]

        # Scale coordinates
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

        # Scale width metrics
        advance_width, left_side_bearing = hmtx_table[glyph_name]
        hmtx_table[glyph_name] = (
            int(round(advance_width * scale)),
            int(round(left_side_bearing * scale)),
        )

        # Scale vertical metrics
        if vmtx_table and glyph_name in vmtx_table:
            advance_height, top_side_bearing = vmtx_table[glyph_name]
            vmtx_table[glyph_name] = (
                int(round(advance_height * scale)),
                int(round(top_side_bearing * scale)),
            )

        scaled += 1
        processed_names.add(glyph_name)

    font.save(ttf_path)
    print(f"Scaled: {scaled}, Skipped: {skipped}")

def get_first_selected_glyph(font):
    for glyph in font.selection.byGlyphs:
        return glyph
    return None

def copy_glyph(src_font, dst_font, codepoint):
    if src_font.findEncodingSlot(codepoint) == -1:
        return False
        
    glyph_name = fontforge.nameFromUnicode(codepoint)
    if not glyph_name:
        glyph_name = f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:X}"
        
    dst_font.createChar(codepoint, glyph_name)
    
    src_font.selection.none()
    src_font.selection.select(("unicode",), codepoint)
    src_glyph = get_first_selected_glyph(src_font)
    if not src_glyph: return False
    
    src_font.copy()
    
    dst_font.selection.none()
    dst_font.selection.select(("unicode",), codepoint)
    dst_font.paste()
    
    dst_glyph = get_first_selected_glyph(dst_font)
    if dst_glyph:
        dst_glyph.width = src_glyph.width
        try:
            dst_glyph.vwidth = src_glyph.vwidth
        except:
            pass
            
    return True

def main():
    json_path = "reports/review_decisions.json"
    if not os.path.exists(json_path):
        # We also check the current dir or fallback location if the user downloaded it to their downloads folder
        # But for this script, we expect it in reports.
        # User might have saved it in downloads, let's allow an argument.
        if len(sys.argv) > 1:
            json_path = sys.argv[1]
        else:
            print(f"Usage: python {sys.argv[0]} [path_to_review_decisions.json]")
            print(f"Defaulting to {json_path}")
            
    if not os.path.exists(json_path):
        print(f"Cannot find {json_path}. Please export from the HTML tool first.")
        sys.exit(1)
        
    with open(json_path, "r", encoding="utf-8") as f:
        decisions = json.load(f)
        
    copy_list = []
    for hex_key, action in decisions.items():
        if action == "copy":
            hex_str = hex_key.replace("U+", "")
            copy_list.append(int(hex_str, 16))
            
    if not copy_list:
        print("No characters marked as 'copy' in the JSON.")
        sys.exit(0)
        
    print(f"Found {len(copy_list)} characters to merge.")
    
    klar_path = "KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf"
    biz_path = "BIZUDPMincho-SourceSerifMix-Regular.ttf"
    out_path = "BIZUDPMincho-ReviewMerged-Regular.ttf"
    out_sfd = "BIZUDPMincho-ReviewMerged-Regular.sfd"
    
    print(f"Opening {klar_path}...")
    klar = fontforge.open(klar_path)
    print(f"Opening {biz_path}...")
    biz = fontforge.open(biz_path)
    
    # Optional unlinking references to prevent dependency hell
    klar.selection.all()
    klar.unlinkReferences()
    klar.selection.none()
    
    copied = 0
    for cp in copy_list:
        if copy_glyph(klar, biz, cp):
            copied += 1
            
    print(f"Successfully copied {copied} glyphs in FontForge.")
    
    print(f"Generating updated font to {out_path}...")
    biz.generate(out_path, flags=("opentype", "dummy-dsig", "round"))
    
    # Backup
    print(f"Saving SFD backup to {out_sfd}...")
    biz.save(out_sfd)
    
    # Compute scale factor
    scale = float(biz.em) / float(klar.em) if klar.em and biz.em else 1.0
    print(f"Scaling copied glyphs by factor {scale:.4f} (Upem {biz.em} / {klar.em})...")
    
    klar.close()
    biz.close()
    
    if scale != 1.0:
        scale_glyphs(out_path, copy_list, scale)
    else:
        print("No scaling needed.")
        
    print("Merge script completed successfully.")

if __name__ == "__main__":
    main()
