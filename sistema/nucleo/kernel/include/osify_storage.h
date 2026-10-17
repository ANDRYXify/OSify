/* ==============================================================================
 * OSify Bare-Metal Storage & Disk Driver (sistema/nucleo/kernel/include/osify_storage.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Driver disco ATA PIO & AHCI SATA per lettura/scrittura blocchi fisici LBA28/LBA48
 * e parser tabelle partizioni GPT (GUID Partition Table) ed MBR.
 * ==============================================================================
 */

#ifndef OSIFY_STORAGE_H
#define OSIFY_STORAGE_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define OSIFY_SECTOR_SIZE 512

/* Tipologia Controller Disco */
typedef enum {
    STORAGE_TYPE_UNKNOWN = 0,
    STORAGE_TYPE_ATA_IDE,       /* Controller IDE/PATA per computer vintage */
    STORAGE_TYPE_AHCI_SATA,     /* Controller SATA moderno */
    STORAGE_TYPE_NVME           /* Controller SSD NVMe ad altissima velocita */
} osify_storage_type_t;

/* Descrittore Unita Disco */
typedef struct {
    osify_storage_type_t type;
    uint32_t drive_id;
    uint64_t total_sectors;
    uint64_t capacity_bytes;
    bool     is_present;
    char     model[40];
} osify_disk_t;

/* Descrittore Partizione */
typedef struct {
    uint32_t partition_id;
    uint64_t start_lba;
    uint64_t sector_count;
    char     type_guid[37];
    char     name[64];
    bool     is_active;
} osify_partition_t;

/* Inizializzazione Storage Fisico */
void osify_storage_init(void);
bool osify_storage_read_sector(uint32_t drive, uint64_t lba, void *buffer);
bool osify_storage_write_sector(uint32_t drive, uint64_t lba, const void *buffer);
int  osify_storage_parse_gpt(uint32_t drive, osify_partition_t *partitions, size_t max_parts);

/* File System Nativo OSifyFS (Superblock, Inodes, Directory) */
typedef struct {
    uint32_t magic;         /* 'OSFS' = 0x5346534F */
    uint32_t version;       /* 1 */
    uint64_t total_blocks;
    uint64_t free_blocks;
    uint64_t root_inode;
} osify_fs_superblock_t;

typedef struct {
    uint32_t inode_id;
    uint32_t file_type;     /* 1=File, 2=Cartella */
    uint64_t size_bytes;
    uint64_t block_pointers[12];
    char     name[64];
} osify_fs_inode_t;

void osify_fs_init(uint32_t drive);
int  osify_fs_read_file(const char *path, void *out_buf, size_t max_len);
int  osify_fs_write_file(const char *path, const void *data, size_t len);

#endif /* OSIFY_STORAGE_H */
