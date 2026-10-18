/* ==============================================================================
 * OSify RingBus: Zero-Copy Lock-Free IPC Engine
 * (sistema/nucleo/include/osify_ringbus.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Canale di comunicazione ad altissimo throughput basato su memorie condivise
 * e code circolari atomiche: zero copie, zero intermediari lenti, latenza minima.
 * ==============================================================================
 */

#ifndef OSIFY_RINGBUS_H
#define OSIFY_RINGBUS_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define OSIFY_RINGBUS_ENTRY_SIZE 64
#define OSIFY_RINGBUS_DEFAULT_CAPACITY 256

/* Elemento di Sottomissione Comando (SQE - Submission Queue Entry) */
typedef struct {
    uint32_t opcode;        /* Comando specifico del sottosistema (Render, Audio, Net, FS) */
    uint32_t flags;         /* Flag di esecuzione (Asincrono, Fence, Priority) */
    uint64_t user_data;     /* Identificativo o callback del chiamante */
    uint64_t addr;          /* Puntatore fisico/virtuale al payload condiviso */
    uint32_t len;           /* Lunghezza payload */
    uint32_t extra[7];      /* Parametri extra a 64-byte totali per cache-line fit */
} __attribute__((aligned(64))) osify_ringbus_sqe_t;

/* Elemento di Completamento Risultato (CQE - Completion Queue Entry) */
typedef struct {
    uint64_t user_data;     /* Trasparenza per correlare la richiesta */
    int32_t  res;           /* Codice di ritorno o byte trasferiti */
    uint32_t flags;
} __attribute__((aligned(16))) osify_ringbus_cqe_t;

/* Header Condiviso del RingBus tra Produttore e Consumatore */
typedef struct {
    volatile uint32_t sq_head;
    volatile uint32_t sq_tail;
    volatile uint32_t sq_mask;
    
    volatile uint32_t cq_head;
    volatile uint32_t cq_tail;
    volatile uint32_t cq_mask;
    
    uint32_t flags;
    uint32_t capacity;
} osify_ringbus_hdr_t;

/* Descrittore Canale RingBus */
typedef struct {
    osify_ringbus_hdr_t *hdr;
    osify_ringbus_sqe_t *sqes;
    osify_ringbus_cqe_t *cqes;
    size_t               total_shm_size;
} osify_ringbus_t;

/* Inizializzazione e Ciclo di Vita del Canale RingBus */
int  osify_ringbus_create(osify_ringbus_t *rb, uint32_t capacity);
void osify_ringbus_destroy(osify_ringbus_t *rb);

/* Operazioni Lock-Free sul RingBus */
osify_ringbus_sqe_t *osify_ringbus_get_sqe(osify_ringbus_t *rb);
void                 osify_ringbus_submit(osify_ringbus_t *rb);
bool                 osify_ringbus_peek_cqe(osify_ringbus_t *rb, osify_ringbus_cqe_t *out_cqe);
void                 osify_ringbus_advance_cq(osify_ringbus_t *rb);

#endif /* OSIFY_RINGBUS_H */
