import struct
import subprocess
from cmd import Cmd
from pathlib import Path
from os.path import getsize
from os import mkdir, getcwd
from os import getcwd, remove, mkdir
from esptool.cmds import detect_chip, attach_flash, read_flash, write_flash, reset_chip, detect_flash_size

HEADER_FORMAT = "<4sHHIII"
ENTRY_FORMAT = "<32sII"

HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
ENTRY_SIZE = struct.calcsize(ENTRY_FORMAT)

def parse_partition_binary(path: str):
    if not path:
        print("Partition file not specified.")
        return
    
    bin_format = '<2sBBII16sI'
    size = 32

    with open(path, "rb") as bin:
        data = bin.read()

        for i in range(0, len(data), 32):
            chunk = data[i:i+32]
            if len(chunk) < size:
                break

            magic, p_type, sub_type, offset, part_size, name, flags = struct.unpack(bin_format, chunk)
            name_str = name.decode("utf-8", errors="ignore").strip("\x00")

            if magic == b"\xff\xff" or not name_str:
                continue

            if magic == b"\xeb\xeb":
                print("[End of Table MD5 Checksum Signature]")
                continue

            print(
                f"{'Name':<12} | "
                f"{'Type':<6} | "
                f"{'Subtype':<8} | "
                f"{'Offset':<10} | "
                f"{'Size (KB)':>10}"
            )
            print("-" * 60)

            print(
                f"{name_str:<12} | "
                f"{p_type:<6} | "
                f"{sub_type:<8} | "
                f"{hex(offset):<10} | "
                f"{part_size / 1024:>10.2f}"
            )


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

    mkdir(f"{getcwd()}/dist")

    with open(f"{getcwd()}/dist/assets.npack", "wb") as bin_out:

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

class NanoShell(Cmd):
    prompt = "nano> "
    intro = "Upload, manage, delete NanoUI assets easily."

    def __init__(self):
        super(NanoShell, self).__init__()

        self.esp = None
        self.image_path = ""
        self.files_unpacked = []
        self.addr = ""

    def do_connect(self, arg):
        if not arg:
            print("Please specify port.")
            return
        
        try:
            self.esp = detect_chip(arg)
            attach_flash(self.esp)
            print(f"Connected: {self.esp.CHIP_NAME}")

        except Exception as error:
            print(f"Error occurred: {str(error)}")
            self.esp = None

    def do_list_parts(self, args):
        if not self.esp:
            print("Board not connect. Please connect to board first.")
            return
        
        file_name = f"{getcwd()}/partition.bin"
        data = read_flash(self.esp, address=0x8000, size=0x1000)
        
        with open(file_name, 'wb') as partition:
            partition.write(data)

        parse_partition_binary(file_name)
        remove(f'{getcwd()}/partition.bin')


    def do_set_flash_addr(self, arg):
        if not arg:
            print("Please specify address")
            return 

        self.addr = arg

    def do_upload_pack(self, arg):
        if not arg:
            print("Please specify source folder")
            return
        
        process = subprocess.Popen([
            f'{getcwd()}/bin/mklittlefs', 
            '-c', str(arg),
            '-b', '4096', 
            '-p', '256', 
            '-s', '1441792',
            f'{getcwd()}/image.bin'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break

            if output:
                print(output.strip())

        r_code = process.wait()
        print(f"Process finished with: {r_code}")

        if self.addr == None or self.addr == "":
            print("Address not set. Abort.")
            return

        target_filesize = getsize(f'{getcwd()}/image.bin') / (1024*1024)
        flash_size = detect_flash_size(self.esp)
        perm = str(input(f"{target_filesize:.2f} MB out of {flash_size} will be used. Do you wish to process [Y or n]: ")).lower()

        if perm == "" or perm == "y":
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break

                if output:
                    print(output.strip())
            print(f"Process finished with: {r_code}")

            if isinstance(self.addr, str):
                self.addr = int(self.addr, 16)

            with open(f'{getcwd()}/image.bin', "rb") as fs_image:
                write_flash(self.esp, [(self.addr, fs_image)])

            remove(f"{getcwd()}/image.bin")
            print("Writing finished...")

            reset_chip(self.esp)
            print("Rebooting chip.")

        else:
            print("Operation aborted by user.")
            return

    def do_pack(self, folder_path):
        if not folder_path:
            print("Please specify folder path.")
            return

        pack_files(folder_path)


    def do_unpack_image(self, image_path):
        self.image_path = image_path
        self.files_unpacked = unpack_image(image_path)

    def do_ls(self, arg):
        if self.image_path == "":
            print("Please unpack an image first.")
            return

        print("============== FILES ==============")

        for file in self.files_unpacked:
            print(f"Filename: {file['name']}")
            print(f"Size: {file['size'] / 1024:.2f} KB")

        print("============== END ==============")

    def do_exit(self, arg):
        print("Exiting...")
        return True
    
if __name__ == "__main__":
    try:
        NanoShell().cmdloop()

    except KeyboardInterrupt:
        print("Exiting...")
