/* ==============================================================================
 * OSify Native Window Manager & Desktop Environment
 * (sistema/nucleo/kernel/include/osify_desktop.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Desktop Environment autonomo a 32bpp direttamente su Linear Framebuffer:
 * Finestre fluttuanti Dark Glass, Floating Dock, cursore mouse vettoriale e Shell.
 * Zero dipendenze da server X11, Wayland o toolkit esterni.
 * ==============================================================================
 */

#ifndef OSIFY_DESKTOP_H
#define OSIFY_DESKTOP_H

#include "osify_kernel.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define MAX_WINDOWS 16

/* Finestra Grafica Dark Glass Nativa */
typedef struct {
    uint32_t id;
    int      x;
    int      y;
    int      w;
    int      h;
    char     title[64];
    bool     is_visible;
    bool     is_focused;
    uint32_t bg_color;
} osify_window_t;

/* Cursore del Mouse Vettoriale */
typedef struct {
    int  x;
    int  y;
    bool is_visible;
    uint32_t saved_under[16 * 16]; /* Buffer per ripristinare i pixel sotto al mouse */
} osify_mouse_cursor_t;

/* Inizializzazione Desktop Environment */
void osify_desktop_init(osify_framebuffer_t *fb);
void osify_desktop_render_all(osify_framebuffer_t *fb);
void osify_desktop_handle_key(osify_framebuffer_t *fb, char c);
void osify_desktop_move_mouse(osify_framebuffer_t *fb, int new_x, int new_y);
void osify_desktop_click_mouse(osify_framebuffer_t *fb, int x, int y, uint8_t buttons);
void osify_desktop_cycle_focus(void);
osify_framebuffer_t *osify_desktop_get_fb(void);
void osify_desktop_set_fb(osify_framebuffer_t *fb);

/* Gestione Finestre */
osify_window_t *osify_wm_create_window(int x, int y, int w, int h, const char *title);
void osify_wm_draw_window(osify_framebuffer_t *fb, const osify_window_t *win);

/* Shell Nativa Integrata su Framebuffer */
void osify_shell_init(void);
void osify_shell_input_char(osify_framebuffer_t *fb, char c);
void osify_shell_execute_cmd(osify_framebuffer_t *fb, const char *cmd);

#endif /* OSIFY_DESKTOP_H */
