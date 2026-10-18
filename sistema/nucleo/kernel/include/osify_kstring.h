/* ==============================================================================
 * OSify Kernel Freestanding Standard Library (No-libc)
 * (sistema/nucleo/kernel/include/osify_kstring.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Funzioni di manipolazione memoria e stringhe 100% autonome e bare-metal.
 * Zero dipendenze da glibc, musl o librerie esterne.
 * ==============================================================================
 */

#ifndef OSIFY_KSTRING_H
#define OSIFY_KSTRING_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

void *osify_memcpy(void *dest, const void *src, size_t n);
void *osify_memset(void *s, int c, size_t n);
int   osify_memcmp(const void *s1, const void *s2, size_t n);

size_t osify_strlen(const char *s);
char  *osify_strcpy(char *dest, const char *src);
char  *osify_strncpy(char *dest, const char *src, size_t n);
int    osify_strcmp(const char *s1, const char *s2);
int    osify_strncmp(const char *s1, const char *s2, size_t n);
const char *osify_strstr(const char *haystack, const char *needle);

int    osify_snprintf(char *str, size_t size, const char *format, ...);

#endif /* OSIFY_KSTRING_H */
