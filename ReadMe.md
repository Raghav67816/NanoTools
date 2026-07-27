# NanoTools

Design, develop and deploy faster with NanoUI tools. No more C arrays for your assets.

Now upload your assets directly into SPIFFS partition and load assets using **FileManager (NanoUI)**. No more re-compiling just to change an icon.

## Features
 - .ttf to bin converter
 - nanoshell (interact with your ESP based boards with ease.)

Please note that **nanoshell only works with ESP ecosystem. Support for more hardware will be coming soon**

## Font Converter Usage

```bash
usage: font_converter.bin [-h] [-fc FIRST_CHAR] [-lc LAST_CHAR] ttf_path output_path font_size

A utility tool to convert .ttf font to NanoUI compatible font format

positional arguments:
  ttf_path              Target .ttf file
  output_path           Save location of output file
  font_size             Desired font size.

options:
  -h, --help            show this help message and exit

Additional Options:
  -fc, --first-char FIRST_CHAR
                        Index of first character
  -lc, --last-char LAST_CHAR
                        Index of last character
```

Example command:

We are assuming that you have a .ttf file.

```bash
font-converter.bin ./font.ttf ./data/font.bin 18
```

This creates a glyph of 18px characters where first character start at **32** and last character is at **125** by default.
