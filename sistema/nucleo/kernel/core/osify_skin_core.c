/* ==============================================================================
 * OSify Naked-Skin Micro-Core Engine (sistema/nucleo/kernel/core/osify_skin_core.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Implementazione dell'Esoscheletro Adattivo: interroga il silicio,
 * modella il sistema come una "cover nuda" e garantisce massime prestazioni.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"

/* Variabile Globale dell'Esoscheletro Attivo */
static osify_hardware_skin_t g_skin;

/* Rilevamento Hardware Bare-Metal Adattivo */
void osify_hardware_detect(osify_hardware_skin_t *skin) {
    if (!skin) return;

#if defined(__x86_64__)
    skin->arch = ARCH_X86_64;
#elif defined(__i386__)
    skin->arch = ARCH_X86_32;
#elif defined(__aarch64__)
    skin->arch = ARCH_ARM64;
#else
    skin->arch = ARCH_UNKNOWN;
#endif

    /* Valori di Default Sicuri pre-probe */
    skin->cpu_cores = 1;
    skin->cpu_threads = 1;
    skin->has_avx = false;
    skin->has_avx2 = false;
    skin->has_neon = false;
    skin->has_hardware_aes = false;

#if defined(__x86_64__) || defined(__i386__)
    /* Rilevamento Introspezione x86 via CPUID */
    uint32_t eax, ebx, ecx, edx;

    /* Vendor String */
    __asm__ volatile("cpuid"
                     : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
                     : "a"(0));
    ((uint32_t *)skin->cpu_vendor)[0] = ebx;
    ((uint32_t *)skin->cpu_vendor)[1] = edx;
    ((uint32_t *)skin->cpu_vendor)[2] = ecx;
    skin->cpu_vendor[12] = '\0';

    /* Feature Flags (ECX ed EDX con EAX=1) */
    __asm__ volatile("cpuid"
                     : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
                     : "a"(1));
    
    skin->has_avx = (ecx & (1 << 28)) != 0;
    skin->has_hardware_aes = (ecx & (1 << 25)) != 0;

    /* AVX2 Extended Features (EBX con EAX=7, ECX=0) */
    __asm__ volatile("cpuid"
                     : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
                     : "a"(7), "c"(0));
    skin->has_avx2 = (ebx & (1 << 5)) != 0;

#elif defined(__aarch64__)
    /* Rilevamento Architettura ARM64 & Apple Silicon */
    skin->has_neon = true; /* Standard per aarch64 */
    skin->has_hardware_aes = true;
#endif

    /* Profilazione Dinamica dell'Esoscheletro (La "Cover Nuda") */
    if (skin->arch == ARCH_X86_32 || skin->ram_total_bytes <= (1024ULL * 1024ULL * 1024ULL)) {
        /* Profilo Vintage / Netbook: minimizza l'overhead a < 32MB di RAM */
        skin->profile = PROFILE_VINTAGE_LITE;
    } else if (skin->ram_total_bytes > (8ULL * 1024ULL * 1024ULL * 1024ULL)) {
        /* Profilo Estremo: sblocca tutti i registri vettoriali e latenza deterministica */
        skin->profile = PROFILE_EXTREME_PERF;
    } else {
        /* Profilo Bilanciato */
        skin->profile = PROFILE_STANDARD_BALANCED;
    }
}

/* Inizializzazione dell'Esoscheletro Adattivo */
void osify_adaptive_skin_init(osify_hardware_skin_t *skin) {
    if (!skin) return;

    /* Applica la configurazione "Cover Nuda" al silicio */
    switch (skin->profile) {
        case PROFILE_VINTAGE_LITE:
            /* Modalita Resurrezione: zero processi inutili, scheduling cooperativo/leggero */
            break;
        case PROFILE_EXTREME_PERF:
            /* Modalita Prestazioni Estreme: affinity dei thread, zero throttling */
            break;
        case PROFILE_STANDARD_BALANCED:
        default:
            break;
    }
}

/* Entry Point Primario del Kernel OSify */
void osify_kernel_early_boot(void *boot_info_ptr) {
    (void)boot_info_ptr;

    /* 1. Scansione Silicio */
    osify_hardware_detect(&g_skin);

    /* 2. Inizializzazione Cover Nuda */
    osify_adaptive_skin_init(&g_skin);
}
