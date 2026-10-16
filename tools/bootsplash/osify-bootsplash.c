/*
 * OSify Framebuffer Bootsplash
 * Ingegnerizzato per OSify (Architettura 2050)
 * Render nativo su /dev/fb0 con animazione reale e alpha blending
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/fb.h>
#include "logo_data.h"

static volatile int running = 1;

static void handle_signal(int sig) {
    (void)sig;
    running = 0;
}

static inline void put_pixel(unsigned char *fb, int x, int y, int stride, int bpp,
                            unsigned char r, unsigned char g, unsigned char b) {
    if (bpp == 32) {
        unsigned int *p = (unsigned int *)(fb + y * stride + x * 4);
        *p = (r << 16) | (g << 8) | b;
    } else if (bpp == 16) {
        unsigned short *p = (unsigned short *)(fb + y * stride + x * 2);
        *p = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
    } else if (bpp == 24) {
        unsigned char *p = fb + y * stride + x * 3;
        p[0] = b;
        p[1] = g;
        p[2] = r;
    }
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    signal(SIGTERM, handle_signal);
    signal(SIGINT, handle_signal);
    signal(SIGHUP, handle_signal);

    int fb_fd = open("/dev/fb0", O_RDWR);
    if (fb_fd < 0) {
        // Fallback silenzioso se framebuffer non presente
        return 0;
    }

    struct fb_var_screeninfo vinfo;
    struct fb_fix_screeninfo finfo;

    if (ioctl(fb_fd, FBIOGET_VSCREENINFO, &vinfo) < 0 ||
        ioctl(fb_fd, FBIOGET_FSCREENINFO, &finfo) < 0) {
        close(fb_fd);
        return 0;
    }

    int width = vinfo.xres;
    int height = vinfo.yres;
    int bpp = vinfo.bits_per_pixel;
    int stride = finfo.line_length;
    long screensize = finfo.smem_len;

    if (screensize <= 0 || width <= 0 || height <= 0) {
        close(fb_fd);
        return 0;
    }

    unsigned char *fb = (unsigned char *)mmap(0, screensize, PROT_READ | PROT_WRITE, MAP_SHARED, fb_fd, 0);
    if (fb == MAP_FAILED) {
        close(fb_fd);
        return 0;
    }

    // 1. Sfondo OLED nero profondo #07090e
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            put_pixel(fb, x, y, stride, bpp, 7, 9, 14);
        }
    }

    // 2. Disegna il Logo OSify 128x128 centrato con Alpha Blending
    int logo_x = (width - LOGO_W) / 2;
    int logo_y = (height - LOGO_H) / 2 - 25;

    for (int ly = 0; ly < LOGO_H; ly++) {
        int py = logo_y + ly;
        if (py < 0 || py >= height) continue;
        for (int lx = 0; lx < LOGO_W; lx++) {
            int px = logo_x + lx;
            if (px < 0 || px >= width) continue;

            int idx = (ly * LOGO_W + lx) * 4;
            unsigned char r = osify_logo_rgba[idx + 0];
            unsigned char g = osify_logo_rgba[idx + 1];
            unsigned char b = osify_logo_rgba[idx + 2];
            unsigned char a = osify_logo_rgba[idx + 3];

            if (a > 10) {
                // Blend sopra lo sfondo 7, 9, 14
                float alpha = a / 255.0f;
                unsigned char out_r = (unsigned char)(r * alpha + 7 * (1.0f - alpha));
                unsigned char out_g = (unsigned char)(g * alpha + 9 * (1.0f - alpha));
                unsigned char out_b = (unsigned char)(b * alpha + 14 * (1.0f - alpha));
                put_pixel(fb, px, py, stride, bpp, out_r, out_g, out_b);
            }
        }
    }

    // 3. Coordinate Barra di Progresso Dinamica
    int bar_w = 220;
    int bar_h = 5;
    int bar_x = (width - bar_w) / 2;
    int bar_y = logo_y + LOGO_H + 35;

    // Disegna binario di sfondo barra (#1e293b)
    for (int by = bar_y - 1; by <= bar_y + bar_h; by++) {
        if (by < 0 || by >= height) continue;
        for (int bx = bar_x - 1; bx <= bar_x + bar_w; bx++) {
            if (bx < 0 || bx >= width) continue;
            put_pixel(fb, bx, by, stride, bpp, 30, 41, 59);
        }
    }

    // 4. Ciclo di animazione reale (avanzamento progressivo con shimmer luminescente)
    int progress = 0;
    int shimmer_pos = 0;

    while (running && progress <= 100) {
        // Verifica se X11 o Desktop sono pronti
        if (access("/tmp/.X11-unix/X0", F_OK) == 0 ||
            access("/run/osify-desktop-ready", F_OK) == 0) {
            break;
        }

        int filled_w = (bar_w * progress) / 100;

        for (int by = bar_y; by < bar_y + bar_h; by++) {
            if (by < 0 || by >= height) continue;
            for (int bx = bar_x; bx < bar_x + filled_w; bx++) {
                if (bx < 0 || bx >= width) continue;

                // Gradiente dal ciano #06b6d4 al viola #7c3aed
                float t = (float)(bx - bar_x) / (float)bar_w;
                unsigned char r = (unsigned char)(6 + (124 - 6) * t);
                unsigned char g = (unsigned char)(182 + (58 - 182) * t);
                unsigned char b = (unsigned char)(212 + (237 - 212) * t);

                // Effetto shimmer luminescente mobile
                int dist = abs(bx - (bar_x + shimmer_pos));
                if (dist < 15) {
                    float glow = 1.0f - (float)dist / 15.0f;
                    r = (unsigned char)(r + (255 - r) * glow * 0.6f);
                    g = (unsigned char)(g + (255 - g) * glow * 0.6f);
                    b = (unsigned char)(b + (255 - b) * glow * 0.6f);
                }

                put_pixel(fb, bx, by, stride, bpp, r, g, b);
            }
        }

        shimmer_pos = (shimmer_pos + 6) % (bar_w + 20);
        if (progress < 95) {
            progress += 1;
        }

        usleep(33000); // ~30 FPS
    }

    munmap(fb, screensize);
    close(fb_fd);
    return 0;
}
