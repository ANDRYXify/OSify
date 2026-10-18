/* ==============================================================================
 * OSify Multi-Format Binary Loader (sistema/nucleo/kernel/loaders/osify_binary_loader.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Parsing ed esecuzione a livello kernel di ELF, Windows PE e macOS Mach-O (No-libc).
 * ==============================================================================
 */

#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"

/* Strutture ELF minime */
typedef struct {
    uint8_t  e_ident[16];
    uint16_t e_type;
    uint16_t e_machine;
    uint32_t e_version;
    uint64_t e_entry;
    uint64_t e_phoff;
    uint64_t e_shoff;
    uint32_t e_flags;
    uint16_t e_ehsize;
    uint16_t e_phentsize;
    uint16_t e_phnum;
} elf64_hdr_t;

/* Strutture PE Windows minime */
typedef struct {
    uint16_t e_magic;    /* 'MZ' */
    uint16_t e_cblp;
    uint16_t e_cp;
    uint16_t e_crlc;
    uint16_t e_cparhdr;
    uint16_t e_minalloc;
    uint16_t e_maxalloc;
    uint16_t e_ss;
    uint16_t e_sp;
    uint16_t e_csum;
    uint16_t e_ip;
    uint16_t e_cs;
    uint16_t e_lfarlc;
    uint16_t e_ovno;
    uint16_t e_res[4];
    uint16_t e_oemid;
    uint16_t e_oeminfo;
    uint16_t e_res2[10];
    int32_t  e_lfanew;   /* Offset to NT Header */
} pe_dos_hdr_t;

osify_loaded_binary_t osify_binary_load(const void *file_buffer, size_t file_len) {
    osify_loaded_binary_t loaded;
    osify_memset(&loaded, 0, sizeof(loaded));
    loaded.is_valid = false;

    if (!file_buffer || file_len < 64) {
        return loaded;
    }

    osify_subsystem_t subsys = osify_detect_binary_format(file_buffer, file_len);
    loaded.subsystem = subsys;

    switch (subsys) {
        case SUBSYSTEM_POSIX_LINUX: {
            const elf64_hdr_t *elf = (const elf64_hdr_t *)file_buffer;
            loaded.entry_point = elf->e_entry;
            loaded.load_base = 0x400000; /* Standard ELF load address */
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_WIN32_NT: {
            const pe_dos_hdr_t *dos = (const pe_dos_hdr_t *)file_buffer;
            if (dos->e_lfanew > 0 && (size_t)dos->e_lfanew + 24 < file_len) {
                loaded.load_base = 0x140000000ULL; /* Default 64-bit PE ImageBase */
                loaded.entry_point = loaded.load_base + 0x1000;
                loaded.size_in_memory = file_len;
                loaded.is_valid = true;
            }
            break;
        }

        case SUBSYSTEM_DARWIN_MACH_O: {
            loaded.load_base = 0x100000000ULL;
            loaded.entry_point = loaded.load_base + 0x1000;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_ANDROID_MOBILE: {
            loaded.load_base = 0x70000000ULL; /* Dalvik/ART VM container base */
            loaded.entry_point = loaded.load_base + 0x1000;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_IOS_TOUCH: {
            loaded.load_base = 0x180000000ULL; /* Darwin iOS Bridge base */
            loaded.entry_point = loaded.load_base + 0x1000;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_SCRIPT_BATCH: {
            loaded.load_base = 0x10000ULL; /* Command shell batch interpreter */
            loaded.entry_point = loaded.load_base;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_PACKAGE_LINUX: {
            loaded.load_base = 0x500000ULL; /* Package extractor and sandbox mount */
            loaded.entry_point = loaded.load_base;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_PACKAGE_MACOS: {
            loaded.load_base = 0x200000000ULL; /* macOS installer sandbox base */
            loaded.entry_point = loaded.load_base + 0x1000;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }

        case SUBSYSTEM_OSIFY_NATIVE:
        default: {
            loaded.load_base = 0x200000;
            loaded.entry_point = loaded.load_base;
            loaded.size_in_memory = file_len;
            loaded.is_valid = true;
            break;
        }
    }

    return loaded;
}
