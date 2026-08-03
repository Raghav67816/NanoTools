import struct
from pathlib import Path

HEADER_FORMAT = "<4sHHIII"
ENTRY_FORMAT = "<32sII"

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
ENTRY_SIZE = struct.calcsize(ENTRY_FORMAT)


def discover_files(dir_path):
    if not dir_path:
        print("Directory path not provided.")
        return []

    files = []

    for file in Path(dir_path).iterdir():
        if file.is_file():
            files.append(file)

    return files


def pack_files(dir_path):

    files = discover_files(dir_path)

    if len(files) == 0 or files == None:
        print("No files found.")
        return

    count = len(files)

    table_offset = HEADER_SIZE
    table_size = ENTRY_SIZE * count
    data_offset = table_offset + table_size

    entries = []

    with open("assets.npack", "wb") as bin_out:

        bin_out.write(
            struct.pack(
                HEADER_FORMAT,
                b"NPAK",
                1,
                count,
                table_offset,
                data_offset,
                0,
            )
        )

        bin_out.write(b"\x00" * table_size)

        for file in files:

            r_offset = bin_out.tell() - data_offset

            data = file.read_bytes()

            bin_out.write(data)

            entries.append(
                (
                    file.name,
                    r_offset,
                    len(data),
                )
            )

        bin_out.seek(table_offset)

        for name, offset, size in entries:

            name_bytes = name.encode("utf-8")[:31]
            name_bytes += b"\x00"
            name_bytes = name_bytes.ljust(32, b"\x00")

            bin_out.write(
                struct.pack(
                    ENTRY_FORMAT,
                    name_bytes,
                    offset,
                    size,
                )
            )

    print(f"Packed {count} assets into assets.npack")


if __name__ == "__main__":
    pack_files("./test")
