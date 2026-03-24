import os
from fontTools.ttLib import TTFont

def update_font_metadata(font_path, new_name):
    font = TTFont(font_path)
    name_table = font['name']
    
    # Define the new names
    family_name = new_name
    full_name = f"{new_name} Regular"
    ps_name = f"{new_name}-Regular"
    unique_id = f"{new_name}-Regular;2026"
    
    for record in name_table.names:
        # NameID 1: Font Family Name
        if record.nameID == 1:
            record.string = family_name.encode(record.getEncoding())
        # NameID 3: Unique Font Identifier
        elif record.nameID == 3:
            record.string = unique_id.encode(record.getEncoding())
        # NameID 4: Full Font Name
        elif record.nameID == 4:
            record.string = full_name.encode(record.getEncoding())
        # NameID 6: PostScript Name
        elif record.nameID == 6:
            record.string = ps_name.encode(record.getEncoding())
        # NameID 16: Typographic Family Name
        elif record.nameID == 16:
            record.string = family_name.encode(record.getEncoding())
            
    font.save(font_path)
    print(f"Updated metadata for {font_path} to {new_name}")

if __name__ == "__main__":
    font_file = "c:/Users/125B/UDminchoModified/KlarMin-Regular.ttf"
    if os.path.exists(font_file):
        update_font_metadata(font_file, "KlarMin")
    else:
        print(f"File {font_file} not found.")
