/* ==============================================================================
 * OSify Hardware Virtualization Contract (Ring -1 / EL2 / HS-Mode)
 * (sistema/nucleo/arch/arch_hv.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Legge 3: Nessun driver Ring 0 esterno (.sys Anti-Cheat, .kext) puo toccare
 * il Ring 0 nativo. Tutto il codice esterno elevato vive in una Cella Aegis via SLAT.
 * ==============================================================================
 */

#ifndef OSIFY_ARCH_HV_H
#define OSIFY_ARCH_HV_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Descrittore Cella di Contenimento Hardware (Opaque) */
typedef struct osify_cell osify_cell_t;

/* Descrittore vCPU Ospite (Opaque) */
typedef struct osify_vcpu osify_vcpu_t;

/* Cause di Uscita dalla Virtualizzazione (VM-Exit / Trap Hypervisor) */
typedef enum {
    OSIFY_VMEXIT_UNKNOWN = 0,
    OSIFY_VMEXIT_SLAT_VIOLATION,    /* EPT / Stage-2: tentato accesso fuori dalla memoria consentita */
    OSIFY_VMEXIT_IO_PORT,           /* I/O Port trap (intercettazione accessi hardware non autorizzati) */
    OSIFY_VMEXIT_MSR_READ,          /* Tentativo lettura MSR di controllo */
    OSIFY_VMEXIT_MSR_WRITE,         /* Tentativo scrittura MSR di controllo */
    OSIFY_VMEXIT_CR_ACCESS,         /* Accesso ai registri CR0/CR3/CR4 */
    OSIFY_VMEXIT_HYPERCALL,         /* Chiamata sicura da Cella ad Host (vmcall / hvc) */
    OSIFY_VMEXIT_INTERRUPT,         /* Interruzione fisica per l'host */
    OSIFY_VMEXIT_HALT               /* Istruzione HLT / WFI eseguita nel guest */
} osify_vmexit_reason_t;

/* Informazioni di Dettaglio sul VM-Exit */
typedef struct {
    osify_vmexit_reason_t reason;
    uintptr_t             fault_gpa;    /* Guest Physical Address scatenante la violazione SLAT */
    uintptr_t             fault_gva;    /* Guest Virtual Address */
    uint32_t              port;         /* Porta I/O coinvolta (se IO_PORT) */
    uint32_t              msr;          /* MSR coinvolto (se MSR_READ/WRITE) */
    uint64_t              val;          /* Valore scambiato */
    bool                  is_write;     /* true se operazione di scrittura */
} osify_vmexit_t;

/* Rilevamento Hardware Support (Intel VT-x, AMD-V, ARM EL2 Stage-2, RISC-V H) */
bool arch_hv_supported(void);

/* Gestione Ciclo di Vita della Cella Aegis */
osify_cell_t *arch_hv_cell_create(void);
void          arch_hv_cell_destroy(osify_cell_t *cell);

/* Mappatura SLAT (Second-Level Address Translation: EPT / NPT / Stage-2 MMU) */
/* Isola fisicamente la cella: il guest puo accedere solo alle pagine qui esplicitamente mappate */
int arch_hv_slat_map(osify_cell_t *cell, uintptr_t gpa, uintptr_t hpa, size_t len, unsigned flags);
int arch_hv_slat_unmap(osify_cell_t *cell, uintptr_t gpa, size_t len);

/* Gestione vCPU Ospite all'interno della Cella */
osify_vcpu_t *arch_hv_vcpu_create(osify_cell_t *cell, unsigned vcpu_id);
void          arch_hv_vcpu_destroy(osify_vcpu_t *vcpu);
void          arch_hv_vcpu_set_entry(osify_vcpu_t *vcpu, uintptr_t rip, uintptr_t rsp, uintptr_t cr3);

/* Esecuzione vCPU fino al successivo VM-Exit */
int arch_hv_vcpu_run(osify_vcpu_t *vcpu, osify_vmexit_t *exit_info);

#endif /* OSIFY_ARCH_HV_H */
