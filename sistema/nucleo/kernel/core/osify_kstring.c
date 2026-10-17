/* ==============================================================================
 * OSify Kernel Freestanding Standard Library Implementation
 * (sistema/nucleo/kernel/core/osify_kstring.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Implementazione bare-metal pura per garantire l'autonomia assoluta del kernel.
 * ==============================================================================
 */

#include "../include/osify_kstring.h"
#include <stdarg.h>

void *osify_memcpy(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;
    while (n--) {
        *d++ = *s++;
    }
    return dest;
}

void *osify_memset(void *s, int c, size_t n) {
    uint8_t *p = (uint8_t *)s;
    while (n--) {
        *p++ = (uint8_t)c;
    }
    return s;
}

int osify_memcmp(const void *s1, const void *s2, size_t n) {
    const uint8_t *p1 = (const uint8_t *)s1;
    const uint8_t *p2 = (const uint8_t *)s2;
    while (n--) {
        if (*p1 != *p2) return *p1 - *p2;
        p1++;
        p2++;
    }
    return 0;
}

size_t osify_strlen(const char *s) {
    size_t len = 0;
    while (s && s[len]) len++;
    return len;
}

char *osify_strcpy(char *dest, const char *src) {
    char *ret = dest;
    while ((*dest++ = *src++));
    return ret;
}

char *osify_strncpy(char *dest, const char *src, size_t n) {
    char *ret = dest;
    while (n && (*dest++ = *src++)) n--;
    while (n--) *dest++ = '\0';
    return ret;
}

int osify_strcmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++;
        s2++;
    }
    return *(const unsigned char *)s1 - *(const unsigned char *)s2;
}

int osify_strncmp(const char *s1, const char *s2, size_t n) {
    while (n && *s1 && (*s1 == *s2)) {
        s1++;
        s2++;
        n--;
    }
    if (n == 0) return 0;
    return *(const unsigned char *)s1 - *(const unsigned char *)s2;
}

/* Formattatore numerico bare-metal autonomo per snprintf */
static int u64_to_str(uint64_t val, char *buf, int base) {
    char tmp[32];
    int i = 0, j = 0;
    if (val == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return 1;
    }
    while (val > 0) {
        int rem = val % base;
        tmp[i++] = (rem < 10) ? ('0' + rem) : ('a' + rem - 10);
        val /= base;
    }
    while (i > 0) {
        buf[j++] = tmp[--i];
    }
    buf[j] = '\0';
    return j;
}

int osify_snprintf(char *str, size_t size, const char *format, ...) {
    if (!str || size == 0 || !format) return 0;

    va_list args;
    va_start(args, format);

    size_t written = 0;
    while (*format && written + 1 < size) {
        if (*format == '%' && *(format + 1)) {
            format++;
            if (*format == 's') {
                const char *s = va_arg(args, const char *);
                if (!s) s = "(null)";
                while (*s && written + 1 < size) {
                    str[written++] = *s++;
                }
            } else if (*format == 'd' || *format == 'u') {
                uint64_t v = va_arg(args, uint32_t);
                char num_buf[32];
                u64_to_str(v, num_buf, 10);
                for (int k = 0; num_buf[k] && written + 1 < size; k++) {
                    str[written++] = num_buf[k];
                }
            } else if (*format == 'x' || *format == 'X') {
                uint64_t v = va_arg(args, uint64_t);
                char num_buf[32];
                u64_to_str(v, num_buf, 16);
                for (int k = 0; num_buf[k] && written + 1 < size; k++) {
                    str[written++] = num_buf[k];
                }
            } else if (*format == '%') {
                str[written++] = '%';
            }
        } else {
            str[written++] = *format;
        }
        format++;
    }

    str[written] = '\0';
    va_end(args);
    return (int)written;
}
