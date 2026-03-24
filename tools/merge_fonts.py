import os
import subprocess
from fontTools.ttLib import TTFont

def update_font_name(font_path, new_family_name, new_ps_name):
    font = TTFont(font_path)
    name_table = font['name']
    
    for record in name_table.names:
        if record.nameID in (1, 3, 4, 6, 16):
            old_str = record.toUnicode()
            
            if record.nameID == 6:
                new_str = old_str.replace("Merriweather", new_ps_name).replace("TRWUDMincho", new_ps_name).replace("-Regular", "") + "-Regular"
            else:
                new_str = old_str.replace("Merriweather", new_family_name).replace("TRWUDMincho", new_family_name)
                
            record.string = new_str.encode(record.getEncoding())
            
    font.save(font_path)
    print(f"Updated names for {font_path}")


def main():
    base_dir = "c:/Users/125B/UDminchoModified"
    merriweather_path = os.path.join(base_dir, "Merriweather-Regular.ttf")
    mincho_path = os.path.join(base_dir, "TRWUDMincho-R.ttf")
    
    merriweather_subset_path = os.path.join(base_dir, "Merriweather-Subset.ttf")
    mincho_subset_path = os.path.join(base_dir, "TRWUDMincho-Subset.ttf")
    merged_path = os.path.join(base_dir, "MerriMincho-Regular.ttf")
    
    western_unicodes = "U+0020-007E,U+00A0-00FF,U+0100-017F,U+0180-024F,U+2000-203F"
    
    print("Subsetting Merriweather...")
    subprocess.run([
        "pyftsubset",
        merriweather_path,
        f"--unicodes={western_unicodes}",
        f"--output-file={merriweather_subset_path}",
        "--name-IDs=*",
        "--name-legacy",
        "--name-languages=*",
        "--layout-features=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs"
    ], check=True)
    
    print("Subsetting TRWUDMincho-R...")
    subprocess.run([
        "pyftsubset",
        mincho_path,
        f"--unicodes=*",
        f"--exclude-unicodes={western_unicodes}",
        f"--output-file={mincho_subset_path}",
        "--name-IDs=*",
        "--name-legacy",
        "--name-languages=*",
        "--layout-features=*",
        "--glyph-names",
        "--symbol-cmap",
        "--legacy-cmap",
        "--notdef-glyph",
        "--notdef-outline",
        "--recommended-glyphs"
    ], check=True)
    
    print("Merging fonts...")
    subprocess.run([
        "pyftmerge",
        merriweather_subset_path,
        mincho_subset_path,
        f"--output-file={merged_path}"
    ], check=True)
    
    print("Updating metadata...")
    update_font_name(merged_path, "MerriMincho", "MerriMincho")
    
    print("Done! Generated:", merged_path)
    
    if os.path.exists(merriweather_subset_path):
        os.remove(merriweather_subset_path)
    if os.path.exists(mincho_subset_path):
        os.remove(mincho_subset_path)

if __name__ == "__main__":
    main()
