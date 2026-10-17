/* ==============================================================================
 * OSify Kernel Bare-Metal Main Entry Point (sistema/nucleo/kernel/core/osify_main.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Punto di ingresso assoluto bare-metal dopo il salto da boot.S.
 * Zero dipendenze esterne: OSify governa direttamente il silicio.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

/* Prototipi interni dei sottosistemi */
void osify_idt_init(void);
void osify_keyboard_init(void);
void osify_keyboard_poll(void);
char osify_keyboard_get_key(void);

/* Entry point C invocato da boot.S */
void osify_kernel_main(uint32_t magic, void *boot_info) {
    (void)magic;
    (void)boot_info;

    /* 1. Inizializzazione Vettori Interrupt & Controller Input */
    osify_idt_init();
    osify_keyboard_init();

    /* 2. Introspezione Silicio & Profilo Cover Nuda */
    osify_hardware_skin_t skin;
    osify_memset(&skin, 0, sizeof(skin));
    skin.ram_total_bytes = 2ULL * 1024ULL * 1024ULL * 1024ULL; /* 2GB default se non passati dal bootloader */
    osify_hardware_detect(&skin);
    osify_adaptive_skin_init(&skin);

    /* 3. Memory Management PMM & VMM con W^X */
    osify_pmm_init(skin.ram_total_bytes);

    /* 4. Sicurezza Livello 0: SIP & Seatbelt Sandbox (macOS style) */
    osify_sec_init();

    /* 5. Anti-Cheat Guard & Attestazione Hardware (TPM 2.0, Secure Boot) */
    osify_anticheat_init();

    /* 6. Framebuffer Grafico Diretto Dark Glass */
    static uint32_t s_local_fb[1024 * 768];
    osify_framebuffer_t fb;
    osify_fb_init(&fb, 1024, 768, s_local_fb);

    /* Sfondo Blu Notte Profondo */
    osify_fb_clear(&fb, 0xFF0B101D);

    /* Barra Superiore macOS-Style (26px) */
    osify_fb_draw_rect(&fb, 0, 0, 1024, 26, 0xFF141C2E);
    osify_fb_draw_string(&fb, 16, 6, "OSify A.0", 0xFF06B6D4);
    osify_fb_draw_string(&fb, 120, 6, "File  Modifica  Visualizza  Sicurezza  Aiuto", 0xFFF8FAFC);
    osify_fb_draw_string(&fb, 920, 6, "12:00", 0xFF94A3B8);

    /* Card Dark Glass Centrale con Accento Neon */
    osify_fb_draw_squircle(&fb, 262, 184, 500, 20, 0xFF141C2E);
    osify_fb_draw_rect(&fb, 262, 184, 500, 4, 0xFF06B6D4); /* Neon Top Border */

    osify_fb_draw_string(&fb, 320, 220, "BENVENUTO IN OSIFY A.0", 0xFF06B6D4);
    osify_fb_draw_string(&fb, 290, 260, "Sistema Operativo Autonomo Universale", 0xFFF8FAFC);
    osify_fb_draw_string(&fb, 290, 290, "Architettura a Cover Nuda & Sicurezza Livello 0", 0xFF94A3B8);
    osify_fb_draw_string(&fb, 290, 340, "Premi un tasto per interagire con la Shell...", 0xFF8B5CF6);

    /* Loop Eventi Interattivo Bare-Metal */
    while (1) {
        osify_keyboard_poll();
        char k = osify_keyboard_get_key();
        if (k != 0) {
            /* Tasto digitato catturato nativamente dalla tastiera hardware */
            osify_fb_draw_string(&fb, 290, 400, "Ricevuto input hardware da tastiera PS/2!", 0xFF22C55E);
        }
    }
}
