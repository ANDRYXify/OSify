/* ==============================================================================
 * OSify Native Dark Glass Graphics Engine (sistema/nucleo/kernel/drivers/osify_native_graphics.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Rendering grafico diretto su Framebuffer lineare (GOP/UEFI/VESA):
 * Zero server X11/Wayland, zero dipendenze esterne, estetica Dark Glass a 32bpp.
 * Sottosistema PCI Driverless per aggancio automatico a qualsiasi controller video.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_hetero_dispatch.h"

/* Palette Colori Ufficiale Dark Glass OSify */
#define OSIFY_COLOR_BG_DARK     0xFF0B101D  /* Blu Notte Profondo */
#define OSIFY_COLOR_CARD_GLASS  0xFF141C2E  /* Dark Glass Card */
#define OSIFY_COLOR_CYAN_NEON   0xFF06B6D4  /* Ciano Elettrico */
#define OSIFY_COLOR_PURPLE_NEON 0xFF8B5CF6  /* Viola Cyber */
#define OSIFY_COLOR_TEXT_WHITE  0xFFF8FAFC  /* Bianco Puro Testo */
#define OSIFY_COLOR_TEXT_DIM    0xFF94A3B8  /* Grigio Ardesia */

/* --- Lettura Registri PCI Configuration Space Driverless --- */
uint32_t osify_pci_read_config_dword(uint8_t bus, uint8_t slot, uint8_t func, uint8_t offset) {
#if defined(__i386__) || defined(__x86_64__)
    uint32_t address = (uint32_t)((1U << 31) | ((uint32_t)bus << 16) |
                                  ((uint32_t)slot << 11) | ((uint32_t)func << 8) |
                                  (offset & 0xFC));
    __asm__ volatile ("outl %0, %1" : : "a"(address), "Nd"((uint16_t)0xCF8));
    uint32_t data;
    __asm__ volatile ("inl %1, %0" : "=a"(data) : "Nd"((uint16_t)0xCFC));
    return data;
#else
    (void)bus; (void)slot; (void)func; (void)offset;
    return 0xFFFFFFFF;
#endif
}

/* Scansione del Bus PCI alla ricerca del Display Controller (VGA o 3D) */
bool osify_pci_find_display(uint32_t *out_bar, uint16_t *out_vendor, uint16_t *out_device, uint32_t *out_vram_size) {
    for (uint8_t bus = 0; bus < 8; bus++) {
        for (uint8_t slot = 0; slot < 32; slot++) {
            for (uint8_t func = 0; func < 8; func++) {
                uint32_t vendor_device = osify_pci_read_config_dword(bus, slot, func, 0x00);
                uint16_t vendor = (uint16_t)(vendor_device & 0xFFFF);
                uint16_t device = (uint16_t)((vendor_device >> 16) & 0xFFFF);
                if (vendor == 0xFFFF || vendor == 0x0000) continue;

                uint32_t class_rev = osify_pci_read_config_dword(bus, slot, func, 0x08);
                uint8_t class_code = (uint8_t)((class_rev >> 24) & 0xFF);

                /* Classe 0x03 = Display Controller (VGA compatibile 0x0300, 3D Controller 0x0302) */
                if (class_code == 0x03) {
                    if (out_vendor) *out_vendor = vendor;
                    if (out_device) *out_device = device;

                    /* Leggi BAR0 per il linear framebuffer address */
                    uint32_t bar0 = osify_pci_read_config_dword(bus, slot, func, 0x10);
                    uint32_t bar_addr = bar0 & 0xFFFFFFF0;

                    if (bar_addr != 0) {
                        if (out_bar) *out_bar = bar_addr;
                        if (out_vram_size) *out_vram_size = 16 * 1024 * 1024; /* 16 MB garantiti */
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

/* Inizializzazione del Framebuffer Diretto */
void osify_fb_init(osify_framebuffer_t *fb, uint32_t width, uint32_t height, void *fb_addr) {
    if (!fb || !fb_addr) return;
    fb->width = width;
    fb->height = height;
    fb->pitch = width * 4;
    fb->bpp = 32;
    fb->buffer = (uint32_t *)fb_addr;
    fb->back_buffer = NULL;
}

/* Pulizia dello Schermo con Burst Unrolling ad Alte Prestazioni */
void osify_fb_clear(osify_framebuffer_t *fb, uint32_t hex_color) {
    if (!fb || !fb->buffer) return;
    uint32_t total_pixels = fb->width * fb->height;
    uint32_t i = 0;

    /* Burst di 8 dword per ciclo per massimizzare il throughput del bus video */
    for (; i + 8 <= total_pixels; i += 8) {
        fb->buffer[i + 0] = hex_color;
        fb->buffer[i + 1] = hex_color;
        fb->buffer[i + 2] = hex_color;
        fb->buffer[i + 3] = hex_color;
        fb->buffer[i + 4] = hex_color;
        fb->buffer[i + 5] = hex_color;
        fb->buffer[i + 6] = hex_color;
        fb->buffer[i + 7] = hex_color;
    }
    for (; i < total_pixels; i++) {
        fb->buffer[i] = hex_color;
    }
}

/* Disegno di un Rettangolo Solido con Line Burst */
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
        int curr_x = x;
        for (; curr_x + 4 <= x_end; curr_x += 4) {
            row[curr_x + 0] = hex_color;
            row[curr_x + 1] = hex_color;
            row[curr_x + 2] = hex_color;
            row[curr_x + 3] = hex_color;
        }
        for (; curr_x < x_end; curr_x++) {
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
    osify_driverless_copy_buffer(fb->buffer, fb->back_buffer, fb->width * fb->height);
}

/* Driverless Copy Buffer con Burst Optimization a 256-bit */
void osify_driverless_copy_buffer(uint32_t *dest, const uint32_t *src, size_t total_pixels) {
    if (!dest || !src) return;
    size_t i = 0;
    for (; i + 8 <= total_pixels; i += 8) {
        dest[i + 0] = src[i + 0];
        dest[i + 1] = src[i + 1];
        dest[i + 2] = src[i + 2];
        dest[i + 3] = src[i + 3];
        dest[i + 4] = src[i + 4];
        dest[i + 5] = src[i + 5];
        dest[i + 6] = src[i + 6];
        dest[i + 7] = src[i + 7];
    }
    for (; i < total_pixels; i++) {
        dest[i] = src[i];
    }
}

/* Driverless Blit Rect ad alto throughput */
void osify_driverless_blit_rect(uint32_t *dest, uint32_t dest_pitch_pixels,
                                int x, int y, int w, int h, uint32_t color) {
    if (!dest) return;
    for (int r = 0; r < h; r++) {
        uint32_t *row = &dest[(y + r) * dest_pitch_pixels + x];
        int c = 0;
        for (; c + 4 <= w; c += 4) {
            row[c + 0] = color;
            row[c + 1] = color;
            row[c + 2] = color;
            row[c + 3] = color;
        }
        for (; c < w; c++) {
            row[c] = color;
        }
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
