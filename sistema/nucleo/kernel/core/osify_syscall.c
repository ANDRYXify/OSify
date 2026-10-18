/* ==============================================================================
 * OSify Native System Call Dispatcher & Ring 0/Ring 3 Bridge
 * (sistema/nucleo/kernel/core/osify_syscall.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Gestione delle chiamate di sistema native int 0x80 con transizione di privilegio.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

/* Costanti Numeriche System Call Native OSify */
#define OSIFY_SYS_WRITE     1
#define OSIFY_SYS_EXIT      2
#define OSIFY_SYS_GET_TICKS 3
#define OSIFY_SYS_MEM_STATS 4
#define OSIFY_SYS_FB_INFO   5
#define OSIFY_SYS_PING      6

void osify_serial_print(const char *s);

/* Wrapper di basso livello per invocare int 0x80 da C */
int32_t osify_syscall(uint32_t num, uintptr_t a1, uintptr_t a2, uintptr_t a3) {
    int32_t ret;
#if defined(__i386__)
    __asm__ volatile (
        "int $0x80"
        : "=a" (ret)
        : "0" (num), "b" ((uint32_t)a1), "c" ((uint32_t)a2), "d" ((uint32_t)a3)
        : "memory"
    );
#else
    (void)num; (void)a1; (void)a2; (void)a3;
    ret = 0;
#endif
    return ret;
}

/* Dispatcher C invocato dall'ISR assembly osify_syscall_isr */
int32_t osify_syscall_dispatch(uint32_t num, uintptr_t a1, uintptr_t a2, uintptr_t a3) {
    switch (num) {
        case OSIFY_SYS_WRITE: {
            int fd = (int)a1;
            const char *buf = (const char *)a2;
            size_t count = (size_t)a3;
            if (!buf) return -1;
            if (fd == 1 || fd == 2) {
                osify_serial_print(buf);
                return (int32_t)count;
            }
            return -1;
        }

        case OSIFY_SYS_EXIT: {
            int code = (int)a1;
            char msg[64];
            osify_snprintf(msg, sizeof(msg), "[SYSCALL] Task terminato con codice %d.\n", code);
            osify_serial_print(msg);
            return 0;
        }

        case OSIFY_SYS_GET_TICKS: {
            static uint32_t s_ticks = 1000;
            return (int32_t)(s_ticks += 10);
        }

        case OSIFY_SYS_MEM_STATS: {
            uint32_t *p_total = (uint32_t *)(uintptr_t)a1;
            uint32_t *p_free  = (uint32_t *)(uintptr_t)a2;
            if (p_total) *p_total = 2048; /* MB */
            if (p_free)  *p_free  = 2016; /* MB */
            return 0;
        }

        case OSIFY_SYS_FB_INFO: {
            uint32_t *pw = (uint32_t *)(uintptr_t)a1;
            uint32_t *ph = (uint32_t *)(uintptr_t)a2;
            if (pw) *pw = 1024;
            if (ph) *ph = 768;
            return 0;
        }

        case OSIFY_SYS_PING: {
            /* Attestazione ontologica OSify (magic: 0x051F1050) */
            return 0x051F1050;
        }

        default: {
            char warn[64];
            osify_snprintf(warn, sizeof(warn), "[SYSCALL] Vettore %u non implementato.\n", num);
            osify_serial_print(warn);
            return -1;
        }
    }
}
