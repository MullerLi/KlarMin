import sys
from pathlib import Path
from fontTools.ttLib import TTFont
import unicodedata as ud

def block_name(codepoint: int) -> str:
    # Basic unicode block estimation based on codepoint ranges
    if 0x4E00 <= codepoint <= 0x9FFF: return "CJK Unified Ideographs"
    if 0x3400 <= codepoint <= 0x4DBF: return "CJK Unified Ideographs Ext A"
    if 0x20000 <= codepoint <= 0x2A6DF: return "CJK Unified Ideographs Ext B"
    if 0x2A700 <= codepoint <= 0x2B73F: return "CJK Unified Ideographs Ext C"
    if 0x2B740 <= codepoint <= 0x2B81F: return "CJK Unified Ideographs Ext D"
    if 0x2B820 <= codepoint <= 0x2CEAF: return "CJK Unified Ideographs Ext E"
    if 0x2CEB0 <= codepoint <= 0x2EBEF: return "CJK Unified Ideographs Ext F"
    if 0x30000 <= codepoint <= 0x3134F: return "CJK Unified Ideographs Ext G"
    if 0xF900 <= codepoint <= 0xFAFF: return "CJK Compatibility Ideographs"
    if 0x2F800 <= codepoint <= 0x2FA1F: return "CJK Compatibility Ideographs Supp"
    if 0x3000 <= codepoint <= 0x303F: return "CJK Symbols and Punctuation"
    if 0x3100 <= codepoint <= 0x312F: return "Bopomofo"
    if 0xFF00 <= codepoint <= 0xFFEF: return "Halfwidth and Fullwidth Forms"
    if 0xAC00 <= codepoint <= 0xD7AF: return "Hangul Syllables"
    if 0x0000 <= codepoint <= 0x007F: return "Basic Latin"
    return "Other"

def main():
    target_path = Path(r"d:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf")
    genki_path = Path(r"d:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf")
    out_path = Path(r"d:\OneDrive\project\UDminchoModified\reports\klarmin_vs_genki_diff.txt")

    print(f"Loading {target_path.name}...")
    target_cmap = TTFont(str(target_path)).getBestCmap()
    print(f"Loading {genki_path.name}...")
    genki_cmap = TTFont(str(genki_path)).getBestCmap()

    target_set = set(target_cmap.keys())
    genki_set = set(genki_cmap.keys())

    missing_in_target = sorted(genki_set - target_set)
    missing_in_genki = sorted(target_set - genki_set)

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("Comparison Report: KlarMinTC v9 vs GenKiMin2TW-R\n")
        f.write("=================================================\n\n")

        f.write(f"Total glyphs mapped in KlarMinTC v9: {len(target_set)}\n")
        f.write(f"Total glyphs mapped in GenKiMin2TW-R: {len(genki_set)}\n\n")

        f.write(f"Codepoints in GenKiMin but missing in KlarMin (Top 10): {len(missing_in_target)} total\n")
        # Let's count by block
        blocks = {}
        for cp in missing_in_target:
            bname = block_name(cp)
            blocks[bname] = blocks.get(bname, 0) + 1
        
        for k, v in sorted(blocks.items(), key=lambda x: -x[1]):
            f.write(f"  - {k}: {v}\n")
            
        f.write(f"\nCodepoints in KlarMin but missing in GenKiMin: {len(missing_in_genki)} total\n")
        f.write("Includes: (Showing up to 20)\n")
        for cp in missing_in_genki[:20]:
            f.write(f"  U+{cp:04X} {chr(cp) if not ud.category(chr(cp)).startswith('C') else ''} \n")
            
    print(f"Report saved to {out_path}")

if __name__ == "__main__":
    main()
