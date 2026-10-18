/* ==============================================================================
 * OSify Capability Handle Subsystem (sistema/nucleo/include/osify_capability.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Modello di sicurezza a Capability: ogni handle e protetto da diritti granulari
 * non falsificabili. Zero file descriptor interi insicuri nel nucleo sovrano.
 * ==============================================================================
 */

#ifndef OSIFY_CAPABILITY_H
#define OSIFY_CAPABILITY_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Maschera dei Diritti di Accesso Granulari */
#define OSIFY_CAP_READ          (1u << 0)
#define OSIFY_CAP_WRITE         (1u << 1)
#define OSIFY_CAP_EXECUTE       (1u << 2)
#define OSIFY_CAP_MAP           (1u << 3)
#define OSIFY_CAP_SYNCHRONIZE   (1u << 4)
#define OSIFY_CAP_DUPLICATE     (1u << 5)
#define OSIFY_CAP_TRANSFER      (1u << 6)
#define OSIFY_CAP_SYS_ADMIN     (1u << 7)

/* Tipologie di Oggetti Sottostanti alla Capability */
typedef enum {
    OSIFY_OBJ_NONE = 0,
    OSIFY_OBJ_FILE,
    OSIFY_OBJ_DIRECTORY,
    OSIFY_OBJ_SHM,
    OSIFY_OBJ_PROCESS,
    OSIFY_OBJ_THREAD,
    OSIFY_OBJ_PORT,
    OSIFY_OBJ_SYNCH,
    OSIFY_OBJ_DEVICE
} osify_obj_type_t;

/* Descrittore Capability Handle */
typedef struct {
    uint32_t         id;
    osify_obj_type_t type;
    uint32_t         rights;
    uint32_t         generation;
    void            *kernel_object;
} osify_cap_handle_t;

/* Tabella Capability di Processo */
typedef struct {
    osify_cap_handle_t *handles;
    size_t              capacity;
    size_t              count;
} osify_cap_table_t;

/* Inizializzazione e Validazione Capability */
void osify_cap_table_init(osify_cap_table_t *table, size_t initial_capacity);
int  osify_cap_create(osify_cap_table_t *table, osify_obj_type_t type, void *kernel_obj, uint32_t rights, osify_cap_handle_t *out_handle);
bool osify_cap_verify(const osify_cap_table_t *table, uint32_t handle_id, uint32_t required_rights, void **out_kernel_obj);
int  osify_cap_close(osify_cap_table_t *table, uint32_t handle_id);

#endif /* OSIFY_CAPABILITY_H */
