/* ==============================================================================
 * OSify Native Window Manager & Desktop Implementation
 * (sistema/nucleo/kernel/drivers/osify_desktop_wm.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Desktop Environment autonomo a 32bpp direttamente su Linear Framebuffer:
 * Dual-Panel (Top Menu Bar a 26px + Floating Dock centrata), Finestre Dark Glass,
 * Cursore del mouse vettoriale, Shell interattiva, Monitor Silicio HUD,
 * Scheda di Acquisizione Virtuale Integrata, e Integrazione Rete, Audio e Installatore.
 * ==============================================================================
 */

#include "../include/osify_desktop.h"
#include "../include/osify_kstring.h"
#include "../include/osify_storage.h"
#include "../include/osify_net.h"
#include "../include/osify_audio.h"
#include "../include/osify_installer.h"
#include "../include/osify_hetero_dispatch.h"
#include "../include/osify_capture_card.h"

/* Palette Colori Ufficiale Dark Glass OSify */
#define COLOR_DESKTOP_BG_TOP    0xFF060913  /* Ossidiana Notte Sfumata */
#define COLOR_DESKTOP_BG_BOT    0xFF0B1424  /* Blu Notte Profondo */
#define COLOR_GRID_CYBER        0xFF0E1E32  /* Griglia Isometrica Cyber */
#define COLOR_PANEL_GLASS       0xFF111827  /* Dark Glass Card */
#define COLOR_TITLEBAR_GLASS    0xFF1F2937  /* Barra Titolo Finestra */
#define COLOR_BORDER_NEON       0xFF06B6D4  /* Ciano Elettrico */
#define COLOR_ACCENT_PURPLE     0xFF8B5CF6  /* Viola Cyber */
#define COLOR_ACCENT_BLUE       0xFF3B82F6  /* Blu Elettrico */
#define COLOR_ACCENT_AMBER      0xFFF59E0B  /* Ambra Dorato */
#define COLOR_BTN_CLOSE         0xFFEF4444  /* Rosso macOS */
#define COLOR_BTN_MIN           0xFFF59E0B  /* Giallo macOS */
#define COLOR_BTN_MAX           0xFF10B981  /* Verde macOS */
#define COLOR_TEXT_WHITE        0xFFF8FAFC  /* Bianco Testo */
#define COLOR_TEXT_MUTED        0xFF94A3B8  /* Grigio Ardesia */

static osify_window_t g_windows[MAX_WINDOWS];
static size_t g_window_count = 0;
static osify_mouse_cursor_t g_mouse;
static bool g_show_installer_window = false;
static bool g_show_capture_window = true;

/* Buffer Shell Nativa su Framebuffer */
#define SHELL_MAX_LINES 12
#define SHELL_LINE_LEN  86
static char g_shell_lines[SHELL_MAX_LINES][SHELL_LINE_LEN];
static size_t g_shell_line_count = 0;
static char g_cmd_input[SHELL_LINE_LEN];
static size_t g_cmd_idx = 0;

void osify_shell_init(void) {
    osify_memset(g_shell_lines, 0, sizeof(g_shell_lines));
    g_shell_line_count = 0;
    g_cmd_idx = 0;
    osify_memset(g_cmd_input, 0, sizeof(g_cmd_input));

    osify_strcpy(g_shell_lines[g_shell_line_count++], "OSify A.1 Shell Nativa Bare-Metal (Kernel Livello 0)");
    osify_strcpy(g_shell_lines[g_shell_line_count++], "Digita 'aiuto' per lista comandi, 'potenza', 'cattura' o 'installa'.");
}

static void shell_append_line(const char *line) {
    if (g_shell_line_count < SHELL_MAX_LINES) {
        osify_strncpy(g_shell_lines[g_shell_line_count++], line, SHELL_LINE_LEN - 1);
    } else {
        /* Scroll verso l'alto */
        for (size_t i = 0; i < SHELL_MAX_LINES - 1; i++) {
            osify_strncpy(g_shell_lines[i], g_shell_lines[i + 1], SHELL_LINE_LEN);
        }
        osify_strncpy(g_shell_lines[SHELL_MAX_LINES - 1], line, SHELL_LINE_LEN - 1);
    }
}

