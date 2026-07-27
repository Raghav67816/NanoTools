import subprocess
from cmd import Cmd
from os import getcwd
from struct import unpack
from os.path import exists
from esptool.cmds import detect_chip, attach_flash, read_flash, write_flash, reset_chip

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

        if self.addr != None or self.addr != "":
            print("Address not set. Abort.")
            return

        with open(f'{getcwd()}/image.bin', "rb") as fs_image:
            write_flash(self.esp, ([self.addr, fs_image]))

        print("Writing finished...")

        reset_chip(self.esp)
        print("Rebooting chip.")


    def do_exit(self, arg):
        print("Exiting...")
        return True
    
if __name__ == "__main__":
    try:
        NanoShell().cmdloop()

    except KeyboardInterrupt:
        print("Exiting...")
