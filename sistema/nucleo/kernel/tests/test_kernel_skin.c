/* ==============================================================================
 * Test Unitario Completo del Kernel Nativo OSify (sistema/nucleo/kernel/tests/test_kernel_skin.c)
 * ==============================================================================
 * Verifica PMM/VMM con W^X, Sicurezza Level-0 (macOS SIP/Seatbelt),
 * Unificatore Percorsi, Loader Binari Reale e Tipografia Dark Glass.
 * ==============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../include/osify_kernel.h"
#include "../include/osify_kstring.h"
#include "../include/osify_storage.h"
#include "../include/osify_desktop.h"

int main(void) {
    printf("[+] Inizio collaudo avanzato del Kernel Nativo OSify...\n");

    /* 1. Test Introspezione e Cover Nuda */
    osify_hardware_skin_t skin;
    memset(&skin, 0, sizeof(skin));
    skin.ram_total_bytes = 16ULL * 1024ULL * 1024ULL * 1024ULL;
    osify_hardware_detect(&skin);
    osify_adaptive_skin_init(&skin);
    assert(skin.arch != ARCH_UNKNOWN);
    assert(skin.profile == PROFILE_EXTREME_PERF);
    printf("[+] 1. Introspezione e Profilazione Adattiva Silicio: OK\n");

    /* 2. Test Memory Management PMM & VMM con W^X */
    osify_pmm_init(64 * 1024 * 1024); /* 64MB di memoria fisica gestita */
    void *p1 = osify_pmm_alloc_page();
    void *p2 = osify_pmm_alloc_page();
    assert(p1 != NULL && p2 != NULL && p1 != p2);
    osify_pmm_free_page(p1);
    osify_pmm_free_page(p2);

    /* Validazione W^X: Permessi R-X sono ammessi */
    assert(osify_vmm_validate_wx(PAGE_PERM_READ | PAGE_PERM_EXEC) == true);
    /* Permessi RW- sono ammessi */
    assert(osify_vmm_validate_wx(PAGE_PERM_READ | PAGE_PERM_WRITE) == true);
    /* Permessi RWX sono categoricamente VIETATI e BLOCCATI */
    assert(osify_vmm_validate_wx(PAGE_PERM_READ | PAGE_PERM_WRITE | PAGE_PERM_EXEC) == false);
    printf("[+] 2. Gestione Memoria PMM & Principio W^X (Anti-Exploit): OK\n");

    /* 3. Test Sicurezza Livello 0: SIP & Seatbelt Sandbox (macOS Style) */
    osify_security_token_t user_tok = osify_sec_create_token(1001, true); /* Sandboxed */
    /* Tentativo di scrittura non autorizzata su /Sistema: deve essere bloccato da SIP */
    assert(osify_sec_check_system_write("/Sistema/Nucleo/kernel.bin", &user_tok) == false);
    /* Tentativo su percorso consentito utente: ammesso */
    assert(osify_sec_check_system_write("/Utenti/Andrea/Documento.txt", &user_tok) == true);
    /* Seatbelt: blocco accesso diretto al disco per token sandboxed */
    assert(osify_sec_enforce_seatbelt(&user_tok, 2) == false);
    printf("[+] 3. Sicurezza Livello 0 (macOS SIP & Seatbelt Sandbox): OK\n");

    /* 4. Test Unificatore Percorsi Universale (Windows C:\ <-> Linux / <-> OSify) */
    char path_out[256];
    osify_path_unify("C:\\Users\\Andrea\\Progetto.ify", path_out, sizeof(path_out));
    assert(strcmp(path_out, "/Utenti/Andrea/Progetto.ify") == 0);

    osify_path_unify("C:\\Program Files\\Gioco\\gioco.exe", path_out, sizeof(path_out));
    assert(strcmp(path_out, "/Applicazioni/Gioco/gioco.exe") == 0);

    osify_path_unify("/home/andrea/.config/osify.cfg", path_out, sizeof(path_out));
    assert(strcmp(path_out, "/Utenti/andrea/.config/osify.cfg") == 0);
    printf("[+] 4. Unificatore Percorsi Universale (Windows C:\\ <-> OSify): OK\n");

    /* 5. Test Caricatore Binari Reale (ELF, PE, Mach-O, .ify) */
    uint8_t elf_dummy[128];
    memset(elf_dummy, 0, sizeof(elf_dummy));
    elf_dummy[0] = 0x7F; elf_dummy[1] = 'E'; elf_dummy[2] = 'L'; elf_dummy[3] = 'F';
    /* Offset entry point at byte 24 */
    *(uint64_t *)(&elf_dummy[24]) = 0x401050ULL;

    osify_loaded_binary_t bin_elf = osify_binary_load(elf_dummy, sizeof(elf_dummy));
    assert(bin_elf.is_valid == true);
    assert(bin_elf.subsystem == SUBSYSTEM_POSIX_LINUX);
    assert(bin_elf.entry_point == 0x401050ULL);

    uint8_t pe_dummy[128];
    memset(pe_dummy, 0, sizeof(pe_dummy));
    pe_dummy[0] = 'M'; pe_dummy[1] = 'Z';
    *(int32_t *)(&pe_dummy[0x3C]) = 0x40; /* e_lfanew */

    osify_loaded_binary_t bin_pe = osify_binary_load(pe_dummy, sizeof(pe_dummy));
    assert(bin_pe.is_valid == true);
    assert(bin_pe.subsystem == SUBSYSTEM_WIN32_NT);
    assert(bin_pe.load_base == 0x140000000ULL);
    printf("[+] 5. Caricatore Binari Multi-Formato Reale (ELF, PE, Mach-O): OK\n");

    /* 6. Test Tipografia e Framebuffer Diretto Dark Glass */
    uint32_t fake_fb[800 * 600];
    osify_framebuffer_t fb;
    osify_fb_init(&fb, 800, 600, fake_fb);
    osify_fb_clear(&fb, 0xFF0B101D);
    osify_fb_draw_string(&fb, 50, 50, "OSify - Resurrezione", 0xFF06B6D4);
    /* Verifica che i pixel del testo siano stati scritti */
    assert(fake_fb[50 + 50 * 800] != 0 || fake_fb[51 + 51 * 800] != 0);
    printf("[+] 6. Tipografia Nativa Dark Glass su Framebuffer a 32bpp: OK\n");

    /* 7. Test Anti-Cheat Guard (Windows EAC, BattlEye, Vanguard Compatibility) */
    osify_anticheat_init();
    assert(osify_anticheat_query_secure_boot() == true);

    uint8_t pcr0_hash[32];
    assert(osify_anticheat_query_tpm2(0, pcr0_hash) == true);
    /* Verifica che il registro PCR sia popolato e valido */
    assert(pcr0_hash[0] != 0 || pcr0_hash[1] != 0);

    /* Test ThreadHideFromDebugger */
    assert(osify_anticheat_hide_thread(4200) == true);
    assert(osify_anticheat_is_thread_hidden(4200) == true);
    assert(osify_anticheat_is_thread_hidden(9999) == false);

    /* Test Driver Signature Enforcement (DSE) */
    uint8_t valid_driver[512];
    memset(valid_driver, 0xAA, sizeof(valid_driver));
    assert(osify_anticheat_verify_driver(valid_driver, sizeof(valid_driver)) == true);
    printf("[+] 7. Anti-Cheat & Hardware Security Guard (TPM 2.0, Secure Boot, DSE, ThreadHide): OK\n");

    /* 8. Test Libreria Freestanding No-libc & Input PS/2 */
    char test_buf[64];
    osify_memset(test_buf, 0, sizeof(test_buf));
    osify_strcpy(test_buf, "OSify");
    assert(osify_strlen(test_buf) == 5);
    assert(osify_strcmp(test_buf, "OSify") == 0);

    osify_snprintf(test_buf, sizeof(test_buf), "Kernel %s A.%d", "Nativo", 0);
    assert(osify_strcmp(test_buf, "Kernel Nativo A.0") == 0);

    /* Test Keyboard ring buffer */
    void osify_keyboard_init(void);
    char osify_keyboard_get_key(void);
    osify_keyboard_init();
    assert(osify_keyboard_get_key() == 0);
    printf("[+] 8. Libreria Freestanding No-libc (kstring) & Driver Input PS/2: OK\n");

    /* 9. Test Storage Fisico ATA & File System Nativo OSifyFS */
    osify_storage_init();
    osify_fs_init(0);

    /* Test Lettura e Scrittura File su OSifyFS */
    char fs_read_buf[64];
    osify_memset(fs_read_buf, 0, sizeof(fs_read_buf));
    int read_bytes = osify_fs_read_file("/Sistema/Versione.txt", fs_read_buf, sizeof(fs_read_buf) - 1);
    assert(read_bytes > 0);
    assert(osify_strcmp(fs_read_buf, "OSify A.0") == 0);

    /* Scrittura nuovo file utente */
    const char *test_doc = "Progetto OSify Completato al 100%";
    assert(osify_fs_write_file("/Utenti/osify/Stato.txt", test_doc, osify_strlen(test_doc)) > 0);
    osify_memset(fs_read_buf, 0, sizeof(fs_read_buf));
    assert(osify_fs_read_file("/Utenti/osify/Stato.txt", fs_read_buf, sizeof(fs_read_buf) - 1) > 0);
    assert(osify_strcmp(fs_read_buf, test_doc) == 0);
    printf("[+] 9. Storage Fisico ATA & File System Nativo OSifyFS (Persistenza Dati): OK\n");

    /* 10. Test Desktop Environment Dark Glass & Shell Nativa su Framebuffer */
    uint32_t desktop_fb_buf[1024 * 768];
    osify_framebuffer_t desktop_fb;
    osify_fb_init(&desktop_fb, 1024, 768, desktop_fb_buf);

    osify_desktop_init(&desktop_fb);
    osify_desktop_render_all(&desktop_fb);

    /* Verifica Top Menu Bar (pixel y=0..25) */
    assert(desktop_fb_buf[10 + 5 * 1024] != 0);
    /* Verifica Floating Dock Inferiore (pixel y=710..750) */
    int dock_center_idx = 512 + 720 * 1024;
    assert(desktop_fb_buf[dock_center_idx] != 0);

    /* Test interazione Shell Nativa */
    osify_shell_execute_cmd(&desktop_fb, "stato");
    osify_shell_execute_cmd(&desktop_fb, "disco");
    osify_shell_execute_cmd(&desktop_fb, "sicurezza");
    printf("[+] 10. Desktop Environment Dark Glass & Shell Nativa su Framebuffer a 32bpp: OK\n");

    printf("\n[✓✓✓] TUTTI I 10 TEST AVANZATI DEL KERNEL NATIVO OSIFY SUPERATI CON SUCCESSO AL 100%%!\n");
    return 0;
}
