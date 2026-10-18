/* ==============================================================================
 * OSify Universal Synchronization Engine: WaitMux (sistema/nucleo/include/osify_synch.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Legge 2: Primitiva Superset universale capace di soddisfare nativamente
 * WaitForMultipleObjects (NT), mach_port_set/kqueue (XNU) ed epoll/futex (Linux).
 * ==============================================================================
 */

#ifndef OSIFY_SYNCH_H
#define OSIFY_SYNCH_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Tipologie di Oggetti Kernel Sincronizzabili */
typedef enum {
    OSIFY_SYNCH_EVENT = 1,      /* Evento binario con reset manuale o automatico */
    OSIFY_SYNCH_MUTEX,          /* Mutex ricorsivo con tracciamento proprietario */
    OSIFY_SYNCH_SEMAPHORE,      /* Semaforo a conteggio */
    OSIFY_SYNCH_TIMER,          /* Timer hardware periodico o one-shot */
    OSIFY_SYNCH_PORT,           /* Porta IPC Capability / Mach Port */
    OSIFY_SYNCH_TASK            /* Stato di terminazione di un processo o thread */
} osify_synch_type_t;

/* Header Comune a Ogni Oggetto del Kernel Sincronizzabile */
typedef struct osify_synch_hdr {
    osify_synch_type_t type;
    volatile bool      signaled;
    uint32_t           count;
    struct osify_waiter *wait_queue; /* Lista thread in attesa */
} osify_synch_hdr_t;

/* Modalita di Attesa WaitMux */
#define OSIFY_WAIT_ANY      0   /* Risveglio non appena ALMENO UN oggetto e segnalato */
#define OSIFY_WAIT_ALL      1   /* Risveglio SOLO quando TUTTI gli oggetti sono segnalati */
#define OSIFY_WAIT_ALERTABLE 2  /* Interrompibile da segnali o APC */

/* Inizializzazione Primitiva di Sincronizzazione */
void osify_synch_init(osify_synch_hdr_t *hdr, osify_synch_type_t type, bool initial_state);
void osify_synch_signal(osify_synch_hdr_t *hdr);
void osify_synch_reset(osify_synch_hdr_t *hdr);

/* Primitiva Kernel Superset: WaitMux */
/* Restituisce l'indice dell'oggetto segnalato (se WAIT_ANY) o 0 (se WAIT_ALL), oppure errore negativo */
int32_t osify_wait_mux(osify_synch_hdr_t **objects, size_t count, uint32_t mode, uint64_t timeout_ns);

#endif /* OSIFY_SYNCH_H */
