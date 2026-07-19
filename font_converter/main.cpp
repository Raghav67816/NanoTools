#include <freetype2/ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H

#include <iostream>
#include <stdint.h>
#include <vector>

using namespace std;

struct Glyph
{
    uint16_t width;
    uint16_t height;

    int16_t bearingX;
    int16_t bearingY;

    uint16_t advance;
    uint32_t bitmapSize;

    std::vector<uint8_t> bitmap;
};

vector<Glyph> glyphs;

int main(int argc, char *argv[])
{

    if(argc < 3){
        cout << "Insufficient arguments" << endl;
        cout << "Usage: nanofont <file_path> <size>" << endl;
    }

    FT_Library library;
    FT_Face font_face;

    if (FT_Init_FreeType(&library))
    {
        cout << "Failed to init FreeType" << endl;
        FT_Done_FreeType(library);
        return 1;
    }

    if (FT_New_Face(library, argv[1], 0, &font_face))
    {
        cout << "Failed to load: " << argv[1] << endl;
        FT_Done_FreeType(library);
        return -1;
    }

    cout << "Loaded: " << argv[1] << endl;
    cout << "Rendering at: " << argv[2] << "px" << endl;

    int font_size = atoi(argv[2]);
    FT_Set_Pixel_Sizes(font_face, 0, font_size);

    for (char c = 32; c <= 126; c++)
    {
        if (FT_Load_Char(font_face, c, FT_LOAD_RENDER))
        {
            continue;
        }

        FT_GlyphSlot glyph = font_face->glyph;
        Glyph out;

        out.width = glyph->bitmap.width;
        out.height = glyph->bitmap.rows;
        out.bearingX = glyph->bitmap_left;
        out.bearingY = glyph->bitmap_top;
        out.advance = glyph->advance.x >> 6;


        size_t size = glyph->bitmap.pitch * glyph->bitmap.rows;
        out.bitmapSize = size;


        out.bitmap.assign(
            glyph->bitmap.buffer,
            glyph->bitmap.buffer + size
        );

        glyphs.push_back(move(out));
    }

    FT_Done_Face(font_face);
    FT_Done_FreeType(library);
    return 0;
}