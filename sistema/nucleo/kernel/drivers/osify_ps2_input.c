/* ==============================================================================
 * OSify PS/2 Keyboard & Mouse Input Driver (sistema/nucleo/kernel/drivers/osify_ps2_input.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Decodifica hardware scancode Set 1 per tastiera e buffer ad anello circolare.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"
#include "../include/osify_desktop.h"

#define PS2_DATA_PORT   0x60
#define PS2_STATUS_PORT 0x64

#define KBD_BUF_SIZE 128

static char g_kbd_buffer[KBD_BUF_SIZE];
static size_t g_buf_head = 0;
static size_t g_buf_tail = 0;

/* Mappa Scancode Set 1 standard -> Carattere ASCII */
static const char g_scancode_map[128] = {
    0,  27, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', '\b',
    '\t', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\n',
    0, /* Ctrl */
    'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '\'', '`',
    0, /* Left Shift */
    '\\', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/',
    0, /* Right Shift */
    '*', 0, ' '
};

static bool g_ps2_hw_active = false;
static int s_mouse_x = 512;
static int s_mouse_y = 384;
static uint8_t s_prev_mouse_buttons = 0;
static uint8_t s_mouse_cycle = 0;
static uint8_t s_mouse_packet[3];

static inline void outb_kbd(uint16_t port, uint8_t val) {
    if (!g_ps2_hw_active) return;
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

static inline uint8_t inb_kbd(uint16_t port) {
    if (!g_ps2_hw_active) return 0;
#if defined(__x86_64__) || defined(__i386__)
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port;
    return 0;
#endif
}

void osify_keyboard_init(void) {
    g_buf_head = 0;
    g_buf_tail = 0;
    osify_memset(g_kbd_buffer, 0, sizeof(g_kbd_buffer));
    g_ps2_hw_active = true;

    /* Inizializzazione Hardware Mouse PS/2 Aux Port */
    /* Abilita porta ausiliaria (mouse) sul controller 8042 */
    outb_kbd(PS2_STATUS_PORT, 0xA8);

    /* Invia comando 0xF4 (Enable Data Reporting) al mouse */
    outb_kbd(PS2_STATUS_PORT, 0xD4);
    outb_kbd(PS2_DATA_PORT, 0xF4);
}

void osify_keyboard_poll(void) {
    if (!g_ps2_hw_active) return;

    uint8_t status = inb_kbd(PS2_STATUS_PORT);
    while (status & 0x01) { /* Finché ci sono byte disponibili nel buffer hardware */
        uint8_t data = inb_kbd(PS2_DATA_PORT);

        /* Controllo se il byte proviene dal mouse (bit 5 di status attivo) */
        if (status & 0x20) {
            if (s_mouse_cycle == 0) {
                /* Il primo byte di un pacchetto mouse PS/2 deve avere il bit 3 impostato a 1 */
                if (data & 0x08) {
                    s_mouse_packet[0] = data;
                    s_mouse_cycle = 1;
                }
            } else if (s_mouse_cycle == 1) {
                s_mouse_packet[1] = data;
                s_mouse_cycle = 2;
            } else if (s_mouse_cycle == 2) {
                s_mouse_packet[2] = data;
                s_mouse_cycle = 0;

                /* Decodifica movimento X e Y */
                int dx = (int8_t)s_mouse_packet[1];
                int dy = (int8_t)s_mouse_packet[2];
                uint8_t buttons = s_mouse_packet[0] & 0x07;

                /* Inverti Y (convenzione PS/2 rispetto allo schermo) */
                s_mouse_x += dx;
                s_mouse_y -= dy;

                if (s_mouse_x < 0) s_mouse_x = 0;
                if (s_mouse_x > 1023) s_mouse_x = 1023;
                if (s_mouse_y < 0) s_mouse_y = 0;
                if (s_mouse_y > 767) s_mouse_y = 767;

                osify_framebuffer_t *fb = osify_desktop_get_fb();
                if (fb) {
                    osify_desktop_move_mouse(fb, s_mouse_x, s_mouse_y);
                    if (buttons != s_prev_mouse_buttons && buttons != 0) {
                        osify_desktop_click_mouse(fb, s_mouse_x, s_mouse_y, buttons);
                    }
                }
                s_prev_mouse_buttons = buttons;
            }
        } else {
            /* Byte da Tastiera PS/2 */
            if (!(data & 0x80)) { /* Key Press (non rilascio) */
                char c = (data < 128) ? g_scancode_map[data] : 0;
                if (c) {
                    size_t next = (g_buf_head + 1) % KBD_BUF_SIZE;
                    if (next != g_buf_tail) {
                        g_kbd_buffer[g_buf_head] = c;
                        g_buf_head = next;
                    }
                }
            }
        }
        status = inb_kbd(PS2_STATUS_PORT);
    }
}

/* Prelievo del prossimo tasto dal buffer */
char osify_keyboard_get_key(void) {
    if (g_buf_head == g_buf_tail) {
        return 0; /* Nessun tasto in attesa */
    }
    char c = g_kbd_buffer[g_buf_tail];
    g_buf_tail = (g_buf_tail + 1) % KBD_BUF_SIZE;
    return c;
}

void osify_keyboard_inject_char(char c) {
    size_t next = (g_buf_head + 1) % KBD_BUF_SIZE;
    if (next != g_buf_tail) {
        g_kbd_buffer[g_buf_head] = c;
        g_buf_head = next;
    }
}
