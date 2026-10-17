/* ==============================================================================
 * OSify Universal Path Unifier (sistema/nucleo/kernel/compat/osify_path_unifier.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Traduzione trasparente a livello 0 dei percorsi file (No-libc Freestanding):
 * Mappa C:\, /usr, /home e /Library nell'albero nativo /Sistema, /Applicazioni, /Utenti.
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

int osify_path_unify(const char *input_path, char *output_unified, size_t max_len) {
    if (!input_path || !output_unified || max_len == 0) return -1;

    char temp[256];
    size_t in_len = osify_strlen(input_path);
    if (in_len >= sizeof(temp)) in_len = sizeof(temp) - 1;

    /* Normalizzazione delle barre rovesciate Windows '\\' in '/' */
    for (size_t i = 0; i < in_len; i++) {
        temp[i] = (input_path[i] == '\\') ? '/' : input_path[i];
    }
    temp[in_len] = '\0';

    /* 1. Mappatura percorsi Windows (C:/Users -> /Utenti, C:/Program Files -> /Applicazioni, C:/Windows -> /Sistema) */
    if (osify_strncmp(temp, "C:/Users/", 9) == 0 || osify_strncmp(temp, "c:/users/", 9) == 0) {
        osify_snprintf(output_unified, max_len, "/Utenti/%s", temp + 9);
        return 0;
    }
    if (osify_strncmp(temp, "C:/Program Files/", 17) == 0 || osify_strncmp(temp, "c:/program files/", 17) == 0) {
        osify_snprintf(output_unified, max_len, "/Applicazioni/%s", temp + 17);
        return 0;
    }
    if (osify_strncmp(temp, "C:/Windows/", 11) == 0 || osify_strncmp(temp, "c:/windows/", 11) == 0) {
        osify_snprintf(output_unified, max_len, "/Sistema/%s", temp + 11);
        return 0;
    }

    /* 2. Mappatura percorsi POSIX / Linux (/home/... -> /Utenti/..., /opt -> /Applicazioni) */
    if (osify_strncmp(temp, "/home/", 6) == 0) {
        osify_snprintf(output_unified, max_len, "/Utenti/%s", temp + 6);
        return 0;
    }
    if (osify_strncmp(temp, "/opt/", 5) == 0) {
        osify_snprintf(output_unified, max_len, "/Applicazioni/%s", temp + 5);
        return 0;
    }
    if (osify_strncmp(temp, "/usr/bin/", 9) == 0) {
        osify_snprintf(output_unified, max_len, "/Sistema/Binari/%s", temp + 9);
        return 0;
    }

    /* 3. Mappatura percorsi macOS (/Users/... -> /Utenti/..., /Applications -> /Applicazioni) */
    if (osify_strncmp(temp, "/Users/", 7) == 0) {
        osify_snprintf(output_unified, max_len, "/Utenti/%s", temp + 7);
        return 0;
    }
    if (osify_strncmp(temp, "/Applications/", 14) == 0) {
        osify_snprintf(output_unified, max_len, "/Applicazioni/%s", temp + 14);
        return 0;
    }

    /* Se gia in formato nativo OSify o relativo, copia direttamente */
    osify_strncpy(output_unified, temp, max_len - 1);
    output_unified[max_len - 1] = '\0';
    return 0;
}
