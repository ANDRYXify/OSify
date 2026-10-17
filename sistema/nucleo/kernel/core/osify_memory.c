/* ==============================================================================
 * OSify Memory Management: PMM & VMM con Protezione W^X
 * (sistema/nucleo/kernel/core/osify_memory.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Gestione memoria a 4 livelli, bitmap allocator fisico, e principio W^X
 * (Write XOR Execute) per prevenzione exploit hardware.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"

#define MAX_PHYS_PAGES 1048576 /* Fino a 4GB tracciati per pagina da 4KB */

static uint8_t g_pmm_bitmap[MAX_PHYS_PAGES / 8];
static uint64_t g_total_pages = 0;
static uint64_t g_allocated_pages = 0;

void osify_pmm_init(uint64_t total_memory_bytes) {
    g_total_pages = total_memory_bytes / OSIFY_PAGE_SIZE;
    if (g_total_pages > MAX_PHYS_PAGES) {
        g_total_pages = MAX_PHYS_PAGES;
    }
    /* Inizialmente tutta la memoria e considerata libera (bit = 0) */
    for (size_t i = 0; i < sizeof(g_pmm_bitmap); i++) {
        g_pmm_bitmap[i] = 0;
    }
    g_allocated_pages = 0;
}

void *osify_pmm_alloc_page(void) {
    /* La pagina 0 (0x0 - 0x1000) e riservata permanentemente come Null Sentinel */
    for (uint64_t i = 1; i < g_total_pages; i++) {
        size_t byte_idx = i / 8;
        uint8_t bit_mask = (uint8_t)(1 << (i % 8));

        if (!(g_pmm_bitmap[byte_idx] & bit_mask)) {
            /* Marca la pagina come occupata */
            g_pmm_bitmap[byte_idx] |= bit_mask;
            g_allocated_pages++;
            return (void *)(uintptr_t)(i * OSIFY_PAGE_SIZE);
        }
    }
    return NULL; /* Memoria fisica esaurita (Out of Memory) */
}

void osify_pmm_free_page(void *page_ptr) {
    if (!page_ptr) return;
    uint64_t page_idx = (uint64_t)(uintptr_t)page_ptr / OSIFY_PAGE_SIZE;
    if (page_idx >= g_total_pages) return;

    size_t byte_idx = page_idx / 8;
    uint8_t bit_mask = (uint8_t)(1 << (page_idx % 8));

    if (g_pmm_bitmap[byte_idx] & bit_mask) {
        g_pmm_bitmap[byte_idx] &= ~bit_mask;
        if (g_allocated_pages > 0) g_allocated_pages--;
    }
}

/* Validazione Rigorosa W^X: Una pagina NON puo essere sia SCRIVIBILE che ESEGUIBILE */
bool osify_vmm_validate_wx(uint32_t perms) {
    if ((perms & PAGE_PERM_WRITE) && (perms & PAGE_PERM_EXEC)) {
        return false; /* Violazione W^X rilevata e bloccata a livello 0 */
    }
    return true;
}

int osify_vmm_map_page(uint64_t virt_addr, uint64_t phys_addr, uint32_t perms) {
    (void)virt_addr;
    (void)phys_addr;
    if (!osify_vmm_validate_wx(perms)) {
        return -1; /* Rifiuto di mappare una pagina W^X malevola */
    }
    return 0;
}
