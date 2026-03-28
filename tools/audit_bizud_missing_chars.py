import sys
from pathlib import Path
from fontTools.ttLib import TTFont

try:
    import pandas as pd
except ImportError:
    raise SystemExit("Please install pandas and openpyxl: pip install pandas openpyxl")

def main():
    biz_font_path = Path(r"d:\OneDrive\project\UDminchoModified\referenceFont\BIZUDPMincho-Regular.ttf")
    jf_excel_path = Path(r"d:\OneDrive\project\UDminchoModified\jf 7000 當務字集 v0.9.xlsx")
    out_path = Path(r"d:\OneDrive\project\UDminchoModified\reports\biz_ud_missing_chars.txt")

    print("Loading JF 7000 Excel...")
    try:
        df = pd.read_excel(jf_excel_path, header=0)
        # Using the first column which usually contains the characters, or '字元' column.
        # Let's inspect column names first.
        char_col = None
        for col in df.columns:
            if '字' in str(col):
                char_col = col
                break
        if not char_col:
            char_col = df.columns[0]
            
        jf_chars = set(df[char_col].dropna().astype(str).str.strip())
        jf_codepoints = {ord(c) for char_str in jf_chars for c in char_str if len(c) == 1}
        print(f"Extracted {len(jf_codepoints)} unique codepoints from JF 7000.")
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    print("Loading BIZ UDPMincho cmap...")
    font = TTFont(str(biz_font_path))
    cmap = font.getBestCmap()

    missing = []
    for cp in sorted(jf_codepoints):
        if cp not in cmap:
            missing.append(cp)

    print(f"Found {len(missing)} missing characters from JF 7000.")
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"BIZ UDPMincho-Regular missing characters based on JF 7000:\n")
        f.write("----------------------------------------------------------\n")
        for cp in missing:
            f.write(f"U+{cp:04X} {chr(cp)}\n")

    print(f"Report saved to {out_path}")

if __name__ == "__main__":
    main()
