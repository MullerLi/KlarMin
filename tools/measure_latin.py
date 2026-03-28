from fontTools.ttLib import TTFont

def dump_bbox(font_path, characters, out_file):
    out_file.write(f"--- {font_path.split('\\\\')[-1]} ---\n")
    tt = TTFont(font_path)
    cmap = tt.getBestCmap()
    glyf = tt["glyf"]
    
    for char in characters:
        cp = ord(char)
        name = cmap.get(cp)
        if name and name in glyf:
            g = glyf[name]
            out_file.write(f"Char '{char}' (U+{cp:04X}): xMin={getattr(g,'xMin',0)}, xMax={getattr(g,'xMax',0)}, yMin={getattr(g,'yMin',0)}, yMax={getattr(g,'yMax',0)} | Width={getattr(g,'xMax',0)-getattr(g,'xMin',0)}, Height={getattr(g,'yMax',0)-getattr(g,'yMin',0)}\n")
        else:
            out_file.write(f"Char '{char}' not found.\n")

def main():
    fonts = [
        r"d:\OneDrive\project\UDminchoModified\BIZUDPMincho-SourceSerifMix-Regular.ttf"
    ]
    chars_to_test = ['H', 'x', 'A', '国', '中', 'g']
    
    with open(r"d:\OneDrive\project\UDminchoModified\reports\measure_latin.txt", "w", encoding="utf-8") as f:
        for font in fonts:
            dump_bbox(font, chars_to_test, f)

if __name__ == "__main__":
    main()
