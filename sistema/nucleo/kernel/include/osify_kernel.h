/* ==============================================================================
 * OSify Naked-Skin Micro-Core (sistema/nucleo/kernel/include/osify_kernel.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Architettura a "Cover Nuda": aderenza totale all'hardware, zero overhead,
 * autonomia assoluta e compatibilita universale su x86_64, i686 e ARM64.
 * ==============================================================================
 */

#ifndef OSIFY_KERNEL_H
#define OSIFY_KERNEL_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define OSIFY_OS_NAME       "OSify"
#define OSIFY_OS_CODENAME   "Resurrezione"
#define OSIFY_VERSION_MAJOR 1
#define OSIFY_VERSION_MINOR 5
#define OSIFY_VERSION_PATCH 0

/* Tipologie di Architettura Hardware Rilevate dall'Esoscheletro */
typedef enum {
    ARCH_UNKNOWN = 0,
    ARCH_X86_32,        /* 32-bit Vintage (Intel Atom, Pentium M, i686) */
    ARCH_X86_64,        /* 64-bit Moderno (Intel Core, AMD Ryzen, Threadripper) */
    ARCH_ARM64,         /* ARM64 & Apple Silicon (M1/M2/M3/M4, Neoverse, Cortex-A) */
    ARCH_RISCV64        /* RISC-V Future-Ready */
} osify_arch_t;

/* Profilo Hardware Adattivo Autonomo Generato all'Avvio */
typedef enum {
    PROFILE_VINTAGE_LITE = 1,   /* < 1 GB RAM, Monocore/Dualcore: footprint < 32MB, zRAM attiva */
    PROFILE_STANDARD_BALANCED,  /* 2-8 GB RAM: efficienza energetica, multitasking fluido */
    PROFILE_EXTREME_PERF        /* > 8 GB RAM, Multicore, GPU dedicata: latenza zero, AVX/NEON */
} osify_profile_t;

/* Sottosistemi di Esecuzione Binaria Universale */
typedef enum {
    SUBSYSTEM_OSIFY_NATIVE = 1, /* Formato proprietario .ify con manifesto e sandbox */
    SUBSYSTEM_POSIX_LINUX,      /* Compatibilita binaria ELF (syscall Linux tradotte a caldo) */
    SUBSYSTEM_WIN32_NT,         /* Compatibilita binaria PE (.exe Windows tradotti al silicio) */
    SUBSYSTEM_DARWIN_MACH_O     /* Compatibilita binaria Mach-O (macOS nativo su ARM/x86) */
} osify_subsystem_t;

/* Struttura del Framebuffer Grafico Diretto Dark Glass (Senza Server Grafici Esterni) */
typedef struct {
    uint32_t *buffer;           /* Puntatore lineare alla memoria video */
    uint32_t *back_buffer;      /* Double buffering per fluidita a 60/120 FPS senza tearing */
    uint32_t width;             /* Larghezza orizzontale in pixel */
    uint32_t height;            /* Altezza verticale in pixel */
    uint32_t pitch;             /* Byte per riga di scansione */
    uint8_t  bpp;               /* Profondita colore (tipicamente 32-bit ARGB) */
} osify_framebuffer_t;

/* Descrittore dell'Esoscheletro Hardware OSify */
typedef struct {
    osify_arch_t    arch;
    osify_profile_t profile;
    char            cpu_vendor[32];
    char            cpu_brand[64];
    uint32_t        cpu_cores;
    uint32_t        cpu_threads;
    uint64_t        ram_total_bytes;
    uint64_t        ram_free_bytes;
    bool            has_avx;
    bool            has_avx2;
    bool            has_neon;
    bool            has_hardware_aes;
    osify_framebuffer_t fb;
} osify_hardware_skin_t;

/* Prototipi Funzionali del Micro-Core */
void osify_kernel_early_boot(void *boot_info_ptr);
void osify_hardware_detect(osify_hardware_skin_t *skin);
void osify_adaptive_skin_init(osify_hardware_skin_t *skin);
void osify_fb_init(osify_framebuffer_t *fb, uint32_t width, uint32_t height, void *fb_addr);
void osify_fb_clear(osify_framebuffer_t *fb, uint32_t hex_color);
void osify_fb_draw_rect(osify_framebuffer_t *fb, int x, int y, int w, int h, uint32_t hex_color);
void osify_fb_draw_squircle(osify_framebuffer_t *fb, int x, int y, int size, int radius, uint32_t hex_color);
void osify_fb_swap_buffers(osify_framebuffer_t *fb);

/* Motore di Compatibilita Universale a Sottosistemi */
int osify_universal_exec(const char *path, osify_subsystem_t forced_subsystem);
int osify_syscall_dispatcher(uint32_t syscall_num, uint64_t arg1, uint64_t arg2, uint64_t arg3, osify_subsystem_t subsystem);

#endif /* OSIFY_KERNEL_H */
