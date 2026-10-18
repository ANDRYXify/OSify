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

const char *osify_strstr(const char *haystack, const char *needle) {
    if (!haystack || !needle) return NULL;
    if (*needle == '\0') return haystack;
    for (; *haystack; haystack++) {
        const char *h = haystack;
        const char *n = needle;
        while (*h && *n) {
            char ch = *h;
            char cn = *n;
            if (ch >= 'A' && ch <= 'Z') ch += 32;
            if (cn >= 'A' && cn <= 'Z') cn += 32;
            if (ch != cn) break;
            h++;
            n++;
        }
        if (*n == '\0') return haystack;
    }
    return NULL;
}

/* Formattatore numerico bare-metal autonomo per snprintf */
static int u64_to_str(uint64_t val, char *buf, int base, bool uppercase) {
    char tmp[65];
    int i = 0, j = 0;
    if (val == 0) {
        buf[0] = '0';
        buf[1] = '\0';
        return 1;
    }
    while (val > 0) {
        int rem = (int)(val % (uint64_t)base);
        if (rem < 10) {
            tmp[i++] = (char)('0' + rem);
        } else {
            tmp[i++] = (char)((uppercase ? 'A' : 'a') + rem - 10);
        }
        val /= (uint64_t)base;
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
            bool zero_pad = false;
            int width = 0;
            bool is_long = false;

            if (*format == '0') {
                zero_pad = true;
                format++;
            }
            while (*format >= '0' && *format <= '9') {
                width = width * 10 + (*format - '0');
                format++;
            }
            if (*format == 'l') {
                is_long = true;
                format++;
                if (*format == 'l') {
                    format++; /* ignora secondo 'l' se presente (es. %lld) */
                }
            }

            if (*format == 's') {
                const char *s = va_arg(args, const char *);
                if (!s) s = "(null)";
                int s_len = (int)osify_strlen(s);
                while (width > s_len && written + 1 < size) {
                    str[written++] = ' ';
                    width--;
                }
                while (*s && written + 1 < size) {
                    str[written++] = *s++;
                }
            } else if (*format == 'c') {
                char c = (char)va_arg(args, int);
                while (width > 1 && written + 1 < size) {
                    str[written++] = ' ';
                    width--;
                }
                if (written + 1 < size) {
                    str[written++] = c;
                }
            } else if (*format == 'd' || *format == 'i') {
                int64_t val = is_long ? (int64_t)va_arg(args, long) : (int64_t)va_arg(args, int);
                bool negative = false;
                uint64_t uval;
                if (val < 0) {
                    negative = true;
                    uval = (uint64_t)(-(val + 1)) + 1; /* safe against INT64_MIN overflow */
                } else {
                    uval = (uint64_t)val;
                }
                char num_buf[32];
                int num_len = u64_to_str(uval, num_buf, 10, false);
                int total_len = num_len + (negative ? 1 : 0);

                if (negative && zero_pad && written + 1 < size) {
                    str[written++] = '-';
                    negative = false;
                }
                while (width > total_len && written + 1 < size) {
                    str[written++] = zero_pad ? '0' : ' ';
                    width--;
                }
                if (negative && written + 1 < size) {
                    str[written++] = '-';
                }
                for (int k = 0; num_buf[k] && written + 1 < size; k++) {
                    str[written++] = num_buf[k];
                }
            } else if (*format == 'u') {
                uint64_t uval = is_long ? (uint64_t)va_arg(args, unsigned long) : (uint64_t)va_arg(args, unsigned int);
                char num_buf[32];
                int num_len = u64_to_str(uval, num_buf, 10, false);
                while (width > num_len && written + 1 < size) {
                    str[written++] = zero_pad ? '0' : ' ';
                    width--;
                }
                for (int k = 0; num_buf[k] && written + 1 < size; k++) {
                    str[written++] = num_buf[k];
                }
            } else if (*format == 'x' || *format == 'X') {
                uint64_t uval = is_long ? (uint64_t)va_arg(args, unsigned long) : (uint64_t)va_arg(args, unsigned int);
                char num_buf[32];
                int num_len = u64_to_str(uval, num_buf, 16, (*format == 'X'));
                while (width > num_len && written + 1 < size) {
                    str[written++] = zero_pad ? '0' : ' ';
                    width--;
                }
                for (int k = 0; num_buf[k] && written + 1 < size; k++) {
                    str[written++] = num_buf[k];
                }
            } else if (*format == 'p') {
                void *ptr = va_arg(args, void *);
                if (!ptr) {
                    const char *nil_str = "(nil)";
                    while (*nil_str && written + 1 < size) {
                        str[written++] = *nil_str++;
                    }
                } else {
                    if (written + 2 < size) {
                        str[written++] = '0';
                        str[written++] = 'x';
                    }
                    char ptr_buf[32];
                    u64_to_str((uint64_t)(uintptr_t)ptr, ptr_buf, 16, false);
                    for (int k = 0; ptr_buf[k] && written + 1 < size; k++) {
                        str[written++] = ptr_buf[k];
                    }
                }
            } else if (*format == '%') {
                str[written++] = '%';
            } else {
                str[written++] = *format;
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

/* Runtime Helper Freestanding: Divisione a 64-bit senza dipendenze libgcc */
uint64_t __udivdi3(uint64_t n, uint64_t d) {
    if (d == 0) return 0;
    uint64_t q = 0, r = 0;
    for (int i = 63; i >= 0; i--) {
        r = (r << 1) | ((n >> i) & 1ULL);
        if (r >= d) {
            r -= d;
            q |= (1ULL << i);
        }
    }
    return q;
}

uint64_t __umoddi3(uint64_t n, uint64_t d) {
    if (d == 0) return 0;
    uint64_t r = 0;
    for (int i = 63; i >= 0; i--) {
        r = (r << 1) | ((n >> i) & 1ULL);
        if (r >= d) {
            r -= d;
        }
    }
    return r;
}

int64_t __divdi3(int64_t a, int64_t b) {
    if (b == 0) return 0;
    int sign = 1;
    if (a < 0) { sign = -sign; a = -a; }
    if (b < 0) { sign = -sign; b = -b; }
    uint64_t res = __udivdi3((uint64_t)a, (uint64_t)b);
    return sign < 0 ? -(int64_t)res : (int64_t)res;
}

int64_t __moddi3(int64_t a, int64_t b) {
    if (b == 0) return 0;
    int sign = (a < 0) ? -1 : 1;
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    uint64_t res = __umoddi3((uint64_t)a, (uint64_t)b);
    return sign < 0 ? -(int64_t)res : (int64_t)res;
}


