import argparse
import struct
from pathlib import Path


MAGIC_CHECKSUM = 0xB1B0AFBA


def u16(data, offset):
    return struct.unpack(">H", data[offset:offset + 2])[0]


def i16(data, offset):
    return struct.unpack(">h", data[offset:offset + 2])[0]


def u32(data, offset):
    return struct.unpack(">I", data[offset:offset + 4])[0]


def write_u16(data, offset, value):
    data[offset:offset + 2] = struct.pack(">H", value)


def write_u32(data, offset, value):
    data[offset:offset + 4] = struct.pack(">I", value)


def read_table_directory(data):
    num_tables = u16(data, 4)
    tables = {}
    pos = 12
    for _ in range(num_tables):
        tag_bytes = data[pos:pos + 4]
        tag = tag_bytes.decode("ascii")
        checksum = u32(data, pos + 4)
        offset = u32(data, pos + 8)
        length = u32(data, pos + 12)
        tables[tag] = {
            "record_offset": pos,
            "checksum": checksum,
            "offset": offset,
            "length": length,
        }
        pos += 16
    return tables


def table_slice(data, table):
    start = table["offset"]
    end = start + table["length"]
    return data[start:end]


def checksum_bytes(data):
    padded = bytes(data)
    pad_len = (-len(padded)) % 4
    if pad_len:
        padded += b"\0" * pad_len
    total = 0
    for i in range(0, len(padded), 4):
        total = (total + u32(padded, i)) & 0xFFFFFFFF
    return total


def read_metrics(path):
    raw = bytearray(path.read_bytes())
    tables = read_table_directory(raw)
    os2 = tables["OS/2"]
    hhea = tables["hhea"]
    head = tables["head"]
    return {
        "usWinAscent": u16(raw, os2["offset"] + 74),
        "usWinDescent": u16(raw, os2["offset"] + 76),
        "sTypoAscender": i16(raw, os2["offset"] + 68),
        "sTypoDescender": i16(raw, os2["offset"] + 70),
        "sTypoLineGap": i16(raw, os2["offset"] + 72),
        "hheaAscent": i16(raw, hhea["offset"] + 4),
        "hheaDescent": i16(raw, hhea["offset"] + 6),
        "hheaLineGap": i16(raw, hhea["offset"] + 8),
        "headYMin": i16(raw, head["offset"] + 38),
        "headYMax": i16(raw, head["offset"] + 42),
        "fsSelection": u16(raw, os2["offset"] + 62),
    }


def recompute_checksums(data, tables):
    head = tables["head"]
    head_offset = head["offset"]
    write_u32(data, head_offset + 8, 0)

    for tag, table in tables.items():
        table_data = bytearray(table_slice(data, table))
        if tag == "head":
            write_u32(table_data, 8, 0)
        checksum = checksum_bytes(table_data)
        write_u32(data, table["record_offset"] + 4, checksum)

    total_checksum = checksum_bytes(data)
    adjustment = (MAGIC_CHECKSUM - total_checksum) & 0xFFFFFFFF
    write_u32(data, head_offset + 8, adjustment)

    final_total = checksum_bytes(data)
    return adjustment, final_total


def build_output_path(target_path):
    stem = target_path.stem + "-linespacingfix"
    return target_path.with_name(stem + target_path.suffix)


def patch_win_metrics(target_path, reference_path, output_path):
    target_raw = bytearray(target_path.read_bytes())
    target_tables = read_table_directory(target_raw)
    reference_metrics = read_metrics(reference_path)
    before_metrics = read_metrics(target_path)

    os2 = target_tables["OS/2"]
    write_u16(target_raw, os2["offset"] + 74, reference_metrics["usWinAscent"])
    write_u16(target_raw, os2["offset"] + 76, reference_metrics["usWinDescent"])

    adjustment, final_total = recompute_checksums(target_raw, target_tables)
    output_path.write_bytes(target_raw)

    after_metrics = read_metrics(output_path)
    return before_metrics, reference_metrics, after_metrics, adjustment, final_total


def main():
    parser = argparse.ArgumentParser(
        description="Copy Windows line metrics from a reference font into a target font."
    )
    parser.add_argument("--target", required=True, type=Path, help="Target TTF/OTF font file")
    parser.add_argument("--reference", required=True, type=Path, help="Reference font file")
    parser.add_argument("--output", type=Path, help="Output file path")
    args = parser.parse_args()

    output_path = args.output or build_output_path(args.target)
    before, reference, after, adjustment, final_total = patch_win_metrics(
        args.target, args.reference, output_path
    )

    print(f"Target: {args.target}")
    print(f"Reference: {args.reference}")
    print(f"Output: {output_path}")
    print(
        "Before win metrics: "
        f"{before['usWinAscent']}/{before['usWinDescent']}"
    )
    print(
        "Reference win metrics: "
        f"{reference['usWinAscent']}/{reference['usWinDescent']}"
    )
    print(
        "After win metrics: "
        f"{after['usWinAscent']}/{after['usWinDescent']}"
    )
    print(
        "Typo/hhea stayed at: "
        f"{after['sTypoAscender']}/{after['sTypoDescender']}/{after['sTypoLineGap']} "
        f"and {after['hheaAscent']}/{after['hheaDescent']}/{after['hheaLineGap']}"
    )
    print(
        "Global bbox remains: "
        f"yMin={after['headYMin']} yMax={after['headYMax']}"
    )
    print(f"head.checkSumAdjustment=0x{adjustment:08X}")
    print(f"Whole font checksum=0x{final_total:08X}")
    if final_total != MAGIC_CHECKSUM:
        raise SystemExit("Checksum verification failed.")


if __name__ == "__main__":
    main()
