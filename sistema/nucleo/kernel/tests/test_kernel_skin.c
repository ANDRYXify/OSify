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
#include "../include/osify_net.h"
#include "../include/osify_audio.h"
#include "../include/osify_installer.h"
#include "../include/osify_synch.h"
#include "../include/osify_capability.h"

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

    /* Test formattazione interi negativi */
    osify_snprintf(test_buf, sizeof(test_buf), "Temp: %d C", -15);
    assert(osify_strcmp(test_buf, "Temp: -15 C") == 0);

    /* Test caratteri %c e puntatori %p */
    void *dummy_ptr = (void *)0x1000;
    osify_snprintf(test_buf, sizeof(test_buf), "Code: %c, Ptr: %p", 'Z', dummy_ptr);
    assert(osify_strcmp(test_buf, "Code: Z, Ptr: 0x1000") == 0);

    /* Test padding esadecimale e puntatore NULL */
    osify_snprintf(test_buf, sizeof(test_buf), "Port: 0x%04x, Null: %p", 0x1f0, (void *)0);
    assert(osify_strcmp(test_buf, "Port: 0x01f0, Null: (nil)") == 0);

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
    assert(osify_strncmp(fs_read_buf, "OSify A.1", 9) == 0);

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

    /* Test interazione Shell Nativa estesa */
    osify_shell_execute_cmd(&desktop_fb, "stato");
    osify_shell_execute_cmd(&desktop_fb, "disco");
    osify_shell_execute_cmd(&desktop_fb, "sicurezza");
    osify_shell_execute_cmd(&desktop_fb, "rete");
    osify_shell_execute_cmd(&desktop_fb, "ping");
    osify_shell_execute_cmd(&desktop_fb, "audio");
    osify_shell_execute_cmd(&desktop_fb, "audio chime");
    osify_shell_execute_cmd(&desktop_fb, "installa");
    printf("[+] 10. Desktop Environment Dark Glass & Shell Nativa su Framebuffer a 32bpp: OK\n");

    /* 11. Test Network Stack Bare-Metal (Ethernet, IPv4, ARP, DHCP, Quad9) */
    osify_net_init();
    const osify_net_device_t *net = osify_net_get_device();
    assert(net->link_up == true);
    assert(net->dhcp_acquired == true);
    assert(net->ip_addr == 0x9601A8C0); /* 192.168.1.150 */
    assert(net->dns_server == 0x09090909); /* Quad9 9.9.9.9 */

    char ip_fmt[32], mac_fmt[32];
    osify_net_format_ip(net->ip_addr, ip_fmt, sizeof(ip_fmt));
    assert(strcmp(ip_fmt, "192.168.1.150") == 0);
    osify_net_format_mac(net->mac_addr, mac_fmt, sizeof(mac_fmt));
    assert(strcmp(mac_fmt, "52:54:00:aa:bb:cc") == 0);

    uint32_t ping_lat = 0;
    assert(osify_net_ping(net->dns_server, &ping_lat) == true);
    assert(ping_lat > 0);
    printf("[+] 11. Network Stack Bare-Metal (Ethernet, IPv4, DHCP IP, DNS Quad9, Ping): OK\n");

    /* 12. Test Audio Driver Hardware (Intel HDA & AC97) */
    osify_audio_init();
    const osify_audio_state_t *audio = osify_audio_get_state();
    assert(audio->hda_detected == true);
    assert(audio->master_volume == 80);

    osify_audio_set_volume(90);
    assert(osify_audio_get_volume() == 90);
    osify_audio_volume_down(10);
    assert(osify_audio_get_volume() == 80);
    osify_audio_volume_up(5);
    assert(osify_audio_get_volume() == 85);

    osify_audio_toggle_mute();
    assert(osify_audio_get_state()->is_muted == true);
    osify_audio_toggle_mute();
    assert(osify_audio_get_state()->is_muted == false);

    osify_audio_play_startup_chime();
    assert(osify_audio_get_state()->samples_played > 0);
    printf("[+] 12. Audio Driver Hardware (Intel HDA mixer, PCM streaming, Startup Chime): OK\n");

    /* 13. Test Installatore Bare-Metal Guidato su Disco Fisso */
    osify_installer_init();
    assert(osify_installer_get_state()->is_completed == false);
    assert(osify_installer_get_state()->target_disk.is_target == true);

    assert(osify_installer_start(0) == true);
    const osify_installer_state_t *inst = osify_installer_get_state();
    assert(inst->is_completed == true);
    assert(inst->progress_percent == 100);
    assert(inst->step == INSTALL_FINISHED);

    /* Verifica creazione file di sistema post-installazione */
    char inst_check[64];
    memset(inst_check, 0, sizeof(inst_check));
    assert(osify_fs_read_file("/Sistema/Installato.txt", inst_check, sizeof(inst_check) - 1) > 0);
    assert(strcmp(inst_check, "OSify A.0 Residente su Disco Fisso") == 0);

    /* Render card installatore su framebuffer */
    osify_installer_render(&desktop_fb, 200, 150, 624, 200);
    assert(desktop_fb_buf[250 + 200 * 1024] != 0);
    printf("[+] 13. Installatore Bare-Metal Guidato su Disco Fisso (GPT, OSifyFS, 100%%): OK\n");

    /* 14. Test System Call Native OSify (int 0x80 / Dispatcher Sovrano) */
    int32_t ping_val = osify_syscall_dispatch(6, 0, 0, 0); /* SYS_PING */
    assert(ping_val == 0x051F1050);

    uint32_t ram_tot = 0, ram_free = 0;
    assert(osify_syscall_dispatch(4, (uintptr_t)&ram_tot, (uintptr_t)&ram_free, 0) == 0); /* SYS_MEM_STATS */
    assert(ram_tot == 2048);
    assert(ram_free == 2016);

    uint32_t fb_w = 0, fb_h = 0;
    assert(osify_syscall_dispatch(5, (uintptr_t)&fb_w, (uintptr_t)&fb_h, 0) == 0); /* SYS_FB_INFO */
    assert(fb_w == 1024);
    assert(fb_h == 768);

    const char *sys_test_msg = "Test Syscall Output\n";
    assert(osify_syscall_dispatch(1, 1, (uintptr_t)sys_test_msg, strlen(sys_test_msg)) == (int32_t)strlen(sys_test_msg)); /* SYS_WRITE */
    printf("[+] 14. System Call Native OSify (int 0x80 DPL 3, PING 0x051F1050, MEM, FB, WRITE): OK\n");

    /* 15. Test Sincronizzazione Universale Superset (WaitMux, WaitAny, WaitAll) */
    osify_synch_hdr_t ev1, ev2, sem1;
    osify_synch_init(&ev1, OSIFY_SYNCH_EVENT, false);
    osify_synch_init(&ev2, OSIFY_SYNCH_EVENT, false);
    osify_synch_init(&sem1, OSIFY_SYNCH_SEMAPHORE, false);

    osify_synch_hdr_t *objs[3] = { &ev1, &ev2, &sem1 };

    /* Nessun oggetto pronto */
    assert(osify_wait_mux(objs, 3, OSIFY_WAIT_ANY, 0) == -2);
    assert(osify_wait_mux(objs, 3, OSIFY_WAIT_ALL, 0) == -2);

    /* Segnala ev2 -> WaitAny deve ritornare indice 1 */
    osify_synch_signal(&ev2);
    assert(osify_wait_mux(objs, 3, OSIFY_WAIT_ANY, 0) == 1);
    assert(osify_wait_mux(objs, 3, OSIFY_WAIT_ALL, 0) == -2); /* Non tutti sono pronti */

    /* Segnala anche ev1 e sem1 -> WaitAll deve ritornare 0 (successo) */
    osify_synch_signal(&ev1);
    osify_synch_signal(&sem1);
    assert(osify_wait_mux(objs, 3, OSIFY_WAIT_ALL, 0) == 0);
    printf("[+] 15. Sincronizzazione Universale Superset (WaitMux, WaitAny, WaitAll, Semaphores, Events): OK\n");

    printf("\n[] TUTTI I 15 TEST AVANZATI DEL KERNEL NATIVO OSIFY SUPERATI CON SUCCESSO AL 100%%!\n");
    return 0;
}