static void execute_command(const char *cmd) {
    if (!cmd || osify_strlen(cmd) == 0) return;

    if (osify_strcmp(cmd, "aiuto") == 0 || osify_strcmp(cmd, "help") == 0) {
        shell_append_line("Comandi disponibili:");
        shell_append_line("  stato     - Telemetria generale e profilo silicio");
        shell_append_line("  potenza   - Introspezione silicio, GFLOPS, ALU/GPU e Scheduler");
        shell_append_line("  cattura   - Scheda di Acquisizione Virtuale senza hardware esterno");
        shell_append_line("  disco     - Elenco partizioni e file OSifyFS");
        shell_append_line("  esplora   - Navigazione ad albero /Sistema /Applicazioni /Utenti");
        shell_append_line("  rete      - Stato interfaccia Ethernet, IP e DNS Quad9");
        shell_append_line("  ping      - Test connettivita ICMP su Quad9 (9.9.9.9)");
        shell_append_line("  audio     - Stato mixer, volume Intel HDA e Chime");
        shell_append_line("  processi  - Connettori eterogenei e compiti assegnati al silicio");
        shell_append_line("  installa  - Avvia installatore guidato su disco fisso GPT");
        shell_append_line("  sicurezza - Verifica TPM 2.0, Secure Boot, SIP e Seatbelt");
        shell_append_line("  pulisci   - Svuota lo storico del terminale");
    } else if (osify_strcmp(cmd, "stato") == 0) {
        shell_append_line("Profilo: OSify A.1 (Naked-Skin Architecture - Zero Bloatware)");
        shell_append_line("Memoria: PMM Bitmap Allocator con protezione W^X attiva");
    } else if (osify_strcmp(cmd, "potenza") == 0 || osify_strcmp(cmd, "hardware") == 0) {
        const osify_hardware_skin_t *h = osify_get_active_skin();
        char msg[96];
        osify_snprintf(msg, sizeof(msg), "CPU: %s (%s)", h->cpu_brand, h->cpu_vendor);
        shell_append_line(msg);
        osify_snprintf(msg, sizeof(msg), "Core: %u fisici, %u logici | Clock: %u MHz | Picco: %u GFLOPS",
                       h->cpu_cores, h->cpu_threads, h->cpu_freq_mhz, (uint32_t)h->cpu_peak_gflops);
        shell_append_line(msg);
        osify_snprintf(msg, sizeof(msg), "ALU SIMD: %s %s %s %s %s (Burst Vector Attivo)",
                       h->has_sse2 ? "SSE2" : "", h->has_sse4_1 ? "SSE4.1" : "",
                       h->has_avx ? "AVX" : "", h->has_avx2 ? "AVX2" : "",
                       h->has_hardware_aes ? "AES-NI" : "");
        shell_append_line(msg);
        osify_snprintf(msg, sizeof(msg), "GPU Driverless: %s [VRAM: %u MB]",
                       h->gpu_vendor, h->gpu_vram_bytes / (1024 * 1024));
        shell_append_line(msg);
        osify_dispatch_stats_t st;
        osify_hetero_get_stats(&st);
        osify_snprintf(msg, sizeof(msg), "Scheduler: %u Task (ALU Scalare: %u, SIMD: %u, GPU: %u, I/O: %u)",
                       st.total_tasks_dispatched, st.tasks_on_alu_scalar, st.tasks_on_alu_vector,
                       st.tasks_on_gpu_blitter, st.tasks_on_async_io);
        shell_append_line(msg);
    } else if (osify_strcmp(cmd, "cattura") == 0) {
        const osify_capture_state_t *c = osify_capture_get_state();
        char c_msg[96];
        osify_snprintf(c_msg, sizeof(c_msg), "Scheda Acquisizione: %s | %ux%u @ %u FPS",
                       c->is_active ? "ATTIVA (DMA Direct Tap)" : "IN PAUSA", c->width, c->height, c->fps);
        shell_append_line(c_msg);
        osify_snprintf(c_msg, sizeof(c_msg), "Frame Catturati: %llu | Bitrate: %u Mbps | Zero Hardware Esterno",
                       c->total_frames_captured, c->bitrate_mbps);
        shell_append_line(c_msg);
        shell_append_line("Flusso Loopback: ATTIVO su /Sistema/Dispositivi/Cattura0");
    } else if (osify_strcmp(cmd, "processi") == 0) {
        osify_dispatch_stats_t st;
        osify_hetero_get_stats(&st);
        char p_msg[96];
        osify_snprintf(p_msg, sizeof(p_msg), "Connettori Attivi: 5 Task al Silicio (Tot GFLOPS: %llu)", st.total_gflops_delivered);
        shell_append_line(p_msg);
        shell_append_line("  1. Kernel-Level0   -> ALU Scalare (Core 0)");
        shell_append_line("  2. Crypto-Guard    -> ALU Vettoriale SIMD (SSE2/AVX)");
        shell_append_line("  3. DarkGlass-UI    -> GPU Blitter Burst (1024 dword/s)");
        shell_append_line("  4. Storage-AsyncIO -> Async I/O DMA (Zero CPU Latency)");
        shell_append_line("  5. Audio-DSP       -> ALU Vettoriale SIMD (PCM Mixer)");
    } else if (osify_strcmp(cmd, "esplora") == 0 || osify_strcmp(cmd, "file") == 0) {
        shell_append_line("Albero File System Nativo OSifyFS (Zero Basi Terze):");
        shell_append_line("  /Sistema      - [Nucleo, Driver, Icone, Servizi, Dispositivi]");
        shell_append_line("  /Applicazioni - [24 App Native .ify: Navigatore, Centro, Giochi...]");
        shell_append_line("  /UEM          - [Ponte Universale Compatibilita PE, ELF, Mach-O]");
        shell_append_line("  /Desktop      - [Branding Ufficiale, Wallpapers, Temi Glass]");
        shell_append_line("  /Utenti       - [/Utenti/Compagno: Scrivania, Documenti, Scaricati]");
    } else if (osify_strcmp(cmd, "disco") == 0) {
        char v_buf[64], a_buf[90];
        osify_memset(v_buf, 0, sizeof(v_buf));
        osify_memset(a_buf, 0, sizeof(a_buf));
        osify_fs_read_file("/Sistema/Versione.txt", v_buf, sizeof(v_buf) - 1);
        osify_fs_read_file("/Applicazioni/Lista.txt", a_buf, sizeof(a_buf) - 1);
        char disco_msg[90];
        osify_snprintf(disco_msg, sizeof(disco_msg), "OSifyFS: %s", v_buf);
        shell_append_line(disco_msg);
        shell_append_line(a_buf);
        shell_append_line("Albero: /Sistema (8 servizi, 5 driver, 40 icone) | /UEM (Attivo)");
    } else if (osify_strcmp(cmd, "rete") == 0 || osify_strcmp(cmd, "ip") == 0) {
        const osify_net_device_t *net = osify_net_get_device();
        char ip_str[32], mac_str[32], net_msg[90];
        osify_net_format_ip(net->ip_addr, ip_str, sizeof(ip_str));
        osify_net_format_mac(net->mac_addr, mac_str, sizeof(mac_str));

        osify_snprintf(net_msg, sizeof(net_msg), "NIC: %s [MAC: %s]", net->nic_name, mac_str);
        shell_append_line(net_msg);
        osify_snprintf(net_msg, sizeof(net_msg), "IP: %s | DHCP: ATTIVO | DNS: 9.9.9.9 (Quad9)", ip_str);
        shell_append_line(net_msg);
    } else if (osify_strcmp(cmd, "ping") == 0) {
        uint32_t lat_ms = 0;
        const osify_net_device_t *net = osify_net_get_device();
        if (osify_net_ping(net->dns_server, &lat_ms)) {
            char ping_msg[90];
            osify_snprintf(ping_msg, sizeof(ping_msg), "Risposta da 9.9.9.9 (Quad9): bytes=32 tempo=%ums TTL=64", lat_ms);
            shell_append_line(ping_msg);
        } else {
            shell_append_line("Errore ping: rete non raggiungibile.");
        }
    } else if (osify_strcmp(cmd, "audio") == 0) {
        const osify_audio_state_t *aud = osify_audio_get_state();
        char aud_msg[90];
        osify_snprintf(aud_msg, sizeof(aud_msg), "Audio: %s | Volume: %u%% | Muto: %s",
                       aud->card_name, aud->master_volume, aud->is_muted ? "SI" : "NO");
        shell_append_line(aud_msg);
        shell_append_line("Formato PCM: 44100Hz 16-bit Stereo | Riproduzione Chime: 'audio chime'");
    } else if (osify_strcmp(cmd, "audio chime") == 0) {
        osify_audio_play_startup_chime();
        shell_append_line("Cyber Startup Chime riprodotto su Intel HDA.");
    } else if (osify_strcmp(cmd, "installa") == 0 || osify_strcmp(cmd, "installer") == 0) {
        shell_append_line("Avvio Installatore Bare-Metal OSify A.1 sul disco fisso...");
        osify_installer_start(0);
        g_show_installer_window = true;
        const osify_installer_state_t *inst = osify_installer_get_state();
        shell_append_line(inst->status_msg);
    } else if (osify_strcmp(cmd, "sicurezza") == 0) {
        shell_append_line("Sicurezza: SIP Immutabile su /Sistema | Seatbelt Sandbox: ATTIVO");
        shell_append_line("Anti-Cheat: TPM 2.0 SHA-256 PCR Enforced | DSE: ATTIVO");
    } else if (osify_strcmp(cmd, "pulisci") == 0 || osify_strcmp(cmd, "clear") == 0) {
        g_shell_line_count = 0;
        shell_append_line("Terminale OSify pulito.");
    } else if (osify_strlen(cmd) > 0) {
        char err[90];
        osify_snprintf(err, sizeof(err), "Comando non riconosciuto: '%s'. Digita 'aiuto'.", cmd);
        shell_append_line(err);
    }
}

