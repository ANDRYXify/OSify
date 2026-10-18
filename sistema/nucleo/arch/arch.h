/* ==============================================================================
 * OSify Multi-Architecture Hardware Contract (Ring 0 / EL1 / S-Mode)
 * (sistema/nucleo/arch/arch.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Legge 1: Nessun registro di controllo CPU, istruzione assembly o trap hardware
 * puo comparire fuori da sistema/nucleo/arch/<arch>/.
 * ==============================================================================
 */

#ifndef OSIFY_ARCH_H
#define OSIFY_ARCH_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Struttura Mappa Memoria Fisica */
typedef struct osify_mem_range {
    uintptr_t base;
    size_t    size;
    uint32_t  type; /* 1 = Usabile, 2 = Riservata, 3 = ACPI, 4 = NVS */
} osify_mem_range_t;

/* Parametri Framebuffer Hardware Iniziale */
typedef struct osify_fb_contract {
    uintptr_t phys_addr;
    uint32_t  width;
    uint32_t  height;
    uint32_t  pitch;
    uint8_t   bpp;
} osify_fb_contract_t;

/* Informazioni di Bootstrap passate al Kernel Neutro */
typedef struct osify_boot_info {
    osify_mem_range_t   *mem_map;
    size_t               mem_count;
    osify_fb_contract_t  fb;
    void                *acpi_rsdp;
    void                *dtb;
    const char          *cmdline;
    void                *initrd;
    size_t               initrd_size;
} osify_boot_info_t;

/* Descrittore Spazio di Indirizzamento Virtuale (Opaque per il Kernel Neutro) */
typedef struct osify_aspace osify_aspace_t;

/* Descrittore Contesto Thread/CPU (Opaque) */
typedef struct osify_ctx osify_ctx_t;

/* Flag Permessi Paginazione MMU con Imposizione W^X */
#define OSIFY_MAP_R       (1u << 0)
#define OSIFY_MAP_W       (1u << 1)
#define OSIFY_MAP_X       (1u << 2)
#define OSIFY_MAP_USER    (1u << 3)
#define OSIFY_MAP_NOCACHE (1u << 4)
#define OSIFY_MAP_WC      (1u << 5) /* Write-Combining per VRAM / Framebuffer */

/* Inizializzazione Early Hardware & Topologia CPU */
void     arch_early_init(osify_boot_info_t *bi);
unsigned arch_cpu_count(void);
unsigned arch_cpu_id(void);
void     arch_cpu_start(unsigned id, void (*entry)(void));
uint64_t arch_time_ns(void);
int      arch_entropy(void *buf, size_t len); /* RDRAND/RDSEED, RNDR, Zkr */

/* Gestione MMU Multi-Granularita con rispetto rigido W^X */
osify_aspace_t *arch_mmu_create(void);
void            arch_mmu_destroy(osify_aspace_t *as);
/* Se (flags & OSIFY_MAP_W) && (flags & OSIFY_MAP_X) -> ritorna -1 (Violazione W^X) */
int             arch_mmu_map(osify_aspace_t *as, uintptr_t va, uintptr_t pa, size_t len, unsigned flags);
void            arch_mmu_unmap(osify_aspace_t *as, uintptr_t va, size_t len);
void            arch_mmu_switch(osify_aspace_t *as);

/* Context Switch Poliglotta (Doppio TLS per NT / Darwin / Linux / OSify) */
void arch_ctx_init(osify_ctx_t *c, void (*entry)(void *), void *arg, void *kstack_top);
void arch_ctx_switch(osify_ctx_t *from, osify_ctx_t *to);
void arch_ctx_set_tls(osify_ctx_t *c, uintptr_t tls_primary, uintptr_t tls_alt);
void arch_enter_user(uintptr_t entry, uintptr_t user_stack, uintptr_t abi_arg);

/* Accesso Protetto Memoria Utente (SMEP/SMAP, PAN/PXN, SUM) */
int arch_copy_from_user(void *dst, const void *usrc, size_t n);
int arch_copy_to_user(void *udst, const void *src, size_t n);

#endif /* OSIFY_ARCH_H */
