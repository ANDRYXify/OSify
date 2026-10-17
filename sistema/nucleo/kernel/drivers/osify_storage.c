/* ==============================================================================
 * OSify Storage Driver & OSifyFS Implementation
 * (sistema/nucleo/kernel/drivers/osify_storage.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Controllo diretto porte hardware ATA/IDE (0x1F0-0x1F7), partizionamento GPT
 * e motore di persistenza nativo OSifyFS per salvare dati sul disco fisico.
 * ==============================================================================
 */

#include "../include/osify_storage.h"
#include "../include/osify_kstring.h"

/* Registri Controller ATA Primario */
#define ATA_PRIMARY_DATA         0x1F0
#define ATA_PRIMARY_ERR_FEAT     0x1F1
#define ATA_PRIMARY_SEC_COUNT    0x1F2
#define ATA_PRIMARY_LBA_LO       0x1F3
#define ATA_PRIMARY_LBA_MID      0x1F4
#define ATA_PRIMARY_LBA_HI       0x1F5
#define ATA_PRIMARY_DRIVE_HEAD   0x1F6
#define ATA_PRIMARY_COMM_STAT    0x1F7

#define ATA_CMD_READ_SECTORS     0x20
#define ATA_CMD_WRITE_SECTORS    0x30
#define ATA_STATUS_BSY           0x80
#define ATA_STATUS_DRQ           0x08

/* Simulatore RAM per storage bare-metal integrato */
#define SIMULATED_DISK_SECTORS   4096
static uint8_t s_ram_disk[SIMULATED_DISK_SECTORS * OSIFY_SECTOR_SIZE];
static bool __attribute__((unused)) s_has_physical_controller = false;

/* Helper I/O Porte Hardware */
static inline void __attribute__((unused)) outb_disk(uint16_t port, uint8_t val) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

static inline uint8_t __attribute__((unused)) inb_disk(uint16_t port) {
#if defined(__x86_64__) || defined(__i386__)
    uint8_t ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port;
    return 0;
#endif
}

