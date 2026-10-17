/* ==============================================================================
 * OSify Bare-Metal Disk Installer (sistema/nucleo/kernel/include/osify_installer.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Installatore bare-metal autonomo: partizionamento GPT del disco fisso interno,
 * installazione del sistema operativo OSify A.0 e configurazione del bootloader.
 * ==============================================================================
 */

#ifndef OSIFY_INSTALLER_H
#define OSIFY_INSTALLER_H

#include "osify_kernel.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Tabella Partizioni GPT Bare-Metal (UEFI Spec 2.10) */
typedef struct {
    uint8_t  signature[8];       /* "EFI PART" */
    uint32_t revision;           /* 0x00010000 */
    uint32_t header_size;        /* 92 byte */
    uint32_t header_crc32;
    uint32_t reserved;
    uint64_t my_lba;             /* LBA 1 */
    uint64_t alternate_lba;      /* Ultimo settore disco */
    uint64_t first_usable_lba;   /* LBA 34 */
    uint64_t last_usable_lba;    /* Ultimo settore - 34 */
    uint8_t  disk_guid[16];
    uint64_t partition_entry_lba;/* LBA 2 */
    uint32_t num_entries;        /* 128 */
    uint32_t entry_size;         /* 128 byte */
    uint32_t entries_crc32;
} __attribute__((packed)) osify_gpt_header_t;

typedef struct {
    uint8_t  type_guid[16];
    uint8_t  unique_guid[16];
    uint64_t starting_lba;
    uint64_t ending_lba;
    uint64_t attributes;
    uint16_t name[36];           /* UTF-16LE */
} __attribute__((packed)) osify_gpt_entry_t;

typedef enum {
    INSTALL_IDLE = 0,
    INSTALL_SCANNING,
    INSTALL_PARTITIONING,
    INSTALL_COPYING_KERNEL,
    INSTALL_WRITING_BOOTLOADER,
    INSTALL_FINISHED,
    INSTALL_ERROR
} osify_install_step_t;

typedef struct {
    uint32_t disk_id;
    char     model[32];
    uint64_t size_bytes;
    bool     is_ssd;
    bool     is_target;
} osify_disk_info_t;

typedef struct {
    osify_install_step_t step;
    uint32_t target_disk_id;
    uint8_t  progress_percent; /* 0 - 100 */
    char     status_msg[128];
    bool     is_completed;
    osify_disk_info_t target_disk;
} osify_installer_state_t;

void osify_installer_init(void);
bool osify_installer_start(uint32_t target_disk);
void osify_installer_render(osify_framebuffer_t *fb, int x, int y, int w, int h);
const osify_installer_state_t *osify_installer_get_state(void);

#endif /* OSIFY_INSTALLER_H */
