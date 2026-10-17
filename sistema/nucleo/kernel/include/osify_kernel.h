/* ==============================================================================
 * OSify Naked-Skin Micro-Core (sistema/nucleo/kernel/include/osify_kernel.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Architettura a "Cover Nuda" & Piattaforma di Compatibilita Universale al Silicio.
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

#define OSIFY_PAGE_SIZE     4096ULL
#define OSIFY_MAX_HANDLES   1024

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

/* Permessi Memoria Virtuale W^X */
#define PAGE_PERM_READ    (1 << 0)
#define PAGE_PERM_WRITE   (1 << 1)
#define PAGE_PERM_EXEC    (1 << 2)
#define PAGE_PERM_USER    (1 << 3)

/* Sicurezza Livello 0: Capability Tokens (Stile macOS SIP & Seatbelt Sandbox) */
typedef struct {
    uint32_t process_id;
    bool can_access_network;
    bool can_access_raw_disk;
    bool can_write_system_tree; /* Protezione SIP su /Sistema */
    bool is_sandboxed;          /* Seatbelt attivo */
} osify_security_token_t;

/* Descrittore Unificato File / Handle */
typedef struct {
    int      id;
    bool     is_open;
    uint32_t flags;
    uint64_t cursor;
    char     path[256];
} osify_handle_t;

/* Struttura del Framebuffer Grafico Diretto Dark Glass */
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

/* --- Inizializzazione Core & Hardware --- */
void osify_kernel_early_boot(void *boot_info_ptr);
void osify_hardware_detect(osify_hardware_skin_t *skin);
void osify_adaptive_skin_init(osify_hardware_skin_t *skin);

/* --- Gestione Memoria a 4 Livelli (PMM & VMM W^X) --- */
void osify_pmm_init(uint64_t total_memory_bytes);
void *osify_pmm_alloc_page(void);
void osify_pmm_free_page(void *page_ptr);
int osify_vmm_map_page(uint64_t virt_addr, uint64_t phys_addr, uint32_t perms);
bool osify_vmm_validate_wx(uint32_t perms);

/* --- Sicurezza Livello 0 & Seatbelt Sandbox (Stile macOS SIP) --- */
void osify_sec_init(void);
bool osify_sec_check_system_write(const char *path, const osify_security_token_t *token);
bool osify_sec_enforce_seatbelt(const osify_security_token_t *token, uint32_t requested_action);
osify_security_token_t osify_sec_create_token(uint32_t pid, bool sandboxed);

/* --- Unificatore Percorsi Universale (Windows C:\ <-> Linux / <-> OSify) --- */
int osify_path_unify(const char *input_path, char *output_unified, size_t max_len);

/* --- Motore Tipografico & Framebuffer Dark Glass Nativo --- */
void osify_fb_init(osify_framebuffer_t *fb, uint32_t width, uint32_t height, void *fb_addr);
void osify_fb_clear(osify_framebuffer_t *fb, uint32_t hex_color);
void osify_fb_draw_rect(osify_framebuffer_t *fb, int x, int y, int w, int h, uint32_t hex_color);
void osify_fb_draw_squircle(osify_framebuffer_t *fb, int x, int y, int size, int radius, uint32_t hex_color);
void osify_fb_draw_char(osify_framebuffer_t *fb, int x, int y, char c, uint32_t fg_color);
void osify_fb_draw_string(osify_framebuffer_t *fb, int x, int y, const char *str, uint32_t fg_color);
void osify_fb_swap_buffers(osify_framebuffer_t *fb);

/* --- Caricatore Binari Reale (ELF, PE, Mach-O, .ify) --- */
typedef struct {
    osify_subsystem_t subsystem;
    uint64_t entry_point;
    uint64_t load_base;
    uint64_t size_in_memory;
    bool     is_valid;
} osify_loaded_binary_t;

osify_subsystem_t osify_detect_binary_format(const void *header_bytes, size_t len);
osify_loaded_binary_t osify_binary_load(const void *file_buffer, size_t file_len);

/* --- Dispatcher Syscall Universale & Calling Convention Thunk --- */
int osify_universal_exec(const char *path, osify_subsystem_t forced_subsystem);
int osify_syscall_dispatcher(uint32_t syscall_num, uint64_t arg1, uint64_t arg2, uint64_t arg3, osify_subsystem_t subsystem);

#endif /* OSIFY_KERNEL_H */