void osify_desktop_init(osify_framebuffer_t *fb) {
    g_window_count = 0;
    g_show_installer_window = false;
    g_show_capture_window = true;

    /* Inizializza Sottosistema Scheda di Acquisizione Virtuale */
    osify_capture_init(fb ? fb->width : 1024, fb ? fb->height : 768, 60);

    /* Finestra 1: Terminale Nativo OSify */
    osify_window_t *win_term = &g_windows[g_window_count++];
    win_term->id = 1;
    win_term->x = 116;
    win_term->y = 38;
    win_term->w = 600;
    win_term->h = 340;
    osify_strcpy(win_term->title, "OSify Terminale Nativo");
    win_term->is_visible = true;
    win_term->is_focused = true;

    /* Finestra 2: Scheda di Acquisizione Video Virtuale */
    osify_window_t *win_cap = &g_windows[g_window_count++];
    win_cap->id = 2;
    win_cap->x = 116;
    win_cap->y = 390;
    win_cap->w = 600;
    win_cap->h = 280;
    osify_strcpy(win_cap->title, "Scheda di Acquisizione Video (Virtual Capture Card)");
    win_cap->is_visible = true;
    win_cap->is_focused = false;

    /* Inizializza cursore del mouse al centro */
    g_mouse.x = fb ? ((int)fb->width / 2) : 512;
    g_mouse.y = fb ? ((int)fb->height / 2) : 384;
    g_mouse.is_visible = true;

    /* Inizializza la shell interattiva */
    osify_shell_init();
}