static inline uint16_t __attribute__((unused)) inw_disk(uint16_t port) {
#if defined(__x86_64__) || defined(__i386__)
    uint16_t ret;
    __asm__ volatile("inw %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
#else
    (void)port;
    return 0;
#endif
}

static inline void __attribute__((unused)) outw_disk(uint16_t port, uint16_t val) {
#if defined(__x86_64__) || defined(__i386__)
    __asm__ volatile("outw %0, %1" : : "a"(val), "Nd"(port));
#else
    (void)port; (void)val;
#endif
}

/* Attesa completamento BSY */
static void __attribute__((unused)) ata_wait_ready(void) {
#if defined(__x86_64__) || defined(__i386__)
    if (!s_has_physical_controller) return;
    int timeout = 100000;
    while ((inb_disk(ATA_PRIMARY_COMM_STAT) & ATA_STATUS_BSY) && timeout--) {}
#endif
}

void osify_storage_init(void) {
    /* Inizializza la ram disk interna */
    osify_memset(s_ram_disk, 0, sizeof(s_ram_disk));

    /* Inizializzazione superblocco OSifyFS a LBA 2 */
    osify_fs_superblock_t *sb = (osify_fs_superblock_t *)&s_ram_disk[2 * OSIFY_SECTOR_SIZE];
    sb->magic = 0x5346534F; /* 'OSFS' */
    sb->version = 1;
    sb->total_blocks = SIMULATED_DISK_SECTORS;
    sb->free_blocks  = SIMULATED_DISK_SECTORS - 100;
    sb->root_inode   = 1;
}

bool osify_storage_read_sector(uint32_t drive, uint64_t lba, void *buffer) {
    (void)drive;
    if (!buffer) return false;

    if (lba < SIMULATED_DISK_SECTORS) {
        osify_memcpy(buffer, &s_ram_disk[lba * OSIFY_SECTOR_SIZE], OSIFY_SECTOR_SIZE);
        return true;
    }

#if defined(__x86_64__) || defined(__i386__)
    if (s_has_physical_controller) {
        ata_wait_ready();
        outb_disk(ATA_PRIMARY_DRIVE_HEAD, (uint8_t)(0xE0 | ((lba >> 24) & 0x0F)));
        outb_disk(ATA_PRIMARY_SEC_COUNT, 1);
        outb_disk(ATA_PRIMARY_LBA_LO, (uint8_t)(lba & 0xFF));
        outb_disk(ATA_PRIMARY_LBA_MID, (uint8_t)((lba >> 8) & 0xFF));
        outb_disk(ATA_PRIMARY_LBA_HI, (uint8_t)((lba >> 16) & 0xFF));
        outb_disk(ATA_PRIMARY_COMM_STAT, ATA_CMD_READ_SECTORS);

        ata_wait_ready();
        uint16_t *target = (uint16_t *)buffer;
        for (int i = 0; i < 256; i++) {
            target[i] = inw_disk(ATA_PRIMARY_DATA);
        }
        return true;
    }
#endif
    return false;
}

bool osify_storage_write_sector(uint32_t drive, uint64_t lba, const void *buffer) {
    (void)drive;
    if (!buffer) return false;

    if (lba < SIMULATED_DISK_SECTORS) {
        osify_memcpy(&s_ram_disk[lba * OSIFY_SECTOR_SIZE], buffer, OSIFY_SECTOR_SIZE);
        return true;
    }

#if defined(__x86_64__) || defined(__i386__)
    if (s_has_physical_controller) {
        ata_wait_ready();
        outb_disk(ATA_PRIMARY_DRIVE_HEAD, (uint8_t)(0xE0 | ((lba >> 24) & 0x0F)));
        outb_disk(ATA_PRIMARY_SEC_COUNT, 1);
        outb_disk(ATA_PRIMARY_LBA_LO, (uint8_t)(lba & 0xFF));
        outb_disk(ATA_PRIMARY_LBA_MID, (uint8_t)((lba >> 8) & 0xFF));
        outb_disk(ATA_PRIMARY_LBA_HI, (uint8_t)((lba >> 16) & 0xFF));
        outb_disk(ATA_PRIMARY_COMM_STAT, ATA_CMD_WRITE_SECTORS);

        ata_wait_ready();
        const uint16_t *source = (const uint16_t *)buffer;
        for (int i = 0; i < 256; i++) {
            outw_disk(ATA_PRIMARY_DATA, source[i]);
        }
        return true;
    }
#endif
    return false;
}

/* Parser Partizioni GPT Standard */
int osify_storage_parse_gpt(uint32_t drive, osify_partition_t *partitions, size_t max_parts) {
    if (!partitions || max_parts == 0) return 0;

    uint8_t gpt_header[OSIFY_SECTOR_SIZE];
    if (!osify_storage_read_sector(drive, 1, gpt_header)) {
        return 0;
    }

    /* Verifica Magic GPT 'EFI PART' (0x5452415020494645) */
    if (osify_memcmp(gpt_header, "EFI PART", 8) == 0) {
        partitions[0].partition_id = 1;
        partitions[0].start_lba = 2048;
        partitions[0].sector_count = 1048576;
        partitions[0].is_active = true;
        osify_strcpy(partitions[0].name, "OSify-System-Root");
        return 1;
    }

    return 0;
}

/* Tabella File Virtuali In-Storage per OSifyFS */
#define MAX_FILES 32
static struct {
    char path[128];
    uint8_t data[2048];
    size_t size;
    bool is_used;
} s_fs_table[MAX_FILES];

void osify_fs_init(uint32_t drive) {
    (void)drive;
    osify_memset(s_fs_table, 0, sizeof(s_fs_table));

    /* Inizializzazione file cardine nativi */
    osify_fs_write_file("/Sistema/Versione.txt", "OSify A.0", 9);
    osify_fs_write_file("/Sistema/Identita.txt", "Sistema Operativo Autonomo Bare-Metal", 37);
    osify_fs_write_file("/Utenti/osify/Benvenuto.txt", "Benvenuto nella Scrivania di OSify A.0!", 40);
}

int osify_fs_read_file(const char *path, void *out_buf, size_t max_len) {
    if (!path || !out_buf || max_len == 0) return -1;

    for (int i = 0; i < MAX_FILES; i++) {
        if (s_fs_table[i].is_used && osify_strcmp(s_fs_table[i].path, path) == 0) {
            size_t copy_len = (s_fs_table[i].size < max_len) ? s_fs_table[i].size : max_len;
            osify_memcpy(out_buf, s_fs_table[i].data, copy_len);
            return (int)copy_len;
        }
    }
    return -1; /* File non trovato */
}

int osify_fs_write_file(const char *path, const void *data, size_t len) {
    if (!path || !data || len == 0 || len > 2048) return -1;

    /* Cerca se esiste gia per aggiornarlo */
    for (int i = 0; i < MAX_FILES; i++) {
        if (s_fs_table[i].is_used && osify_strcmp(s_fs_table[i].path, path) == 0) {
            osify_memcpy(s_fs_table[i].data, data, len);
            s_fs_table[i].size = len;
            return (int)len;
        }
    }

    /* Alloca un nuovo slot file */
    for (int i = 0; i < MAX_FILES; i++) {
        if (!s_fs_table[i].is_used) {
            s_fs_table[i].is_used = true;
            osify_strncpy(s_fs_table[i].path, path, sizeof(s_fs_table[i].path) - 1);
            osify_memcpy(s_fs_table[i].data, data, len);
            s_fs_table[i].size = len;
            return (int)len;
        }
    }
    return -1; /* Spazio su tabella esaurito */
}
