import sys
from fontTools.ttLib import TTFont

fonts = [
    r'd:\OneDrive\project\UDminchoModified\referenceFont\BIZUDPMincho-Regular.ttf',
    r'd:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-PunctFix-v9-symbolfix.ttf',
    r'C:\Users\Administrator\Downloads\Lato,Source_Serif_4,TASA_Explorer,TASA_Orbiter\Source_Serif_4\static\SourceSerif4_18pt-Regular.ttf'
]

with open(r'd:\OneDrive\project\UDminchoModified\reports\metrics.txt', 'w', encoding='utf-8') as out:
    for f in fonts:
        out.write(f"--- {f} ---\n")
        try:
            tt = TTFont(f)
            upm = tt['head'].unitsPerEm
            os2 = tt['OS/2']
            hhea = tt['hhea']
            out.write(f"UPM: {upm}\n")
            out.write(f"OS/2 TypoA/D/L: {os2.sTypoAscender} / {os2.sTypoDescender} / {os2.sTypoLineGap}\n")
            out.write(f"OS/2 WinA/D: {os2.usWinAscent} / {os2.usWinDescent}\n")
            out.write(f"hhea A/D/L: {hhea.ascent} / {hhea.descent} / {hhea.lineGap}\n")
            out.write(f"OS/2 xHeight: {getattr(os2, 'sxHeight', 'N/A')}, CapHeight: {getattr(os2, 'sCapHeight', 'N/A')}\n")
            tt.close()
        except Exception as e:
            out.write(f"Error: {e}\n")
