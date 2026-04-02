import sys
import json
import os
import re
from pathlib import Path
from fontTools.ttLib import TTFont

def get_cmap(font_path):
    print(f"Loading {font_path}...")
    font = TTFont(str(font_path))
    cmap = font.getBestCmap()
    return cmap if cmap else {}

def is_target_char(codepoint):
    """Check if the codepoint is in a block we want to review.
    Covers: CJK Ideographs, CJK Symbols/Punctuation, Bopomofo,
    Bopomofo Extended, Fullwidth Forms, CJK Compatibility,
    and other ranges relevant to Traditional Chinese typography
    (matching 芫荽 / Iansui coverage scope)."""
    ranges = [
        (0x3000, 0x303F),   # CJK Symbols and Punctuation
        (0x3100, 0x312F),   # Bopomofo
        (0x31A0, 0x31BF),   # Bopomofo Extended
        (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
        (0x4E00, 0x9FFF),   # CJK Unified Ideographs
        (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
        (0xFE30, 0xFE4F),   # CJK Compatibility Forms
        (0xFF00, 0xFFEF),   # Halfwidth and Fullwidth Forms
        (0x20000, 0x2A6DF), # CJK Extension B
        (0x2A700, 0x2B73F), # CJK Extension C
        (0x2B740, 0x2B81F), # CJK Extension D
        (0x2B820, 0x2CEAF), # CJK Extension E/F
        (0x2CEB0, 0x2EBEF), # CJK Extension G/I
        # Symbols & phonetics used by 芫荽 scope
        (0x00C0, 0x024F),   # Latin Extended-A/B (Vietnamese, pinyin)
        (0x0250, 0x02AF),   # IPA Extensions (KK/DJ phonetics)
        (0x02B0, 0x02FF),   # Spacing Modifier Letters
        (0x0300, 0x036F),   # Combining Diacritical Marks
        (0x1E00, 0x1EFF),   # Latin Extended Additional
        (0x2010, 0x2027),   # General Punctuation subset
        (0x2030, 0x205E),   # General Punctuation subset
        (0x2150, 0x218F),   # Number Forms
        (0x2190, 0x21FF),   # Arrows
        (0x2200, 0x22FF),   # Mathematical Operators
        (0x2460, 0x24FF),   # Enclosed Alphanumerics (circled numbers)
        (0x2500, 0x257F),   # Box Drawing
        (0x2580, 0x259F),   # Block Elements
        (0x25A0, 0x25FF),   # Geometric Shapes
        (0x2600, 0x26FF),   # Miscellaneous Symbols
        (0x3200, 0x32FF),   # Enclosed CJK Letters
        (0x3300, 0x33FF),   # CJK Compatibility
    ]
    for lo, hi in ranges:
        if lo <= codepoint <= hi:
            return True
    return False

def classify_block(codepoint):
    ranges = [
        ((0x00C0, 0x024F), "Latin Extended"),
        ((0x0250, 0x02AF), "IPA Extensions"),
        ((0x02B0, 0x02FF), "Spacing Modifier Letters"),
        ((0x0300, 0x036F), "Combining Diacritical Marks"),
        ((0x1E00, 0x1EFF), "Latin Extended Additional"),
        ((0x2010, 0x205E), "General Punctuation"),
        ((0x2150, 0x218F), "Number Forms"),
        ((0x2190, 0x21FF), "Arrows"),
        ((0x2200, 0x22FF), "Mathematical Operators"),
        ((0x2460, 0x24FF), "Enclosed Alphanumerics"),
        ((0x2500, 0x257F), "Box Drawing"),
        ((0x2580, 0x259F), "Block Elements"),
        ((0x25A0, 0x25FF), "Geometric Shapes"),
        ((0x2600, 0x26FF), "Miscellaneous Symbols"),
        ((0x3000, 0x303F), "CJK Symbols and Punctuation"),
        ((0x3100, 0x312F), "Bopomofo"),
        ((0x31A0, 0x31BF), "Bopomofo Extended"),
        ((0x3200, 0x32FF), "Enclosed CJK Letters"),
        ((0x3300, 0x33FF), "CJK Compatibility"),
        ((0x3400, 0x4DBF), "CJK Unified Ideographs Extension A"),
        ((0x4E00, 0x9FFF), "CJK Unified Ideographs"),
        ((0xF900, 0xFAFF), "CJK Compatibility Ideographs"),
        ((0xFE30, 0xFE4F), "CJK Compatibility Forms"),
        ((0xFF00, 0xFFEF), "Halfwidth and Fullwidth Forms"),
        ((0x20000, 0x2A6DF), "CJK Unified Ideographs Extension B"),
        ((0x2A700, 0x2B73F), "CJK Unified Ideographs Extension C"),
        ((0x2B740, 0x2B81F), "CJK Unified Ideographs Extension D"),
        ((0x2B820, 0x2CEAF), "CJK Unified Ideographs Extension E/F"),
        ((0x2CEB0, 0x2EBEF), "CJK Unified Ideographs Extension G/I"),
    ]
    for (start, end), label in ranges:
        if start <= codepoint <= end:
            return label
    return "Other"

def unicode_plane(codepoint):
    if codepoint <= 0xFFFF: return "BMP"
    if codepoint <= 0x1FFFF: return "SMP"
    if codepoint <= 0x2FFFF: return "SIP"
    return "TIP+"

def parse_rtf_unicode(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    matches = re.finditer(r'\\u(-?\d+)', content)
    code_units = []
    for match in matches:
        val = int(match.group(1))
        if val < 0:
            val += 65536
        code_units.append(val)
    
    codepoints = set()
    i = 0
    while i < len(code_units):
        cu = code_units[i]
        if 0xD800 <= cu <= 0xDBFF and i + 1 < len(code_units):
            next_cu = code_units[i+1]
            if 0xDC00 <= next_cu <= 0xDFFF:
                cp = 0x10000 + ((cu - 0xD800) << 10) + (next_cu - 0xDC00)
                codepoints.add(cp)
                i += 2
                continue
        codepoints.add(cu)
        i += 1
    return codepoints

def main():
    root_dir = Path(__file__).parent.parent
    rtf_dir = root_dir / "essentialFontTW"
    biz_path = root_dir / "BIZUDPMincho-SourceSerifMix-Regular.ttf"
    klar_path = root_dir / "KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf"
    genyo_path = root_dir / "referenceFont" / "GenYoMin2TW-R.ttf"
    
    out_json = root_dir / "reports" / "missing_chars.json"
    out_js = root_dir / "reports" / "missing_chars_data.js"

    # Collect ALL RTF files (01-06)
    rtf_files = sorted(rtf_dir.glob("*.rtf"))
    if not rtf_files:
        print("Error: No RTF files found in essentialFontTW/")
        sys.exit(1)
        
    print(f"Found RTF files: {[f.name for f in rtf_files]}")
    
    rtf_chars = set()
    for rtf_file in rtf_files:
        cps = parse_rtf_unicode(rtf_file)
        rtf_chars.update(cps)
        
    print(f"Extracted {len(rtf_chars)} total unique Unicode codepoints from RTFs.")

    biz_cmap = get_cmap(biz_path)
    klar_cmap = get_cmap(klar_path)
    genyo_cmap = get_cmap(genyo_path) if genyo_path.exists() else {}

    biz_keys = set(biz_cmap.keys())
    klar_keys = set(klar_cmap.keys())

    # We want characters in RTFs that ARE in KlarMin (so we have something to copy)
    # AND are CJK Han.
    candidates = rtf_chars & klar_keys
    
    results = []
    
    for c in sorted(list(candidates)):
        if is_target_char(c):
            results.append({
                "codepoint": c,
                "hex": f"U+{c:04X}",
                "char": chr(c),
                "klarmin_name": klar_cmap[c],
                "in_genyo": c in genyo_cmap,
                "genyo_name": genyo_cmap.get(c),
                "in_biz": c in biz_keys,
                "biz_name": biz_cmap.get(c),
                "plane": unicode_plane(c),
                "block": classify_block(c),
            })

    print(f"Total KlarMin characters: {len(klar_keys)}")
    print(f"Total BIZ characters: {len(biz_keys)}")
    print(f"Total RTF+KlarMin CJK Candidates to review: {len(results)}")
    
    missing_in_biz = sum(1 for r in results if not r['in_biz'])
    exist_in_biz = len(results) - missing_in_biz
    print(f"  - Missing in BIZ (Add): {missing_in_biz}")
    print(f"  - Exist in BIZ (Replace): {exist_in_biz}")

    out_json.parent.mkdir(parents=True, exist_ok=True)

    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(out_js, 'w', encoding='utf-8') as f:
        f.write("window.MISSING_CHARS = ")
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write(";")

    print(f"Successfully wrote {len(results)} characters to {out_json} and {out_js}")

if __name__ == "__main__":
    main()
