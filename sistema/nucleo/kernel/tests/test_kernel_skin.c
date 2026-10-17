/* ==============================================================================
 * Test Unitario del Kernel Nativo OSify (sistema/nucleo/kernel/tests/test_kernel_skin.c)
 * ==============================================================================
 * Verifica la Cover Nuda, l'adattabilita hardware, il Framebuffer Dark Glass
 * e il ponte di compatibilita universale a caldo (.ify, ELF, PE, Mach-O).
 * ==============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../include/osify_kernel.h"

/* Dichiarazione helper presente in osify_universal_bridge.c */
osify_subsystem_t osify_detect_binary_format(const void *header_bytes, size_t len);

int main(void) {
    printf("[+] Inizio collaudo del Kernel Nativo OSify (Naked-Skin Architecture)...\n");

    /* 1. Test Introspezione e Cover Nuda */
    osify_hardware_skin_t skin;
    memset(&skin, 0, sizeof(skin));
    skin.ram_total_bytes = 16ULL * 1024ULL * 1024ULL * 1024ULL; /* 16 GB simulati */
    osify_hardware_detect(&skin);
    osify_adaptive_skin_init(&skin);

    printf("[+] Architettura rilevata: %d (1=x86_32, 2=x86_64, 3=ARM64)\n", skin.arch);
    printf("[+] Profilo Esoscheletro applicato: %d (1=Vintage, 2=Bilanciato, 3=Estremo)\n", skin.profile);
    assert(skin.arch != ARCH_UNKNOWN);
    assert(skin.profile == PROFILE_EXTREME_PERF);

    /* 2. Test Profilo Vintage (<1GB RAM) */
    osify_hardware_skin_t vintage_skin;
    memset(&vintage_skin, 0, sizeof(vintage_skin));
    vintage_skin.ram_total_bytes = 512ULL * 1024ULL * 1024ULL; /* 512 MB Netbook */
    osify_hardware_detect(&vintage_skin);
    assert(vintage_skin.profile == PROFILE_VINTAGE_LITE);
    printf("[+] Profilo Vintage Netbook (<1GB) adattato a memoria ultra-compatta: OK\n");

    /* 3. Test Motore Grafico Diretto Dark Glass */
    uint32_t fake_fb[800 * 600];
    osify_framebuffer_t fb;
    osify_fb_init(&fb, 800, 600, fake_fb);
    assert(fb.width == 800 && fb.height == 600);

    osify_fb_clear(&fb, 0xFF0B101D);
    assert(fake_fb[0] == 0xFF0B101D);
    assert(fake_fb[799 + 599 * 800] == 0xFF0B101D);

    /* Disegno Card Dark Glass e Squircle */
    osify_fb_draw_rect(&fb, 100, 100, 200, 150, 0xFF141C2E);
    assert(fake_fb[100 + 100 * 800] == 0xFF141C2E);

    osify_fb_draw_squircle(&fb, 350, 200, 64, 16, 0xFF06B6D4);
    assert(fake_fb[366 + 216 * 800] == 0xFF06B6D4);
    printf("[+] Motore Grafico Dark Glass Nativo (Framebuffer Diretto a 32bpp): OK\n");

    /* 4. Test Riconoscimento Magic Formati Binari Universali */
    uint8_t elf_header[4]   = {0x7F, 'E', 'L', 'F'};
    uint8_t pe_header[4]    = {'M', 'Z', 0x90, 0x00};
    uint8_t macho_header[4] = {0xCE, 0xFA, 0xED, 0xFE}; /* Mach-O little-endian 32/64 */
    uint8_t ify_header[4]   = {'I', 'F', 'Y', 0x00};

    assert(osify_detect_binary_format(ify_header, 4) == SUBSYSTEM_OSIFY_NATIVE);
    assert(osify_detect_binary_format(elf_header, 4) == SUBSYSTEM_POSIX_LINUX);
    assert(osify_detect_binary_format(pe_header, 4) == SUBSYSTEM_WIN32_NT);
    assert(osify_detect_binary_format(macho_header, 4) == SUBSYSTEM_DARWIN_MACH_O);
    printf("[+] Riconoscimento Formati Universali (.ify, ELF Linux, PE Windows, Mach-O): OK\n");

    /* 5. Test Syscall Dispatcher */
    int res_native = osify_syscall_dispatcher(1, 0, 0, 0, SUBSYSTEM_OSIFY_NATIVE);
    assert(res_native == 0);

    int res_linux = osify_syscall_dispatcher(1, 1, 0, 0, SUBSYSTEM_POSIX_LINUX);
    assert(res_linux == 0);

    int res_win = osify_syscall_dispatcher(0x10, 0, 0, 0, SUBSYSTEM_WIN32_NT);
    assert(res_win == 0);
    printf("[+] Dispatcher Syscall Universale ad alta velocita: OK\n");

    printf("[+] TUTTI I TEST DEL KERNEL NATIVO OSIFY SUPERATI CON SUCCESSO AL 100%%!\n");
    return 0;
}
