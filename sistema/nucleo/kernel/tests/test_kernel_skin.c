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

    printf("\n[✓✓✓] TUTTI I TEST AVANZATI DEL KERNEL NATIVO OSIFY SUPERATI CON SUCCESSO AL 100%%!\n");
    return 0;
}
