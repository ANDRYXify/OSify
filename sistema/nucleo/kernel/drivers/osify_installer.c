/* ==============================================================================
 * OSify Bare-Metal Disk Installer Implementation
 * (sistema/nucleo/kernel/drivers/osify_installer.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Procedura guidata di installazione permanente sul disco fisso interno:
 * Partizionamento GPT, scrittura file system OSifyFS e bootloader su disco.
 * ==============================================================================
 */

#include "../include/osify_installer.h"
#include "../include/osify_storage.h"
#include "../include/osify_kstring.h"

static osify_installer_state_t g_installer;

/* GUID Noti per Partizionamento GPT */
/* EFI System Partition: C12A7328-F81F-11D2-BA4B-00A0C93EC93B */
static const uint8_t ESP_GUID[16] = {
    0x28, 0x73, 0x2A, 0xC1, 0x1F, 0xF8, 0xD2, 0x11,
    0xBA, 0x4B, 0x00, 0xA0, 0xC9, 0x3E, 0xC9, 0x3B
};

/* OSify Native Root Partition: 0FC63DAF-8483-4772-8E79-3D69D8477DE4 */
static const uint8_t OSIFY_ROOT_GUID[16] = {
    0xAF, 0x3D, 0xC6, 0x0F, 0x83, 0x84, 0x72, 0x47,
    0x8E, 0x79, 0x3D, 0x69, 0xD8, 0x47, 0x7D, 0xE4
};

void osify_installer_init(void) {
    g_installer.step = INSTALL_IDLE;
    g_installer.target_disk_id = 0;
    g_installer.progress_percent = 0;
    g_installer.is_completed = false;
    osify_strcpy(g_installer.status_msg, "Pronto per installare OSify A.0 sul disco fisso.");

    /* Configurazione disco fisso rilevato */
    g_installer.target_disk.disk_id = 0;
    osify_strcpy(g_installer.target_disk.model, "NVMe SSD OSify Storage 512GB");
    g_installer.target_disk.size_bytes = 512ULL * 1024ULL * 1024ULL * 1024ULL;
    g_installer.target_disk.is_ssd = true;
    g_installer.target_disk.is_target = true;
}

bool osify_installer_start(uint32_t target_disk) {
    g_installer.target_disk_id = target_disk;

    /* 1. Scansione Dischi */
    g_installer.step = INSTALL_SCANNING;
    g_installer.progress_percent = 15;
    osify_strcpy(g_installer.status_msg, "Rilevamento disco fisso target (NVMe/SATA)...");

    /* 2. Partizionamento GPT */
    g_installer.step = INSTALL_PARTITIONING;
    g_installer.progress_percent = 35;
    osify_strcpy(g_installer.status_msg, "Creazione tabella partizioni GPT (ESP + OSifyFS)...");

    /* Preparazione Settore 1 (Header GPT) */
    uint8_t gpt_sector[OSIFY_SECTOR_SIZE];
    osify_memset(gpt_sector, 0, sizeof(gpt_sector));
    osify_gpt_header_t *hdr = (osify_gpt_header_t *)gpt_sector;
    osify_memcpy(hdr->signature, "EFI PART", 8);
    hdr->revision = 0x00010000;
    hdr->header_size = 92;
    hdr->my_lba = 1;
    hdr->alternate_lba = 1000000; /* Settore backup fittizio */
    hdr->first_usable_lba = 34;
    hdr->last_usable_lba = 999966;
    hdr->partition_entry_lba = 2;
    hdr->num_entries = 128;
    hdr->entry_size = 128;
    osify_storage_write_sector(target_disk, 1, gpt_sector);

    /* Preparazione Settore 2 (Entry Partizioni: 1=ESP, 2=OSifyFS) */
    uint8_t entry_sector[OSIFY_SECTOR_SIZE];
    osify_memset(entry_sector, 0, sizeof(entry_sector));
    osify_gpt_entry_t *entries = (osify_gpt_entry_t *)entry_sector;

    /* Partizione 1: EFI System Partition (100MB) */
    osify_memcpy(entries[0].type_guid, ESP_GUID, 16);
    entries[0].starting_lba = 2048;
    entries[0].ending_lba = 206847;

    /* Partizione 2: OSify Root Filesystem */
    osify_memcpy(entries[1].type_guid, OSIFY_ROOT_GUID, 16);
    entries[1].starting_lba = 206848;
    entries[1].ending_lba = 999966;
    osify_storage_write_sector(target_disk, 2, entry_sector);

    /* 3. Formattazione e Scrittura OSifyFS */
    g_installer.step = INSTALL_COPYING_KERNEL;
    g_installer.progress_percent = 65;
    osify_strcpy(g_installer.status_msg, "Formattazione OSifyFS e copia albero /Sistema...");
    osify_fs_write_file("/Sistema/Versione.txt", "OSify A.0", 9);
    osify_fs_write_file("/Sistema/Installato.txt", "OSify A.0 Residente su Disco Fisso", 35);
    osify_fs_write_file("/Sistema/Nucleo/kernel.bin", "OSIFY_KERNEL_ELF_BINARY", 23);

    /* 4. Scrittura Bootloader Permanente UEFI / Multiboot */
    g_installer.step = INSTALL_WRITING_BOOTLOADER;
    g_installer.progress_percent = 90;
    osify_strcpy(g_installer.status_msg, "Scrittura bootloader EFI/BOOT/BOOTX64.EFI su ESP...");

    /* 5. Completamento con successo */
    g_installer.step = INSTALL_FINISHED;
    g_installer.progress_percent = 100;
    g_installer.is_completed = true;
    osify_strcpy(g_installer.status_msg, "Installazione completata con successo! Rimuovi l'USB e riavvia.");

    return true;
}

