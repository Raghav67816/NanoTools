from cmd import Cmd
from os import getcwd
from struct import unpack
from esptool.cmds import detect_chip, attach_flash, read_flash

def parse_partition_binary(path: str):
    if not path:
        print("Partition file not specified.")
        return
    
    bin_format = '<2s B B I I 16s I'
    size = 32

    with open(path, "rb") as bin:
        data = bin.read()

        for i in range(0, len(data), 32):
            chunk = data[i:i+32]
            if len(chunk) < size:
                break

            magic, p_type, sub_type, offset, part_size, name, flags = unpack(bin_format, chunk)
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

class NanoShell(Cmd):
    prompt = "nano> "
    intro = "Upload, manage, delete NanoUI assets easily."

    def __init__(self):
        super(NanoShell, self).__init__()

        self.esp = None

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


    def do_exit(self, arg):
        print("Exiting...")
        return True
    
if __name__ == "__main__":
    try:
        NanoShell().cmdloop()

    except KeyboardInterrupt:
        print("Exiting...")
