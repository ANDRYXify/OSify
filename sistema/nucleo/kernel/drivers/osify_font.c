/* ==============================================================================
 * OSify Dark Glass Native Typography & Glyph Engine
 * (sistema/nucleo/kernel/drivers/osify_font.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Rendering tipografico diretto a 8x16 su Framebuffer a 32bpp:
 * Zero server X11/Wayland, zero librerie esterne.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "osify_font_data.h"

void osify_fb_draw_char(osify_framebuffer_t *fb, int x, int y, char c, uint32_t fg_color) {
    if (!fb || !fb->buffer) return;
    unsigned char uc = (unsigned char)c;

    const uint8_t *glyph = g_font_8x16[uc];
    for (int row = 0; row < 16; row++) {
        int target_y = y + row;
        if (target_y < 0 || target_y >= (int)fb->height) continue;

        uint8_t bits = glyph[row];
        for (int col = 0; col < 8; col++) {
            int target_x = x + col;
            if (target_x < 0 || target_x >= (int)fb->width) continue;

            if (bits & (0x80 >> col)) {
                fb->buffer[target_y * fb->width + target_x] = fg_color;
            }
        }
    }
}

void osify_fb_draw_string(osify_framebuffer_t *fb, int x, int y, const char *str, uint32_t fg_color) {
    if (!fb || !str) return;
    int curr_x = x;
    while (*str) {
        if (*str == '\n') {
            y += 18;
            curr_x = x;
        } else {
            osify_fb_draw_char(fb, curr_x, y, *str, fg_color);
            curr_x += 9;
        }
        str++;
    }
}
