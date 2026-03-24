import os
from fontTools.ttLib import TTFont

font_path = "c:/Users/125B/UDminchoModified/KlarMin-Regular.ttf"
font = TTFont(font_path)
name_table = font['name']

with open("c:/Users/125B/UDminchoModified/names_utf8.txt", "w", encoding="utf-8") as f:
    for record in name_table.names:
        if record.nameID in (1, 2, 3, 4, 6, 16, 17):
            try:
                f.write(f"NameID: {record.nameID}, PlatformID: {record.platformID}, PlatEncID: {record.platEncID}, LangID: {record.langID}\n")
                f.write(f"Current String: {record.toUnicode()}\n")
                f.write("---\n")
            except Exception as e:
                f.write(f"Failed to read NameID {record.nameID}: {e}\n")