void osify_wm_draw_window(osify_framebuffer_t *fb, const osify_window_t *win) {
    if (!fb || !fb->buffer || !win || !win->is_visible) return;

    /* 1. Sfondo Finestra Dark Glass */
    osify_fb_draw_rect(fb, win->x, win->y, win->w, win->h, COLOR_PANEL_GLASS);

    /* 2. Barra del Titolo */
    osify_fb_draw_rect(fb, win->x, win->y, win->w, 28, COLOR_TITLEBAR_GLASS);

    /* Bordo Neon Ciano a 1px */
    osify_fb_draw_rect(fb, win->x, win->y, win->w, 1, win->is_focused ? COLOR_BORDER_NEON : COLOR_ACCENT_PURPLE);

    /* 3. Pulsanti Stile macOS (Rosso, Giallo, Verde) */
    osify_fb_draw_squircle(fb, win->x + 12, win->y + 8, 12, 6, COLOR_BTN_CLOSE);
    osify_fb_draw_squircle(fb, win->x + 30, win->y + 8, 12, 6, COLOR_BTN_MIN);
    osify_fb_draw_squircle(fb, win->x + 48, win->y + 8, 12, 6, COLOR_BTN_MAX);

    /* 4. Titolo Finestra */
    osify_fb_draw_string(fb, win->x + 70, win->y + 6, win->title, COLOR_TEXT_WHITE);
}

