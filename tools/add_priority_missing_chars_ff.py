# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import argparse
import sys

try:
    import fontforge
except ImportError:
    raise SystemExit(
        "Cannot import fontforge.\n"
        "Run this script with FontForge:\n"
        "  fontforge -lang=py -script add_priority_missing_chars_ff.py"
    )


DEFAULT_GENKI = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\GenKiMin2TW-R.otf")
DEFAULT_MERRI_ITALIC = Path(r"D:\OneDrive\project\UDminchoModified\referenceFont\Merriweather-Italic.ttf")
DEFAULT_TARGET = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix.ttf")
DEFAULT_OUTPUT = Path(r"D:\OneDrive\project\UDminchoModified\KlarMinTC-Regular-GenKiMerriMix-Extended.ttf")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy high-priority missing glyphs into merged KlarMin.")
    parser.add_argument("--genki", type=Path, default=DEFAULT_GENKI)
    parser.add_argument("--merri-italic", type=Path, default=DEFAULT_MERRI_ITALIC)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sfd-output", type=Path, default=None)
    parser.add_argument("--log-output", type=Path, default=None)
    parser.add_argument("--genki-codepoints-file", type=Path, required=True)
    parser.add_argument("--merri-codepoints-file", type=Path, required=True)
    return parser.parse_args()


def validate_paths(*paths: Path) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing file(s):\n" + "\n".join(missing))


def default_sidecar_path(font_path: Path, suffix: str) -> Path:
    return font_path.with_name(font_path.stem + suffix)


def load_codepoints(path: Path) -> list[int]:
    codepoints: list[int] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("u+"):
            line = line[2:]
        codepoints.append(int(line, 16))
    return sorted(set(codepoints))


def select_unicode(font, codepoint: int) -> None:
    font.selection.none()
    font.selection.select(("unicode",), codepoint)


def first_selected_glyph(font):
    for glyph in font.selection.byGlyphs:
        return glyph
    return None


def ensure_char(dst_font, codepoint: int):
    glyph_name = fontforge.nameFromUnicode(codepoint)
    if not glyph_name:
        glyph_name = f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:X}"
    return dst_font.createChar(codepoint, glyph_name)


def prepare_source_font(src_font) -> None:
    src_font.selection.none()
    src_font.selection.all()
    src_font.unlinkReferences()
    src_font.selection.none()


def copy_unicode_glyph(src_font, dst_font, codepoint: int) -> tuple[bool, str]:
    if src_font.findEncodingSlot(codepoint) == -1:
        return False, "source-missing"

    ensure_char(dst_font, codepoint)

    select_unicode(src_font, codepoint)
    src_glyph = first_selected_glyph(src_font)
    if src_glyph is None:
        return False, "source-selection-empty"

    src_font.copy()

    select_unicode(dst_font, codepoint)
    dst_font.paste()
    dst_glyph = first_selected_glyph(dst_font)
    if dst_glyph is None:
        return False, "paste-failed"

    try:
        dst_glyph.width = src_glyph.width
    except Exception:
        pass

    try:
        dst_glyph.vwidth = src_glyph.vwidth
    except Exception:
        pass

    return True, "ok"


def rename_output_font(font) -> None:
    for attr, suffix in (
        ("fontname", "-Extended"),
        ("familyname", " Extended"),
        ("fullname", " Extended"),
    ):
        try:
            setattr(font, attr, getattr(font, attr) + suffix)
        except Exception:
            pass


def run_pass(pass_label: str, source_label: str, source_font, target_font, codepoints: list[int], log_lines: list[str]) -> int:
    copied = 0
    log_lines.append(pass_label)
    for codepoint in codepoints:
        ok, status = copy_unicode_glyph(source_font, target_font, codepoint)
        display = chr(codepoint) if codepoint <= sys.maxunicode else ""
        log_lines.append(f"{source_label}\tU+{codepoint:04X}\t{display}\t{status}")
        if ok:
            copied += 1
    log_lines.append("")
    return copied


def main() -> None:
    args = parse_args()
    validate_paths(
        args.genki,
        args.merri_italic,
        args.target,
        args.genki_codepoints_file,
        args.merri_codepoints_file,
    )

    out_sfd = args.sfd_output or default_sidecar_path(args.output, ".sfd")
    out_log = args.log_output or default_sidecar_path(args.output, "-log.txt")

    genki_codepoints = load_codepoints(args.genki_codepoints_file)
    merri_codepoints = load_codepoints(args.merri_codepoints_file)

    print("Opening fonts...")
    genki = fontforge.open(str(args.genki))
    merri_italic = fontforge.open(str(args.merri_italic))
    target = fontforge.open(str(args.target))

    prepare_source_font(genki)
    prepare_source_font(merri_italic)
    rename_output_font(target)

    log_lines: list[str] = []
    genki_copied = run_pass(
        "=== PASS 1: GenKiMin2TW-R.otf -> high-priority missing chars ===",
        "GENKI",
        genki,
        target,
        genki_codepoints,
        log_lines,
    )
    merri_copied = run_pass(
        "=== PASS 2: Merriweather-Italic.ttf -> missing thin/spacing chars ===",
        "MERRIITALIC",
        merri_italic,
        target,
        merri_codepoints,
        log_lines,
    )

    print(f"Saving SFD backup -> {out_sfd}")
    target.save(str(out_sfd))

    print(f"Generating merged font -> {args.output}")
    target.generate(str(args.output), flags=("opentype", "dummy-dsig", "round"))

    summary = [
        "=== SUMMARY ===",
        f"GenKi copied: {genki_copied}/{len(genki_codepoints)}",
        f"Merri italic copied: {merri_copied}/{len(merri_codepoints)}",
        f"Output TTF: {args.output}",
        f"Output SFD: {out_sfd}",
    ]
    log_lines.extend(summary)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print("\n".join(summary))
    print(f"Log file -> {out_log}")

    genki.close()
    merri_italic.close()
    target.close()


if __name__ == "__main__":
    main()
