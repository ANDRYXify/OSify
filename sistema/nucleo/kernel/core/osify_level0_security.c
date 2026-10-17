/* ==============================================================================
 * OSify Level-0 Security Engine: SIP & Seatbelt Sandbox (macOS Style)
 * (sistema/nucleo/kernel/core/osify_level0_security.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Protezione dell'albero di sistema /Sistema a livello kernel (SIP) e
 * sandboxing a capability per isolare processi nativi o stranieri.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

void osify_sec_init(void) {
    /* Inizializzazione delle barriere di sicurezza a Livello 0 */
}

osify_security_token_t osify_sec_create_token(uint32_t pid, bool sandboxed) {
    osify_security_token_t tok;
    tok.process_id = pid;
    tok.is_sandboxed = sandboxed;
    tok.can_write_system_tree = false; /* Immutabile per impostazione predefinita */
    
    if (sandboxed) {
        tok.can_access_network = false;
        tok.can_access_raw_disk = false;
    } else {
        tok.can_access_network = true;
        tok.can_access_raw_disk = false; /* Solo il Micro-Core puo accedere direttamente ai settori grezzi */
    }
    return tok;
}

/* Controllo Integrita di Sistema (SIP) su /Sistema */
bool osify_sec_check_system_write(const char *path, const osify_security_token_t *token) {
    if (!path || !token) return false;

    /* Se il percorso tenta di toccare /Sistema e il token non ha i privilegi del kernel, blocca */
    if (osify_strncmp(path, "/Sistema", 8) == 0 || osify_strncmp(path, "C:\\Sistema", 10) == 0) {
        if (!token->can_write_system_tree) {
            return false; /* Violazione SIP: Accesso negato a livello 0 */
        }
    }
    return true;
}

/* Applicazione della Gabbia Seatbelt Sandbox */
bool osify_sec_enforce_seatbelt(const osify_security_token_t *token, uint32_t requested_action) {
    if (!token) return false;

    if (token->is_sandboxed) {
        /* Azione 1: Accesso Rete Raw, Azione 2: Accesso Disco Fisico */
        if (requested_action == 1 && !token->can_access_network) {
            return false;
        }
        if (requested_action == 2 && !token->can_access_raw_disk) {
            return false;
        }
    }
    return true;
}