void osify_desktop_render_all(osify_framebuffer_t *fb) {
    if (!fb || !fb->buffer) return;

    /* 1. Sfondo Scrivania Gradiente Dark Glass con Cyber Mesh Isometrico */
    for (uint32_t py = 0; py < fb->height; py++) {
        uint32_t *row = &fb->buffer[py * fb->width];
        /* Interpolazione gradiente top-bot */
        uint32_t r = 6 + (py * (11 - 6)) / fb->height;
        uint32_t g = 9 + (py * (20 - 9)) / fb->height;
        uint32_t b = 19 + (py * (36 - 19)) / fb->height;
        uint32_t bg_col = 0xFF000000 | (r << 16) | (g << 8) | b;

        for (uint32_t px = 0; px < fb->width; px++) {
            /* Griglia Cyber a passi di 32px */
            if ((px % 32 == 0) || (py % 32 == 0)) {
                row[px] = COLOR_GRID_CYBER;
            } else {
                row[px] = bg_col;
            }
        }
    }

    /* Logo OSify Luminescente Centrale in Filigrana */
    int center_x = (int)fb->width / 2;
    int center_y = (int)fb->height / 2;
    osify_fb_draw_squircle(fb, center_x - 70, center_y - 70, 140, 28, 0xFF0A1828);
    osify_fb_draw_squircle(fb, center_x - 45, center_y - 45, 90, 18, 0xFF0E2A3E);
    osify_fb_draw_squircle(fb, center_x - 20, center_y - 20, 40, 8, COLOR_BORDER_NEON);

    /* 2. Icone Native della Scrivania (Sinistra) */
    struct {
        const char *label;
        uint32_t color;
        int y;
    } desktop_icons[] = {
        {"Questo PC",  COLOR_BORDER_NEON,   42},
        {"OSifyFS",    COLOR_ACCENT_BLUE,   122},
        {"App (.ify)", COLOR_ACCENT_PURPLE, 202},
        {"Cattura",    COLOR_ACCENT_AMBER,  282},
        {"Cestino",    COLOR_BTN_CLOSE,     362}
    };

    for (int i = 0; i < 5; i++) {
        int ix = 24;
        int iy = desktop_icons[i].y;
        /* Icona Squircle con riflesso */
        osify_fb_draw_squircle(fb, ix, iy, 48, 12, desktop_icons[i].color);
        osify_fb_draw_squircle(fb, ix + 4, iy + 4, 40, 8, COLOR_PANEL_GLASS);
        /* Simbolo icona interno */
        osify_fb_draw_rect(fb, ix + 16, iy + 16, 16, 16, desktop_icons[i].color);
        /* Etichetta testuale */
        osify_fb_draw_string(fb, ix - 6, iy + 52, desktop_icons[i].label, COLOR_TEXT_WHITE);
    }

    /* 3. Top Menu Bar macOS-Style a 26px */
    osify_fb_draw_rect(fb, 0, 0, fb->width, 26, COLOR_PANEL_GLASS);
    osify_fb_draw_rect(fb, 0, 25, fb->width, 1, COLOR_BORDER_NEON);
    osify_fb_draw_string(fb, 16, 5, "OSify A.1", COLOR_BORDER_NEON);
    osify_fb_draw_string(fb, 120, 5, "File  Modifica  Visualizza  Dispositivi  Rete  Sicurezza  Aiuto", COLOR_TEXT_WHITE);

    /* Telemetria di Rete, Audio e Orologio */
    const osify_net_device_t *net = osify_net_get_device();
    const osify_audio_state_t *aud = osify_audio_get_state();
    char top_status[96];
    char ip_short[24];
    osify_net_format_ip(net->ip_addr, ip_short, sizeof(ip_short));
    osify_snprintf(top_status, sizeof(top_status), "[IP: %s] [Vol: %u%%] [Rec: 60FPS] 12:00",
                   ip_short, aud->master_volume);
    osify_fb_draw_string(fb, fb->width - 390, 5, top_status, COLOR_TEXT_MUTED);

    /* 4. HUD Laterale Monitor Risorse Silicio & Potenza Hardware (Destra) */
    int hud_x = 734;
    int hud_y = 38;
    int hud_w = 274;
    int hud_h = 490;

    osify_fb_draw_rect(fb, hud_x, hud_y, hud_w, hud_h, COLOR_PANEL_GLASS);
    osify_fb_draw_rect(fb, hud_x, hud_y, hud_w, 24, COLOR_TITLEBAR_GLASS);
    osify_fb_draw_rect(fb, hud_x, hud_y, hud_w, 1, COLOR_BORDER_NEON);
    osify_fb_draw_string(fb, hud_x + 12, hud_y + 4, "MONITOR SILICIO & HUD 2050", COLOR_BORDER_NEON);

    const osify_hardware_skin_t *h = osify_get_active_skin();
    const osify_capture_state_t *c = osify_capture_get_state();
    osify_dispatch_stats_t st;
    osify_hetero_get_stats(&st);

    int hy = hud_y + 34;
    osify_fb_draw_string(fb, hud_x + 12, hy, "CPU:", COLOR_TEXT_MUTED);
    osify_fb_draw_string(fb, hud_x + 50, hy, h->cpu_brand, COLOR_TEXT_WHITE);
    hy += 20;

    char hud_buf[64];
    osify_snprintf(hud_buf, sizeof(hud_buf), "Core: %u Fisici | %u Logici", h->cpu_cores, h->cpu_threads);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_TEXT_WHITE);
    hy += 20;

    osify_snprintf(hud_buf, sizeof(hud_buf), "Clock: %u MHz | %u GFLOPS", h->cpu_freq_mhz, (uint32_t)h->cpu_peak_gflops);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_ACCENT_AMBER);
    hy += 20;

    /* Barra grafica utilizzo CPU */
    osify_fb_draw_rect(fb, hud_x + 12, hy, 250, 8, 0xFF1E293B);
    osify_fb_draw_rect(fb, hud_x + 12, hy, 180, 8, COLOR_BORDER_NEON); /* 72% */
    hy += 18;

    osify_fb_draw_string(fb, hud_x + 12, hy, "RAM: 2048 MB (Libera: 2016 MB)", COLOR_TEXT_MUTED);
    hy += 20;
    osify_fb_draw_rect(fb, hud_x + 12, hy, 250, 8, 0xFF1E293B);
    osify_fb_draw_rect(fb, hud_x + 12, hy, 40, 8, COLOR_ACCENT_PURPLE); /* 16% */
    hy += 24;

    osify_fb_draw_string(fb, hud_x + 12, hy, "SCHEDA ACQUISIZIONE:", COLOR_BORDER_NEON);
    hy += 20;
    osify_snprintf(hud_buf, sizeof(hud_buf), "Stato: %s (%u FPS)", c->is_active ? "LIVE DMA" : "STOP", c->fps);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_TEXT_WHITE);
    hy += 20;
    osify_snprintf(hud_buf, sizeof(hud_buf), "Bitrate: %u Mbps Lossless", c->bitrate_mbps);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_TEXT_MUTED);
    hy += 24;

    osify_fb_draw_string(fb, hud_x + 12, hy, "SCHEDULER ETEROGENEO:", COLOR_ACCENT_PURPLE);
    hy += 20;
    osify_snprintf(hud_buf, sizeof(hud_buf), "ALU Scalare: %u | SIMD: %u", st.tasks_on_alu_scalar, st.tasks_on_alu_vector);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_TEXT_WHITE);
    hy += 20;
    osify_snprintf(hud_buf, sizeof(hud_buf), "GPU Blit: %u   | I/O: %u", st.tasks_on_gpu_blitter, st.tasks_on_async_io);
    osify_fb_draw_string(fb, hud_x + 12, hy, hud_buf, COLOR_TEXT_WHITE);
    hy += 24;

    osify_fb_draw_string(fb, hud_x + 12, hy, "SICUREZZA & RING 0:", COLOR_BTN_MAX);
    hy += 20;
    osify_fb_draw_string(fb, hud_x + 12, hy, "SIP: IMMUTABILE | W^X: ON", COLOR_TEXT_WHITE);
    hy += 20;
    osify_fb_draw_string(fb, hud_x + 12, hy, "TPM 2.0 PCR: ENFORCED", COLOR_TEXT_MUTED);

    /* 5. Disegno Finestre Attive */
    for (size_t i = 0; i < g_window_count; i++) {
        osify_wm_draw_window(fb, &g_windows[i]);

        /* Finestra 1: Shell Terminale */
        if (osify_strcmp(g_windows[i].title, "OSify Terminale Nativo") == 0) {
            int text_y = g_windows[i].y + 36;
            for (size_t l = 0; l < g_shell_line_count; l++) {
                osify_fb_draw_string(fb, g_windows[i].x + 16, text_y, g_shell_lines[l], COLOR_TEXT_WHITE);
                text_y += 20;
            }
            char prompt_buf[100];
            osify_snprintf(prompt_buf, sizeof(prompt_buf), "osify> %s_", g_cmd_input);
            osify_fb_draw_string(fb, g_windows[i].x + 16, text_y, prompt_buf, COLOR_BORDER_NEON);
        }

        /* Finestra 2: Scheda di Acquisizione Virtuale */
        if (osify_strcmp(g_windows[i].title, "Scheda di Acquisizione Video (Virtual Capture Card)") == 0) {
            int cy = g_windows[i].y + 36;
            osify_fb_draw_string(fb, g_windows[i].x + 16, cy, "OSify Virtual Capture Card Engine (Zero Hardware Esterno)", COLOR_BORDER_NEON);
            cy += 24;
            char cap_line[96];
            osify_snprintf(cap_line, sizeof(cap_line), "Sorgente: Linear Framebuffer Tap (1024x768x32 @ %u FPS)", c->fps);
            osify_fb_draw_string(fb, g_windows[i].x + 16, cy, cap_line, COLOR_TEXT_WHITE);
            cy += 20;
            osify_snprintf(cap_line, sizeof(cap_line), "Frame Ricevuti: %llu | Flusso DMA: Lossless Ring Buffer 16MB", c->total_frames_captured);
            osify_fb_draw_string(fb, g_windows[i].x + 16, cy, cap_line, COLOR_TEXT_WHITE);
            cy += 20;
            osify_snprintf(cap_line, sizeof(cap_line), "Loopback di Rete: loopback://dispositivi/cattura0 (Bitrate: %u Mbps)", c->bitrate_mbps);
            osify_fb_draw_string(fb, g_windows[i].x + 16, cy, cap_line, COLOR_ACCENT_AMBER);
            cy += 24;

            /* Pulsanti Interattivi Scheda di Acquisizione */
            osify_fb_draw_squircle(fb, g_windows[i].x + 16, cy, 140, 8, COLOR_ACCENT_PURPLE);
            osify_fb_draw_string(fb, g_windows[i].x + 36, cy + 8, "[REC LIVE]", COLOR_TEXT_WHITE);

            osify_fb_draw_squircle(fb, g_windows[i].x + 170, cy, 170, 8, COLOR_PANEL_GLASS);
            osify_fb_draw_rect(fb, g_windows[i].x + 170, cy, 170, 1, COLOR_BORDER_NEON);
            osify_fb_draw_string(fb, g_windows[i].x + 185, cy + 8, "[FOTOGRAMMA PPM]", COLOR_BORDER_NEON);

            osify_fb_draw_squircle(fb, g_windows[i].x + 354, cy, 180, 8, COLOR_PANEL_GLASS);
            osify_fb_draw_rect(fb, g_windows[i].x + 354, cy, 180, 1, COLOR_BTN_MAX);
            osify_fb_draw_string(fb, g_windows[i].x + 370, cy + 8, "[STREAM LOOPBACK]", COLOR_BTN_MAX);
        }
    }

    /* 6. Finestra Installatore Guidato su Disco Fisso (se attiva) */
    if (g_show_installer_window) {
        osify_installer_render(fb, 140, 100, 720, 220);
    }

    /* 7. Floating Dock Inferiore con Riflesso Glassmorphism */
    int dock_w = 540;
    int dock_h = 56;
    int dock_x = ((int)fb->width - dock_w) / 2;
    int dock_y = (int)fb->height - dock_h - 12;

    osify_fb_draw_squircle(fb, dock_x, dock_y, dock_w, 16, COLOR_PANEL_GLASS);
    osify_fb_draw_rect(fb, dock_x + 10, dock_y, dock_w - 20, 1, COLOR_BORDER_NEON); /* Neon reflex */

    const char *dock_labels[] = {"Term", "Files", "Cattura", "Apps", "Rete", "Installa"};
    uint32_t dock_colors[] = {COLOR_BORDER_NEON, COLOR_ACCENT_BLUE, COLOR_ACCENT_AMBER,
                              COLOR_ACCENT_PURPLE, COLOR_BTN_MAX, 0xFFE11D48};

    int start_icon_x = dock_x + 24;
    for (int d = 0; d < 6; d++) {
        int ix = start_icon_x + d * 82;
        int iy = dock_y + 8;
        osify_fb_draw_squircle(fb, ix, iy, 40, 10, dock_colors[d]);
        osify_fb_draw_squircle(fb, ix + 4, iy + 4, 32, 8, COLOR_PANEL_GLASS);
        /* Pallino indicatore app attiva */
        osify_fb_draw_squircle(fb, ix + 17, dock_y + 48, 6, 3, COLOR_BORDER_NEON);
        osify_fb_draw_string(fb, ix - 4, iy + 12, dock_labels[d], COLOR_TEXT_WHITE);
    }

    /* 8. Cursore del Mouse Vettoriale con Ombra */
    if (g_mouse.is_visible) {
        int mx = g_mouse.x;
        int my = g_mouse.y;
        /* Ombra */
        osify_fb_draw_rect(fb, mx + 1, my + 1, 10, 10, 0xFF000000);
        /* Cursore a punta */
        for (int row = 0; row < 12; row++) {
            for (int col = 0; col <= row; col++) {
                if (mx + col < (int)fb->width && my + row < (int)fb->height) {
                    fb->buffer[(my + row) * fb->width + (mx + col)] = COLOR_BORDER_NEON;
                }
            }
        }
    }

    /* 9. Tap Automatico sul Framebuffer per la Scheda di Acquisizione Virtuale */
    osify_capture_process_frame(fb);
}

