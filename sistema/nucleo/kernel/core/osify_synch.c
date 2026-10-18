/* ==============================================================================
 * OSify Universal Synchronization Implementation (sistema/nucleo/kernel/core/osify_synch.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Implementazione della primitiva Superset WaitMux capace di soddisfare nativamente
 * WaitForMultipleObjects di Windows NT, kqueue/mach_port_set di macOS ed epoll di Linux.
 * ==============================================================================
 */

#include "../include/osify_synch.h"
#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

void osify_synch_init(osify_synch_hdr_t *hdr, osify_synch_type_t type, bool initial_state) {
    if (!hdr) return;
    hdr->type = type;
    hdr->signaled = initial_state;
    hdr->count = initial_state ? 1 : 0;
    hdr->wait_queue = NULL;
}

void osify_synch_signal(osify_synch_hdr_t *hdr) {
    if (!hdr) return;
    hdr->signaled = true;
    hdr->count++;
}

void osify_synch_reset(osify_synch_hdr_t *hdr) {
    if (!hdr) return;
    hdr->signaled = false;
    hdr->count = 0;
}

int32_t osify_wait_mux(osify_synch_hdr_t **objects, size_t count, uint32_t mode, uint64_t timeout_ns) {
    (void)timeout_ns;
    if (!objects || count == 0) return -1;

    if (mode == OSIFY_WAIT_ANY) {
        /* Restituisce il primo oggetto pronto */
        for (size_t i = 0; i < count; i++) {
            if (objects[i] && objects[i]->signaled) {
                /* Se e' un evento a consumo o semaforo, decrementa */
                if (objects[i]->type == OSIFY_SYNCH_SEMAPHORE && objects[i]->count > 0) {
                    objects[i]->count--;
                    if (objects[i]->count == 0) objects[i]->signaled = false;
                }
                return (int32_t)i;
            }
        }
        return -2; /* Nessun oggetto pronto (in polling / non bloccante) */
    } else if (mode == OSIFY_WAIT_ALL) {
        /* Verifica che TUTTI gli oggetti siano segnalati */
        for (size_t i = 0; i < count; i++) {
            if (!objects[i] || !objects[i]->signaled) {
                return -2; /* Almeno uno non e' pronto */
            }
        }
        return 0; /* Tutti gli oggetti sono pronti contemporaneamente */
    }

    return -1;
}
