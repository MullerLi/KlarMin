# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import subprocess
import sys
import unicodedata as ud

from fontTools.ttLib import TTFont


DEFAULT_BASE_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix.ttf")
DEFAULT_GENKI = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf")
DEFAULT_MERRI_ITALIC = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Italic.ttf")
DEFAULT_BASE_OUTPUT = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-Extended.ttf")
DEFAULT_ITALIC_OUTPUT = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-ItalicAlt-v3.ttf")
DEFAULT_FONTFORGE = Path(r"C:\Program Files\FontForgeBuilds\bin\fontforge.exe")

BLOCKS = [
    ("Latin Extended-B", 0x0180, 0x024F),
    ("Spacing Modifier Letters", 0x02B0, 0x02FF),
    ("Combining Diacritical Marks", 0x0300, 0x036F),
    ("Latin Extended Additional", 0x1E00, 0x1EFF),
    ("General Punctuation", 0x2000, 0x206F),
    ("Superscripts and Subscripts", 0x2070, 0x209F),
    ("Combining Marks for Symbols", 0x20D0, 0x20FF),
    ("Arrows", 0x2190, 0x21FF),
    ("Math Operators", 0x2200, 0x22FF),
    ("Dingbats", 0x2700, 0x27BF),
    ("Misc Symbols and Arrows", 0x2B00, 0x2BFF),
    ("Hangul Compatibility Jamo", 0x3130, 0x318F),
    ("Bopomofo Extended", 0x31A0, 0x31BF),
    ("CJK Unified Ideographs Ext A", 0x3400, 0x4DBF),
    ("CJK Unified Ideographs", 0x4E00, 0x9FFF),
    ("Hangul Syllables", 0xAC00, 0xD7AF),
    ("CJK Compatibility Ideographs", 0xF900, 0xFAFF),
]

LOW_PRIORITY_BLOCKS = {
    "CJK Unified Ideographs",
    "CJK Unified Ideographs Ext A",
    "Hangul Syllables",
    "Hangul Compatibility Jamo",
    "CJK Compatibility Ideographs",
    "Other",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add high-priority missing chars and rebuild italic alternates.")
    parser.add_argument("--target", type=Path, default=DEFAULT_BASE_TARGET)
    parser.add_argument("--genki", type=Path, default=DEFAULT_GENKI)
    parser.add_argument("--merri-italic", type=Path, default=DEFAULT_MERRI_ITALIC)
    parser.add_argument("--base-output", type=Path, default=DEFAULT_BASE_OUTPUT)
    parser.add_argument("--italic-output", type=Path, default=DEFAULT_ITALIC_OUTPUT)
    parser.add_argument("--fontforge", type=Path, default=DEFAULT_FONTFORGE)
    return parser.parse_args()


def validate_paths(*paths: Path) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing file(s):\n" + "\n".join(missing))


def locate_fontforge(explicit: Path) -> Path:
    if explicit.exists():
        return explicit
    which = shutil.which("fontforge")
    if which:
        return Path(which)
    raise SystemExit("FontForge executable not found. Pass --fontforge or install FontForge.")


def block_name(codepoint: int) -> str:
    for name, start, end in BLOCKS:
        if start <= codepoint <= end:
            return name
    return "Other"


def is_printable(codepoint: int) -> bool:
    return not ud.category(chr(codepoint)).startswith("C")


def load_cmap(path: Path) -> dict[int, str]:
    return TTFont(str(path)).getBestCmap()


def collect_genki_candidates(target_cmap: dict[int, str], genki_cmap: dict[int, str]) -> list[int]:
    missing = []
    for codepoint in sorted(set(genki_cmap) - set(target_cmap)):
        if not is_printable(codepoint):
            continue
        if block_name(codepoint) in LOW_PRIORITY_BLOCKS:
            continue
        missing.append(codepoint)
    return missing


def collect_merri_italic_candidates(target_cmap: dict[int, str], merri_cmap: dict[int, str]) -> list[int]:
    return [
        codepoint
        for codepoint in sorted(set(merri_cmap) - set(target_cmap))
        if is_printable(codepoint)
    ]


def write_codepoints(path: Path, codepoints: list[int]) -> None:
    lines = [f"U+{codepoint:04X}" for codepoint in codepoints]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def run_command(args: list[str]) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    args = parse_args()
    validate_paths(args.target, args.genki, args.merri_italic)
    fontforge_path = locate_fontforge(args.fontforge)

    target_cmap = load_cmap(args.target)
    genki_cmap = load_cmap(args.genki)
    merri_italic_cmap = load_cmap(args.merri_italic)

    genki_codepoints = collect_genki_candidates(target_cmap, genki_cmap)
    merri_codepoints = collect_merri_italic_candidates(target_cmap, merri_italic_cmap)

    genki_list = args.base_output.with_name(args.base_output.stem + "-genki-candidates.txt")
    merri_list = args.base_output.with_name(args.base_output.stem + "-merri-candidates.txt")
    write_codepoints(genki_list, genki_codepoints)
    write_codepoints(merri_list, merri_codepoints)

    helper_script = Path(__file__).with_name("add_priority_missing_chars_ff.py")
    scaler_script = Path(__file__).with_name("postprocess_genki_scale.py")
    italic_script = Path(__file__).with_name("add_merriweather_italic_alts.py")

    run_command(
        [
            str(fontforge_path),
            "-lang=py",
            "-script",
            str(helper_script),
            "--target",
            str(args.target),
            "--genki",
            str(args.genki),
            "--merri-italic",
            str(args.merri_italic),
            "--output",
            str(args.base_output),
            "--genki-codepoints-file",
            str(genki_list),
            "--merri-codepoints-file",
            str(merri_list),
        ]
    )

    if genki_codepoints:
        run_command(
            [
                sys.executable,
                str(scaler_script),
                "--genki",
                str(args.genki),
                "--target",
                str(args.target),
                "--merged",
                str(args.base_output),
                "--codepoints-file",
                str(genki_list),
            ]
        )

    run_command(
        [
            sys.executable,
            str(italic_script),
            "--target",
            str(args.base_output),
            "--italic",
            str(args.merri_italic),
            "--output",
            str(args.italic_output),
        ]
    )

    print(f"GenKi candidates added: {len(genki_codepoints)}")
    print(f"Merri italic candidates added: {len(merri_codepoints)}")
    print(f"Base output: {args.base_output}")
    print(f"Italic output: {args.italic_output}")


if __name__ == "__main__":
    main()
