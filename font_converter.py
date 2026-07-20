import struct
import argparse
from PIL import ImageFont, Image, ImageDraw

def generate_font_bin(ttf_path, output_path, font_size, first_char=32, last_char=126):
    font = ImageFont.truetype(ttf_path, font_size)

    glyph_metrics = []
    bitmap_bytes = bytearray()

    current_offset = 0

    for _char in range(first_char, last_char + 1):
        char = chr(_char)
        box = font.getbbox(char)
        advance = font.getlength(char)


        if char.isspace() or box is None:
            width, height, x_offset, y_offset = 0, 0, 0, 0
        else:
            x_offset = box[0]
            y_offset = box[1]
            width = box[2] - x_offset
            height = box[3] - y_offset

        if width > 0 and height > 0:
            img = Image.new('L', (width, height), 0)
            draw = ImageDraw.Draw(img)


            draw.text((-x_offset, -y_offset), char, fill=255, font=font)
            char_pixels = list(img.getdata())
            bitmap_bytes.extend(char_pixels)
            data_size = len(char_pixels)

        else:
            data_size = 0

        safe_x_offset = max(-128, min(127, x_offset))
        safe_y_offset = max(-128, min(127, y_offset))


        glyph_metrics.append((
            current_offset,
            width,
            height,
            int(safe_x_offset),
            int(safe_y_offset),
            int(advance)
        ))

        current_offset += data_size

    with open(output_path, 'wb') as bin_file:
        header = struct.pack('<4sHHHHH', b'FONT', 1, len(glyph_metrics), font_size, 0, 0)
        bin_file.write(header)


        for metric in glyph_metrics:
            bin_file.write(
                struct.pack(
                    '<IBBbbH',
                    metric[0],
                    metric[1],
                    metric[2],
                    metric[3],
                    metric[4],
                    metric[5]
                )
            )

        bin_file.write(bitmap_bytes)

    print("File generated successfully")


def main():
    parser = argparse.ArgumentParser(
        description="A utility tool to convert .ttf font to NanoUI compatible font format"
    )

    parser.add_argument(
        "ttf_path",
        type=str,
        help="Target .ttf file"
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="Save location of output file"
    )

    parser.add_argument(
        "font_size",
        type=int,
        help="Desired font size."
    )

    optional_group = parser.add_argument_group("Additional Options")

    optional_group.add_argument(
        "-fc", "--first-char",
        type=int,
        default=32,
        help="Index of first character"
    )

    optional_group.add_argument(
        "-lc", "--last-char",
        type=int,
        default=126,
        help="Index of last character"        
    )

    args = parser.parse_args()

    generate_font_bin(args.ttf_path, args.output_path, args.font_size, args.first_char, args.last_char)

if __name__ == "__main__":
    main()

