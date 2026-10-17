/* ==============================================================================
 * OSify Kernel Bare-Metal Main Entry Point (sistema/nucleo/kernel/core/osify_main.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Punto di ingresso assoluto bare-metal dopo il salto da boot.S.
 * Inizializza memoria W^X, sicurezza SIP/Seatbelt, storage OSifyFS,
 * e avvia il Desktop Environment nativo Dark Glass con Shell interattiva.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"
#include "../include/osify_storage.h"
#include "../include/osify_desktop.h"

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
    skin.ram_total_bytes = 2ULL * 1024ULL * 1024ULL * 1024ULL;
    osify_hardware_detect(&skin);
    osify_adaptive_skin_init(&skin);

    /* 3. Memory Management PMM & VMM con W^X */
    osify_pmm_init(skin.ram_total_bytes);

    /* 4. Sicurezza Livello 0: SIP & Seatbelt Sandbox (macOS style) */
    osify_sec_init();

    /* 5. Anti-Cheat Guard & Attestazione Hardware (TPM 2.0, Secure Boot) */
    osify_anticheat_init();

    /* 6. Storage Fisico & File System Nativo OSifyFS */
    osify_storage_init();
    osify_fs_init(0);

    /* 7. Framebuffer Grafico Diretto & Desktop Environment Dark Glass */
    static uint32_t s_local_fb[1024 * 768];
    osify_framebuffer_t fb;
    osify_fb_init(&fb, 1024, 768, s_local_fb);

    /* Inizializza e renderizza la Scrivania e la Finestra Shell */
    osify_desktop_init(&fb);
    osify_desktop_render_all(&fb);

    /* 8. Loop Eventi Interattivo Bare-Metal a 60 FPS */
    while (1) {
        osify_keyboard_poll();
        char k = osify_keyboard_get_key();
        if (k != 0) {
            osify_desktop_handle_key(&fb, k);
        }
    }
}
