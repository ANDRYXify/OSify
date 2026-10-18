/* ==============================================================================
 * OSify Heterogeneous Process & Hardware Dispatcher (osify_hetero_dispatch.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Gestione adattiva e differenziata dei carichi di lavoro al silicio:
 * diversifica l'esecuzione tra ALU scalare, ALU vettoriale SIMD, GPU blitter e I/O.
 * Architettura 100% Driverless: massimizza le prestazioni su qualsiasi silicio.
 * ==============================================================================
 */

#include "../include/osify_hetero_dispatch.h"
#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

static osify_process_connector_t s_task_table[OSIFY_MAX_TASKS];
static osify_dispatch_stats_t    s_stats;
static bool                      s_initialized = false;

/* Inizializzazione dello Scheduler Eterogeneo e Connettori */
void osify_hetero_dispatch_init(void) {
    osify_memset(s_task_table, 0, sizeof(s_task_table));
    osify_memset(&s_stats, 0, sizeof(s_stats));

    /* Pre-registrazione dei connettori di sistema fondamentali */
    osify_task_register(1, "OSify-Kernel-Level0",  WORKLOAD_SYSTEM_LOGIC, 10);
    osify_task_register(2, "OSify-Crypto-Guard",   WORKLOAD_CRYPTO_MATH,  9);
    osify_task_register(3, "OSify-DarkGlass-UI",    WORKLOAD_GRAPHICS_UI,  8);
    osify_task_register(4, "OSify-Storage-AsyncIO", WORKLOAD_STORAGE_NET,  7);
    osify_task_register(5, "OSify-Audio-DSP",       WORKLOAD_CRYPTO_MATH,  6);

    /* Dispatch iniziale dei connettori di sistema */
    for (uint32_t i = 1; i <= 5; i++) {
        osify_task_dispatch(i);
    }

    s_initialized = true;
}

/* Registrazione di un Nuovo Processo con Assegnazione Adattiva dell'Unita */
int osify_task_register(uint32_t task_id, const char *name, osify_workload_t workload, uint32_t priority) {
    if (task_id == 0 || task_id >= OSIFY_MAX_TASKS) return -1;

    osify_process_connector_t *t = &s_task_table[task_id];
    t->task_id = task_id;
    osify_strncpy(t->name, name ? name : "Processo-Anonimo", sizeof(t->name) - 1);
    t->workload = workload;
    t->priority = priority;
    t->state = TASK_STATE_READY;
    t->instructions_executed = 0;
    t->cycles_spent = 0;
    t->is_active = true;

    /* Selezione automatica dell'Unita Computazionale piu efficiente (Driverless) */
    switch (workload) {
        case WORKLOAD_SYSTEM_LOGIC:
            t->assigned_unit = UNIT_ALU_SCALAR;
            s_stats.tasks_on_alu_scalar++;
            break;
        case WORKLOAD_CRYPTO_MATH:
            t->assigned_unit = UNIT_ALU_VECTOR;
            s_stats.tasks_on_alu_vector++;
            break;
        case WORKLOAD_GRAPHICS_UI:
            t->assigned_unit = UNIT_GPU_BLITTER;
            s_stats.tasks_on_gpu_blitter++;
            break;
        case WORKLOAD_STORAGE_NET:
            t->assigned_unit = UNIT_ASYNC_IO;
            s_stats.tasks_on_async_io++;
            break;
        default:
            t->assigned_unit = UNIT_ALU_SCALAR;
            s_stats.tasks_on_alu_scalar++;
            break;
    }

    s_stats.total_tasks_dispatched++;
    return 0;
}

/* Esecuzione e Dispatching del Task sull'Hardware Connesso */
bool osify_task_dispatch(uint32_t task_id) {
    if (task_id == 0 || task_id >= OSIFY_MAX_TASKS) return false;
    osify_process_connector_t *t = &s_task_table[task_id];
    if (!t->is_active) return false;

    t->state = TASK_STATE_RUNNING;

    /* Simulazione esecuzione deterministica basata sull'unita */
    if (t->assigned_unit == UNIT_ALU_VECTOR) {
        /* Calcolo SIMD: 64 operazioni per ciclo vettoriale */
        t->instructions_executed += 64000;
        t->cycles_spent += 1000;
        s_stats.total_gflops_delivered += 5;
    } else if (t->assigned_unit == UNIT_GPU_BLITTER) {
        /* Blit VRAM: 1024 dword trasferite */
        t->instructions_executed += 32000;
        t->cycles_spent += 500;
    } else if (t->assigned_unit == UNIT_ASYNC_IO) {
        /* I/O non bloccante */
        t->instructions_executed += 1000;
        t->cycles_spent += 100;
    } else {
        /* ALU scalare standard */
        t->instructions_executed += 5000;
        t->cycles_spent += 2500;
    }

    t->state = TASK_STATE_READY;
    return true;
}

/* Recupero del Descrittore Connettore Processo */
osify_process_connector_t *osify_task_get(uint32_t task_id) {
    if (task_id == 0 || task_id >= OSIFY_MAX_TASKS) return NULL;
    if (!s_task_table[task_id].is_active) return NULL;
    return &s_task_table[task_id];
}

/* Statistiche del Sottosistema Eterogeneo */
void osify_hetero_get_stats(osify_dispatch_stats_t *stats) {
    if (!stats) return;
    if (!s_initialized) {
        osify_hetero_dispatch_init();
    }
    osify_memcpy(stats, &s_stats, sizeof(osify_dispatch_stats_t));
}
