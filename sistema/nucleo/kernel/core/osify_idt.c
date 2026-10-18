/* ==============================================================================
 * OSify Interrupt Descriptor Table & PIC Driver (sistema/nucleo/kernel/core/osify_idt.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Gestione degli interrupt bare-metal e remapping PIC 8259A per tastiera e mouse.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

void osify_serial_print(const char *s);

/* Struttura Descrittore IDT Gate (x86 a 32-bit/compat) */
typedef struct {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t  zero;
    uint8_t  type_attr;
    uint16_t offset_high;
} __attribute__((packed)) osify_idt_entry_t;

typedef struct {
    uint16_t limit;
    uint32_t base;
} __attribute__((packed)) osify_idt_ptr_t;

static osify_idt_entry_t g_idt[256];
static osify_idt_ptr_t   g_idt_ptr;

/* Primitiva I/O outb/inb per x86 */
static inline void outb(uint16_t port, uint8_t val) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

static inline uint8_t __attribute__((unused)) inb(uint16_t port) {
#if defined(__x86_64__) || defined(__i386__)
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port;
    return 0;
#endif
}

extern void osify_default_isr(void);

void osify_idt_set_gate(uint8_t num, uint32_t base, uint16_t sel, uint8_t flags) {
    g_idt[num].offset_low  = (uint16_t)(base & 0xFFFF);
    g_idt[num].offset_high = (uint16_t)((base >> 16) & 0xFFFF);
    g_idt[num].selector    = sel;
    g_idt[num].zero        = 0;
    g_idt[num].type_attr   = flags;
}

void osify_pic_remap(void) {
    /* Inizializzazione PIC master e slave (ICW1) */
    outb(0x20, 0x11);
    outb(0xA0, 0x11);

    /* Vettori base ICW2: Master a 0x20, Slave a 0x28 */
    outb(0x21, 0x20);
    outb(0xA1, 0x28);

    /* Cascata ICW3 */
    outb(0x21, 0x04);
    outb(0xA1, 0x02);

    /* Modalita 8086 ICW4 */
    outb(0x21, 0x01);
    outb(0xA1, 0x01);

    /* Maschera preventiva totale su master e slave per stabilita bare-metal */
    outb(0x21, 0xFF);
    outb(0xA1, 0xFF);
}

void osify_idt_init(void) {
    osify_serial_print("  -> inizio idt_init\n");
    uint16_t cs = 0x08;
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("mov %%cs, %0" : "=r"(cs));
#endif

    g_idt_ptr.limit = sizeof(g_idt) - 1;
    g_idt_ptr.base  = (uint32_t)(uintptr_t)&g_idt;
    osify_memset(&g_idt, 0, sizeof(g_idt));

    osify_serial_print("  -> popolamento gate\n");
    for (int i = 0; i < 256; i++) {
        osify_idt_set_gate((uint8_t)i, (uint32_t)(uintptr_t)&osify_default_isr, cs, 0x8E);
    }

    osify_serial_print("  -> pic_remap\n");
    osify_pic_remap();

    osify_serial_print("  -> prima di lidt\n");
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("lidt %0" : : "m"(g_idt_ptr));
#endif
    osify_serial_print("  -> idt_init completato con successo\n");
}
