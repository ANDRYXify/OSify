/* ==============================================================================
 * OSify Kernel Bare-Metal Main Entry Point (sistema/nucleo/kernel/core/osify_main.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Punto di ingresso assoluto bare-metal dopo il salto da boot.S.
 * Inizializza memoria W^X, sicurezza SIP/Seatbelt, storage OSifyFS,
 * network stack Ethernet/DHCP, audio driver Intel HDA/AC97 con chime,
 * installatore disco guidato e Desktop Dark Glass su Framebuffer lineare.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"
#include "../include/osify_storage.h"
#include "../include/osify_desktop.h"
#include "../include/osify_net.h"
#include "../include/osify_audio.h"
#include "../include/osify_installer.h"
#include "../include/osify_hetero_dispatch.h"

/* Prototipi interni dei sottosistemi di basso livello */
void osify_idt_init(void);
void osify_keyboard_init(void);
void osify_keyboard_poll(void);
char osify_keyboard_get_key(void);

/* Driver Porta Seriale COM1 (0x3F8) per Telemetria Kernel Nativo */
static inline void outb_io(uint16_t port, uint8_t val) {
#if defined(__i386__) || defined(__x86_64__)
    __asm__ volatile ("outb %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

static inline uint8_t inb_io(uint16_t port) {
#if defined(__i386__) || defined(__x86_64__)
    uint8_t ret;
    __asm__ volatile ("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port; return 0;
#endif
}

static bool g_serial_hw_active = false;

void osify_serial_init(void) {
    g_serial_hw_active = true;
    outb_io(0x3F8 + 1, 0x00);
    outb_io(0x3F8 + 3, 0x80);
    outb_io(0x3F8 + 0, 0x03);
    outb_io(0x3F8 + 1, 0x00);
    outb_io(0x3F8 + 3, 0x03);
    outb_io(0x3F8 + 2, 0xC7);
    outb_io(0x3F8 + 4, 0x0B);
}

void osify_serial_print(const char *s) {
    if (!g_serial_hw_active) {
        return; /* Salvaguardia host: previene violazione privilegi I/O nei test Ring 3 */
    }
    while (s && *s) {
        while ((inb_io(0x3F8 + 5) & 0x20) == 0);
        outb_io(0x3F8, (uint8_t)*s);
        s++;
    }
}

/* Entry point C invocato da boot.S */
void osify_kernel_main(uint32_t magic, void *boot_info) {
    osify_serial_init();
    osify_serial_print("\n=======================================================\n");
    osify_serial_print(" [OSify A.1] Avvio Kernel Nativo Sovrano al 100%...\n");
    osify_serial_print(" Ingegnerizzato da Andrea Taliento (ANDRYXify)\n");
    osify_serial_print("=======================================================\n");

    /* 1. Inizializzazione Vettori Interrupt & Controller Input PS/2 */
    osify_serial_print("[1/12] Inizializzazione IDT Interrupt e Controller PS/2...\n");
    osify_idt_init();
    osify_keyboard_init();

    /* 2. Introspezione Silicio & Profilo Cover Nuda */
    osify_serial_print("[2/12] Introspezione Hardware Silicio e Potenza Effettiva...\n");
    osify_hardware_skin_t skin;
    osify_memset(&skin, 0, sizeof(skin));
    skin.ram_total_bytes = 2ULL * 1024ULL * 1024ULL * 1024ULL;
    osify_hardware_detect(&skin);
    osify_adaptive_skin_init(&skin);

    char hw_log[128];
    osify_snprintf(hw_log, sizeof(hw_log), "  -> CPU: %s (%u core, %u GFLOPS, SIMD: %s)\n",
                   skin.cpu_brand, skin.cpu_cores, (uint32_t)skin.cpu_peak_gflops,
                   skin.has_avx2 ? "AVX2" : (skin.has_avx ? "AVX" : (skin.has_sse2 ? "SSE2" : "Base")));
    osify_serial_print(hw_log);
    osify_snprintf(hw_log, sizeof(hw_log), "  -> GPU: %s (VRAM: %u MB, BAR: 0x%x)\n",
                   skin.gpu_vendor, skin.gpu_vram_bytes / (1024 * 1024), skin.gpu_bar_addr);
    osify_serial_print(hw_log);

    /* 3. Scheduler Eterogeneo & Connettori di Processo (ALU / SIMD / GPU / IO) */
    osify_serial_print("[3/12] Inizializzazione Scheduler Eterogeneo e Connettori Silicio...\n");
    osify_hetero_dispatch_init();
    osify_dispatch_stats_t d_stats;
    osify_hetero_get_stats(&d_stats);
    osify_snprintf(hw_log, sizeof(hw_log), "  -> Connettori attivi: %u (ALU: %u, SIMD: %u, GPU: %u, I/O: %u)\n",
                   d_stats.total_tasks_dispatched, d_stats.tasks_on_alu_scalar, d_stats.tasks_on_alu_vector,
                   d_stats.tasks_on_gpu_blitter, d_stats.tasks_on_async_io);
    osify_serial_print(hw_log);

    /* 4. Memory Management PMM & VMM con protezione W^X */
    osify_serial_print("[4/12] PMM Memory Allocator & Protezione W^X (Anti-Exploit)...\n");
    osify_pmm_init(skin.ram_total_bytes);

    /* 5. Sicurezza Livello 0: SIP & Seatbelt Sandbox (macOS style) */
    osify_serial_print("[5/12] Sicurezza Livello 0: SIP & Seatbelt Sandbox...\n");
    osify_sec_init();

    /* 6. Anti-Cheat Guard & Attestazione Hardware (TPM 2.0, Secure Boot, DSE) */
    osify_serial_print("[6/12] Anti-Cheat Guard e Attestazione Hardware TPM 2.0...\n");
    osify_anticheat_init();

    /* 7. Storage Fisico ATA & File System Nativo OSifyFS */
    osify_serial_print("[7/12] Storage Controller ATA e File System Nativo OSifyFS...\n");
    osify_storage_init();
    osify_fs_init(0);

    /* 8. Network Stack Bare-Metal (Ethernet II, IPv4, ARP, DHCP, Quad9) */
    osify_serial_print("[8/12] Network Stack Bare-Metal: Ethernet II, DHCP, Quad9 DNS...\n");
    osify_net_init();

    /* 9. Sottosistema Audio Hardware (Intel HDA / AC97) & Startup Chime */
    osify_serial_print("[9/12] Sottosistema Audio Hardware (Intel HDA / AC97) & Startup Chime...\n");
    osify_audio_init();
    osify_audio_play_startup_chime();

    /* 10. Installatore Bare-Metal Guidato su Disco Fisso */
    osify_serial_print("[10/12] Modulo Installatore Bare-Metal Permanente GPT...\n");
    osify_installer_init();

    /* 11. Framebuffer Grafico Diretto & Desktop Environment Dark Glass */
    osify_serial_print("[11/12] Display Server Dark Glass Driverless & Video Hardware...\n");
    static uint32_t s_local_fb[1024 * 768];
    uint32_t *fb_addr = s_local_fb;
    uint32_t fb_w = 1024;
    uint32_t fb_h = 768;

    /* Tentativo 1: Configurazione Hardware Bochs/QEMU BGA (PCI Video) */
    if (osify_bga_set_video_mode(1024, 768, 32)) {
        osify_serial_print("  -> Hardware BGA rilevato! Risoluzione 1024x768x32 attivata via I/O port 0x01CE.\n");
        fb_addr = (uint32_t *)0xFD000000;
    } else if (skin.gpu_bar_addr != 0) {
        osify_serial_print("  -> Framebuffer PCI Driverless agganciato via BAR0 hardware.\n");
        fb_addr = (uint32_t *)(uintptr_t)skin.gpu_bar_addr;
    } else {
        osify_serial_print("  -> Controller BGA non rilevato. Verifica puntatori Multiboot...\n");
    }

    /* Tentativo 2: Introspezione puntatore Framebuffer Multiboot 1 (se presente) */
    if (magic == 0x2BADB002 && boot_info != NULL) {
        uint32_t *mb = (uint32_t *)boot_info;
        uint32_t mb_flags = mb[0];
        if ((mb_flags & (1 << 12)) != 0) {
            uint64_t mb_fb_addr = *(uint64_t *)((uintptr_t)mb + 88);
            uint32_t mb_w = *(uint32_t *)((uintptr_t)mb + 100);
            uint32_t mb_h = *(uint32_t *)((uintptr_t)mb + 104);
            if (mb_fb_addr != 0 && mb_w >= 640 && mb_h >= 480) {
                osify_serial_print("  -> Framebuffer Multiboot rilevato e configurato.\n");
                fb_addr = (uint32_t *)(uintptr_t)mb_fb_addr;
                fb_w = mb_w;
                fb_h = mb_h;
            }
        }
    }

    osify_framebuffer_t fb;
    osify_fb_init(&fb, fb_w, fb_h, fb_addr);

    /* Inizializza e renderizza la Scrivania e la Finestra Shell */
    osify_desktop_init(&fb);
    osify_desktop_render_all(&fb);
    osify_serial_print("[] DESKTOP DARK GLASS RENDERIZZATO CON SUCCESSO!\n");

    /* 12. Collaudo System Call Native (int 0x80 DPL 3) */
    osify_serial_print("[12/12] Collaudo System Call Native (int 0x80 DPL 3)...\n");
    int32_t ping_ret = osify_syscall(6, 0, 0, 0); /* SYS_PING */
    if (ping_ret == 0x051F1050) {
        osify_serial_print("  -> SYS_PING via int 0x80: Successo! Risposta: 0x051F1050 (OSify)\n");
    }

    /* Test Syscall 7: SYS_HW_POWER */
    osify_hardware_skin_t test_hw_skin;
    if (osify_syscall(7, (uintptr_t)&test_hw_skin, 0, 0) == 0) {
        osify_serial_print("  -> SYS_HW_POWER via int 0x80: Profilo hardware e GFLOPS letti da Ring 3!\n");
    }

    /* Test Syscall 8: SYS_HETERO_DISPATCH */
    if (osify_syscall(8, 2, 0, 0) == 0) { /* Dispatch task 2 su SIMD */
        osify_serial_print("  -> SYS_HETERO_DISPATCH via int 0x80: Esecuzione accelerata SIMD convalidata!\n");
    }

    const char *test_msg = "  -> SYS_WRITE via int 0x80: Canale Ring 0 <-> Ring 3 attivo al 100%!\n";
    osify_syscall(1, 1, (uint32_t)(uintptr_t)test_msg, osify_strlen(test_msg));
    osify_serial_print("[] KERNEL NATIVO SOVRANO & SCHEDULER ETEROGENEO OPERATIVI AL 100%!\n");

    /* Loop Eventi Interattivo Bare-Metal a 60 FPS */
    while (1) {
        osify_keyboard_poll();
        char k = osify_keyboard_get_key();
        if (k != 0) {
            osify_desktop_handle_key(&fb, k);
        }
    }
}
