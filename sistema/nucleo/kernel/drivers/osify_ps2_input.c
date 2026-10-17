/* ==============================================================================
 * OSify PS/2 Keyboard & Mouse Input Driver (sistema/nucleo/kernel/drivers/osify_ps2_input.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Decodifica hardware scancode Set 1 per tastiera e buffer ad anello circolare.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

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

static inline uint8_t inb_kbd(uint16_t port) {
#if defined(__x86_64__) || defined(__i386__)
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port;
    return 0;
#endif
}

/* Invocata all'interrupt IRQ 1 o tramite polling continuo */
void osify_keyboard_poll(void) {
    uint8_t status = inb_kbd(PS2_STATUS_PORT);
    if (status & 0x01) { /* Dato pronto */
        uint8_t scancode = inb_kbd(PS2_DATA_PORT);
        if (!(scancode & 0x80)) { /* Key Press (non rilascio) */
            char c = (scancode < 128) ? g_scancode_map[scancode] : 0;
            if (c) {
                size_t next = (g_buf_head + 1) % KBD_BUF_SIZE;
                if (next != g_buf_tail) {
                    g_kbd_buffer[g_buf_head] = c;
                    g_buf_head = next;
                }
            }
        }
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

void osify_keyboard_init(void) {
    g_buf_head = 0;
    g_buf_tail = 0;
    osify_memset(g_kbd_buffer, 0, sizeof(g_kbd_buffer));
}
