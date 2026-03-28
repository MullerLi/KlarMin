import sys
import json
import os
from fontTools.ttLib import TTFont

def get_cmap(font_path):
    print(f"Loading {font_path}...")
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    return cmap if cmap else {}

def is_cjk_han(codepoint):
    """
    Check if a codepoint is within the CJK Unified Ideographs or Extension blocks.
    Basic: 4E00-9FFF
    Ext A: 3400-4DBF
    Ext B to F: 20000-2EBEF
    """
    if 0x4E00 <= codepoint <= 0x9FFF:
        return True
    if 0x3400 <= codepoint <= 0x4DBF:
        return True
    if 0x20000 <= codepoint <= 0x2EBEF:
        return True
    # Include some common punctuation and symbols too just in case they were missing
    if 0x3000 <= codepoint <= 0x303F:  # CJK Symbols and Punctuation
        return True
    if 0xFF00 <= codepoint <= 0xFFEF:  # Halfwidth and Fullwidth Forms
        return True
    return False


def classify_block(codepoint):
    ranges = [
        ((0x3000, 0x303F), "CJK Symbols and Punctuation"),
        ((0x3400, 0x4DBF), "CJK Unified Ideographs Extension A"),
        ((0x4E00, 0x9FFF), "CJK Unified Ideographs"),
        ((0xF900, 0xFAFF), "CJK Compatibility Ideographs"),
        ((0x20000, 0x2A6DF), "CJK Unified Ideographs Extension B"),
        ((0x2A700, 0x2B73F), "CJK Unified Ideographs Extension C"),
        ((0x2B740, 0x2B81F), "CJK Unified Ideographs Extension D"),
        ((0x2B820, 0x2CEAF), "CJK Unified Ideographs Extension E/F"),
        ((0x2CEB0, 0x2EBEF), "CJK Unified Ideographs Extension G/I"),
        ((0xFF00, 0xFFEF), "Halfwidth and Fullwidth Forms"),
    ]
    for (start, end), label in ranges:
        if start <= codepoint <= end:
            return label
    return "Other"


def unicode_plane(codepoint):
    if codepoint <= 0xFFFF:
        return "BMP"
    if codepoint <= 0x1FFFF:
        return "SMP"
    if codepoint <= 0x2FFFF:
        return "SIP"
    return "TIP+"

def main():
    biz_path = "BIZUDPMincho-SourceSerifMix-Regular.ttf"
    klar_path = "KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf"
    genyo_path = os.path.join("referenceFont", "GenYoMin2TW-R.ttf")
    out_json = os.path.join("reports", "missing_chars.json")
    out_js = os.path.join("reports", "missing_chars_data.js")

    if not os.path.exists(biz_path) or not os.path.exists(klar_path):
        print("Error: Required font files not found in the root directory.")
        sys.exit(1)

    biz_cmap = get_cmap(biz_path)
    klar_cmap = get_cmap(klar_path)
    genyo_cmap = get_cmap(genyo_path) if os.path.exists(genyo_path) else {}

    biz_keys = set(biz_cmap.keys())
    klar_keys = set(klar_cmap.keys())

    missing = klar_keys - biz_keys

    results = []
    
    for c in sorted(list(missing)):
        if is_cjk_han(c):
            results.append({
                "codepoint": c,
                "hex": f"U+{c:04X}",
                "char": chr(c),
                "klarmin_name": klar_cmap[c],
                "in_genyo": c in genyo_cmap,
                "genyo_name": genyo_cmap.get(c),
                "plane": unicode_plane(c),
                "block": classify_block(c),
            })

    print(f"Total KlarMin characters: {len(klar_keys)}")
    print(f"Total BIZ characters: {len(biz_keys)}")
    print(f"Missing characters: {len(missing)}")
    print(f"Filtered CJK missing characters to export: {len(results)}")

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(out_js, 'w', encoding='utf-8') as f:
        f.write("window.MISSING_CHARS = ")
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write(";")

    print(f"Successfully wrote {len(results)} characters to {out_json} and {out_js}")

if __name__ == "__main__":
    main()
