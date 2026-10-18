/* ==============================================================================
 * OSify Native Dark Glass Graphics Engine (sistema/nucleo/kernel/drivers/osify_native_graphics.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Rendering grafico diretto su Framebuffer lineare (GOP/UEFI/VESA):
 * Zero server X11/Wayland, zero dipendenze, estetica Dark Glass nativa a 32bpp.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"

/* Palette Colori Ufficiale Dark Glass OSify */
#define OSIFY_COLOR_BG_DARK     0xFF0B101D  /* Blu Notte Profondo */
#define OSIFY_COLOR_CARD_GLASS  0xFF141C2E  /* Dark Glass Card */
#define OSIFY_COLOR_CYAN_NEON   0xFF06B6D4  /* Ciano Elettrico */
#define OSIFY_COLOR_PURPLE_NEON 0xFF8B5CF6  /* Viola Cyber */
#define OSIFY_COLOR_TEXT_WHITE  0xFFF8FAFC  /* Bianco Puro Testo */
#define OSIFY_COLOR_TEXT_DIM    0xFF94A3B8  /* Grigio Ardesia */

void osify_fb_init(osify_framebuffer_t *fb, uint32_t width, uint32_t height, void *fb_addr) {
    if (!fb || !fb_addr) return;
    fb->width = width;
    fb->height = height;
    fb->pitch = width * 4;
    fb->bpp = 32;
    fb->buffer = (uint32_t *)fb_addr;
    fb->back_buffer = NULL; /* Assegnato dall'allocatore bare-metal se disponibile */
}

/* Pulizia dello Schermo con Colore di Fondo */
void osify_fb_clear(osify_framebuffer_t *fb, uint32_t hex_color) {
    if (!fb || !fb->buffer) return;
    uint32_t total_pixels = fb->width * fb->height;
    for (uint32_t i = 0; i < total_pixels; i++) {
        fb->buffer[i] = hex_color;
    }
}

/* Disegno di un Rettangolo Solido */
void osify_fb_draw_rect(osify_framebuffer_t *fb, int x, int y, int w, int h, uint32_t hex_color) {
    if (!fb || !fb->buffer) return;

    int x_end = x + w;
    int y_end = y + h;

    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x_end > (int)fb->width) x_end = (int)fb->width;
    if (y_end > (int)fb->height) y_end = (int)fb->height;

    for (int curr_y = y; curr_y < y_end; curr_y++) {
        uint32_t *row = &fb->buffer[curr_y * fb->width];
        for (int curr_x = x; curr_x < x_end; curr_x++) {
            row[curr_x] = hex_color;
        }
    }
}

/* Disegno Geometrico di Squircle con Angoli Arrotondati (Stile OSify macOS/Glass) */
void osify_fb_draw_squircle(osify_framebuffer_t *fb, int x, int y, int size, int radius, uint32_t hex_color) {
    if (!fb || !fb->buffer || radius <= 0) return;

    int r2 = radius * radius;
    int inner_w = size - 2 * radius;
    int inner_h = size - 2 * radius;

    for (int py = 0; py < size; py++) {
        int target_y = y + py;
        if (target_y < 0 || target_y >= (int)fb->height) continue;

        for (int px = 0; px < size; px++) {
            int target_x = x + px;
            if (target_x < 0 || target_x >= (int)fb->width) continue;

            /* Controllo angoli arrotondati */
            int dx = 0, dy = 0;
            if (px < radius) dx = radius - px;
            else if (px >= radius + inner_w) dx = px - (radius + inner_w);

            if (py < radius) dy = radius - py;
            else if (py >= radius + inner_h) dy = py - (radius + inner_h);

            if (dx * dx + dy * dy <= r2) {
                fb->buffer[target_y * fb->width + target_x] = hex_color;
            }
        }
    }
}

/* Scambio dei Buffer per Evitare Tearing (Double Buffering) */
void osify_fb_swap_buffers(osify_framebuffer_t *fb) {
    if (!fb || !fb->buffer || !fb->back_buffer) return;
    uint32_t total_pixels = fb->width * fb->height;
    for (uint32_t i = 0; i < total_pixels; i++) {
        fb->buffer[i] = fb->back_buffer[i];
    }
}

/* --- Driver Hardware Bochs/QEMU BGA (Bochs Graphics Adapter) --- */
static inline void outw_io(uint16_t port, uint16_t val) {
#if defined(__i386__) || defined(__x86_64__)
    __asm__ volatile ("outw %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

static inline uint16_t inw_io(uint16_t port) {
#if defined(__i386__) || defined(__x86_64__)
    uint16_t ret;
    __asm__ volatile ("inw %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port; return 0;
#endif
}

bool osify_bga_set_video_mode(uint32_t width, uint32_t height, uint32_t bpp) {
    outw_io(0x01CE, 0);
    uint16_t id = inw_io(0x01CF);
    if (id < 0xB0C0 || id > 0xB0C6) {
        return false;
    }
    /* Disabilita prima di riconfigurare */
    outw_io(0x01CE, 4);
    outw_io(0x01CF, 0);

    /* Imposta parametri geometrici e profondita */
    outw_io(0x01CE, 1);
    outw_io(0x01CF, (uint16_t)width);
    outw_io(0x01CE, 2);
    outw_io(0x01CF, (uint16_t)height);
    outw_io(0x01CE, 3);
    outw_io(0x01CF, (uint16_t)bpp);

    /* Abilita Linear Framebuffer Mode (0x01 | 0x40) */
    outw_io(0x01CE, 4);
    outw_io(0x01CF, 0x41);

    return true;
}