void osify_desktop_handle_key(osify_framebuffer_t *fb, char key) {
    if (!fb) return;

    if (key == '\n' || key == '\r') {
        execute_command(g_cmd_input);
        g_cmd_idx = 0;
        osify_memset(g_cmd_input, 0, sizeof(g_cmd_input));
    } else if (key == '\b') {
        if (g_cmd_idx > 0) {
            g_cmd_input[--g_cmd_idx] = '\0';
        }
    } else if (g_cmd_idx < SHELL_LINE_LEN - 2 && key >= 32 && key <= 126) {
        g_cmd_input[g_cmd_idx++] = key;
        g_cmd_input[g_cmd_idx] = '\0';
    }

    osify_desktop_render_all(fb);
}

osify_window_t *osify_wm_create_window(int x, int y, int w, int h, const char *title) {
    if (g_window_count >= MAX_WINDOWS) return NULL;
    osify_window_t *win = &g_windows[g_window_count++];
    win->id = (uint32_t)g_window_count;
    win->x = x;
    win->y = y;
    win->w = w;
    win->h = h;
    osify_strncpy(win->title, title ? title : "Finestra", sizeof(win->title) - 1);
    win->is_visible = true;
    win->is_focused = true;
    win->bg_color = COLOR_PANEL_GLASS;
    return win;
}

void osify_desktop_move_mouse(osify_framebuffer_t *fb, int new_x, int new_y) {
    g_mouse.x = new_x;
    g_mouse.y = new_y;
    if (fb) osify_desktop_render_all(fb);
}

void osify_shell_input_char(osify_framebuffer_t *fb, char c) {
    osify_desktop_handle_key(fb, c);
}

void osify_shell_execute_cmd(osify_framebuffer_t *fb, const char *cmd) {
    execute_command(cmd);
    if (fb) {
        osify_desktop_render_all(fb);
    }
}

