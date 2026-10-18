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

typedef enum {
    INSTALL_MODE_FULL_DISK = 0,       /* 1. Intero Disco (Auto-GPT: ESP + OSifyFS) */
    INSTALL_MODE_CUSTOM_PARTITION = 1, /* 2. Partizione Personalizzata (es. /dev/sda2) */
    INSTALL_MODE_DUAL_BOOT = 2        /* 3. Affianca ad Altro OS (Dual-Boot Windows/Linux) */
} osify_install_mode_t;

typedef struct {
    char     username[32];
    char     hostname[32];
    char     password[32];
    char     keyboard_layout[16];
    uint32_t avatar_color;
} osify_user_profile_t;

typedef struct {
    osify_install_mode_t mode;
    uint32_t target_partition_id;
    char     partition_name[32];
    uint64_t partition_size_mb;
} osify_partition_choice_t;

typedef struct {
    uint32_t disk_id;
    char     model[32];
    uint64_t size_bytes;
    bool     is_ssd;
    bool     is_target;
} osify_disk_info_t;

typedef struct {
    osify_install_step_t     step;
    uint32_t                 target_disk_id;
    uint8_t                  progress_percent; /* 0 - 100 */
    char                     status_msg[128];
    bool                     is_completed;
    bool                     is_booted_into_installed;
    uint32_t                 current_wizard_tab; /* 0: Destinazione, 1: Profilo, 2: Installazione, 3: Pronto */
    osify_disk_info_t        target_disk;
    osify_partition_choice_t part_choice;
    osify_user_profile_t     user_profile;
} osify_installer_state_t;

void osify_installer_init(void);
bool osify_installer_start(uint32_t target_disk);
bool osify_installer_start_configured(uint32_t target_disk, int mode, uint32_t part_id, const osify_user_profile_t *prof);
void osify_installer_set_mode(int mode);
void osify_installer_set_target_partition(uint32_t part_id, const char *name, uint64_t size_mb);
void osify_installer_set_user_profile(const char *username, const char *hostname, const char *password, const char *kb);
void osify_installer_set_wizard_tab(uint32_t tab);
bool osify_installer_boot_into_installed_system(void);
void osify_installer_render(osify_framebuffer_t *fb, int x, int y, int w, int h);
const osify_installer_state_t *osify_installer_get_state(void);

#endif /* OSIFY_INSTALLER_H */
