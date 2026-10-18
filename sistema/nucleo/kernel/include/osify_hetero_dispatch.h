/* ==============================================================================
 * OSify Heterogeneous Process & Hardware Dispatcher (osify_hetero_dispatch.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Gestione adattiva e differenziata dei carichi di lavoro al silicio:
 * diversifica l'esecuzione tra ALU scalare, ALU vettoriale SIMD, GPU blitter e I/O.
 * Architettura 100% Driverless: massimizza le prestazioni su qualsiasi silicio.
 * ==============================================================================
 */

#ifndef OSIFY_HETERO_DISPATCH_H
#define OSIFY_HETERO_DISPATCH_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Tipologie di Unita Computazionali Eterogenee */
typedef enum {
    UNIT_ALU_SCALAR   = 0x01, /* Core ALU standard per logica di controllo, IPC e syscall */
    UNIT_ALU_VECTOR   = 0x02, /* Pipeline SIMD (SSE2/AVX/AVX2/NEON) per crittografia, audio e math */
    UNIT_GPU_BLITTER  = 0x04, /* Unita grafica/VRAM e memory burst blitter per desktop e compositing */
    UNIT_ASYNC_IO     = 0x08  /* Canale asincrono DMA a latenza zero per storage e rete */
} osify_compute_unit_t;

/* Classificazione del Carico di Lavoro (Workload) */
typedef enum {
    WORKLOAD_SYSTEM_LOGIC = 0, /* Task di sistema, parser, gestione processi -> ALU scalare */
    WORKLOAD_CRYPTO_MATH,      /* Calcolo numerico, hash, cifratura, DSP audio -> ALU vettoriale */
    WORKLOAD_GRAPHICS_UI,      /* Rendering interfaccia, finestre, trasformazioni -> GPU Blitter */
    WORKLOAD_STORAGE_NET       /* Trasferimenti a blocchi disco e pacchetti rete -> Async I/O */
} osify_workload_t;

/* Stato del Processo nello Scheduler Eterogeneo */
typedef enum {
    TASK_STATE_IDLE = 0,
    TASK_STATE_READY,
    TASK_STATE_RUNNING,
    TASK_STATE_WAITING_IO,
    TASK_STATE_COMPLETED
} osify_task_state_t;

#define OSIFY_MAX_TASKS 64

/* Descrittore Connettore Processo Eterogeneo */
typedef struct {
    uint32_t            task_id;
    char                name[32];
    osify_workload_t    workload;
    osify_compute_unit_t assigned_unit;
    osify_task_state_t  state;
    uint32_t            priority;
    uint64_t            instructions_executed;
    uint64_t            cycles_spent;
    bool                is_active;
} osify_process_connector_t;

/* Statistiche del Dispatcher Eterogeneo */
typedef struct {
    uint32_t total_tasks_dispatched;
    uint32_t tasks_on_alu_scalar;
    uint32_t tasks_on_alu_vector;
    uint32_t tasks_on_gpu_blitter;
    uint32_t tasks_on_async_io;
    uint64_t total_gflops_delivered;
} osify_dispatch_stats_t;

/* --- Funzioni Principali del Dispatcher Eterogeneo --- */
void osify_hetero_dispatch_init(void);
int  osify_task_register(uint32_t task_id, const char *name, osify_workload_t workload, uint32_t priority);
bool osify_task_dispatch(uint32_t task_id);
osify_process_connector_t *osify_task_get(uint32_t task_id);
void osify_hetero_get_stats(osify_dispatch_stats_t *stats);

/* Blitter Vettoriale Driverless ad alto throughput per il Framebuffer */
void osify_driverless_blit_rect(uint32_t *dest, uint32_t dest_pitch_pixels,
                                int x, int y, int w, int h, uint32_t color);
void osify_driverless_copy_buffer(uint32_t *dest, const uint32_t *src, size_t total_pixels);

#endif /* OSIFY_HETERO_DISPATCH_H */
