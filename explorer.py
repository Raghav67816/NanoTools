import struct

HEADER_FORMAT = "<4sHHIII"
ENTRY_FORMAT = "<32sII"

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
ENTRY_SIZE = struct.calcsize(ENTRY_FORMAT)

def unpack_image(path):
    if not path:
        print("Image path not specified.")
        return

    out_data = []

    bin_data = open(path, "rb")
    data = bin_data.read()

    header = data[:HEADER_SIZE]
    magic, version, count, table_offset, data_offset, flags = struct.unpack(HEADER_FORMAT, header)

    for i in range(count):
        start = table_offset + (ENTRY_SIZE * i)
        end = start + ENTRY_SIZE

        entry_data = data[start:end]
        name, offset, size = struct.unpack(ENTRY_FORMAT, entry_data)

        name = name.rstrip(b"\x00").decode("utf-8")

        entry = {
            "name": name,
            "size": size
        }

        out_data.append(entry)

    return out_data