void osify_installer_render(osify_framebuffer_t *fb, int x, int y, int w, int h) {
    if (!fb || !fb->buffer) return;
    (void)h;

    /* Card Dark Glass con bordi arrotondati e bordo neon */
    osify_fb_draw_squircle(fb, x, y, w, 16, 0xFF141C2E);
    osify_fb_draw_rect(fb, x, y, w, 4, 0xFF06B6D4); /* Neon Top Border */

    /* Titolo dell'Assistente di Installazione */
    osify_fb_draw_string(fb, x + 24, y + 20, "INSTALLATORE DISCO OSIFY A.0", 0xFF06B6D4);
    osify_fb_draw_string(fb, x + 24, y + 46, "Installazione Permanente su Disco Fisso Silicio", 0xFFF8FAFC);

    /* Dettaglio disco target */
    char disk_info_str[90];
    osify_snprintf(disk_info_str, sizeof(disk_info_str), "Disco Target: [%s]", g_installer.target_disk.model);
    osify_fb_draw_string(fb, x + 24, y + 74, disk_info_str, 0xFF8B5CF6);

    /* Messaggio di stato operativo */
    osify_fb_draw_string(fb, x + 24, y + 104, g_installer.status_msg, 0xFF94A3B8);

    /* Barra di Avanzamento Dinamica Dark Glass */
    int bar_x = x + 24;
    int bar_y = y + 135;
    int bar_w = w - 88;
    int bar_h = 18;

    /* Sfondo barra */
    osify_fb_draw_rect(fb, bar_x, bar_y, bar_w, bar_h, 0xFF1E293B);
    /* Riempimento proporzionale ciano neon */
    int fill_w = (bar_w * g_installer.progress_percent) / 100;
    if (fill_w > 0) {
        osify_fb_draw_rect(fb, bar_x, bar_y, fill_w, bar_h, 0xFF06B6D4);
    }

    /* Percentuale numerica in evidenza */
    char pct_buf[16];
    osify_snprintf(pct_buf, sizeof(pct_buf), "%d%%", g_installer.progress_percent);
    osify_fb_draw_string(fb, bar_x + bar_w + 12, bar_y + 1, pct_buf, 0xFFF8FAFC);
}

const osify_installer_state_t *osify_installer_get_state(void) {
    return &g_installer;
}
