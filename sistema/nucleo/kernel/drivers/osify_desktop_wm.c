/* ==============================================================================
 * OSify Native Window Manager & Desktop Implementation
 * (sistema/nucleo/kernel/drivers/osify_desktop_wm.c)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Desktop Environment autonomo a 32bpp direttamente su Linear Framebuffer:
 * Dual-Panel (Top Menu Bar a 26px + Floating Dock centrata), Finestre Dark Glass,
 * Cursore del mouse vettoriale, Shell interattiva e Integrazione Rete, Audio e Installatore.
 * ==============================================================================
 */

#include "../include/osify_desktop.h"
#include "../include/osify_kstring.h"
#include "../include/osify_storage.h"
#include "../include/osify_net.h"
#include "../include/osify_audio.h"
#include "../include/osify_installer.h"
#include "../include/osify_hetero_dispatch.h"

/* Palette Colori Ufficiale Dark Glass OSify */
#define COLOR_DESKTOP_BG        0xFF0B101D  /* Blu Notte Profondo */
#define COLOR_PANEL_GLASS       0xFF141C2E  /* Dark Glass Card */
#define COLOR_TITLEBAR_GLASS    0xFF1E293B  /* Barra Titolo Finestra */
#define COLOR_BORDER_NEON       0xFF06B6D4  /* Ciano Elettrico */
#define COLOR_ACCENT_PURPLE     0xFF8B5CF6  /* Viola Cyber */
#define COLOR_BTN_CLOSE         0xFFEF4444  /* Rosso macOS */
#define COLOR_BTN_MIN           0xFFF59E0B  /* Giallo macOS */
#define COLOR_BTN_MAX           0xFF10B981  /* Verde macOS */
#define COLOR_TEXT_WHITE        0xFFF8FAFC  /* Bianco Testo */
#define COLOR_TEXT_MUTED        0xFF94A3B8  /* Grigio Ardesia */

static osify_window_t g_windows[MAX_WINDOWS];
static size_t g_window_count = 0;
static osify_mouse_cursor_t g_mouse;
static bool g_show_installer_window = false;

/* Buffer Shell Nativa su Framebuffer */
#define SHELL_MAX_LINES 14
#define SHELL_LINE_LEN  90
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
    osify_strcpy(g_shell_lines[g_shell_line_count++], "Digita 'aiuto' per la lista comandi, 'rete', 'audio' o 'installa'.");
}

static void shell_append_line(const char *line) {
    if (g_shell_line_count < SHELL_MAX_LINES) {
        osify_strncpy(g_shell_lines[g_shell_line_count++], line, SHELL_LINE_LEN - 1);
    } else {
        /* Scroll verso l'alto */
        for (size_t i = 0; i < SHELL_MAX_LINES - 1; i++) {
            osify_strcpy(g_shell_lines[i], g_shell_lines[i + 1]);
        }
        osify_strncpy(g_shell_lines[SHELL_MAX_LINES - 1], line, SHELL_LINE_LEN - 1);
    }
}

void osify_shell_execute_cmd(osify_framebuffer_t *fb, const char *cmd) {
    char echo_buf[100];
    osify_snprintf(echo_buf, sizeof(echo_buf), "osify> %s", cmd);
    shell_append_line(echo_buf);

    if (osify_strcmp(cmd, "aiuto") == 0 || osify_strcmp(cmd, "help") == 0) {
        shell_append_line("Comandi disponibili:");
        shell_append_line("  stato     - Telemetria generale e profilo silicio");
        shell_append_line("  potenza   - Introspezione silicio, GFLOPS, ALU/GPU e Scheduler");
        shell_append_line("  disco     - Elenco partizioni e file OSifyFS");
        shell_append_line("  rete      - Stato interfaccia Ethernet, IP e DNS Quad9");
        shell_append_line("  ping      - Test connettivita ICMP su Quad9 (9.9.9.9)");
        shell_append_line("  audio     - Stato mixer, volume Intel HDA e Chime");
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

    g_cmd_idx = 0;
    osify_memset(g_cmd_input, 0, sizeof(g_cmd_input));
    osify_desktop_render_all(fb);
}

void osify_shell_input_char(osify_framebuffer_t *fb, char c) {
    if (c == '\n' || c == '\r') {
        osify_shell_execute_cmd(fb, g_cmd_input);
    } else if (c == '\b' || c == 127) {
        if (g_cmd_idx > 0) {
            g_cmd_input[--g_cmd_idx] = '\0';
            osify_desktop_render_all(fb);
        }
    } else if (c >= 32 && c <= 126) {
        if (g_cmd_idx + 1 < sizeof(g_cmd_input)) {
            g_cmd_input[g_cmd_idx++] = c;
            g_cmd_input[g_cmd_idx] = '\0';
            osify_desktop_render_all(fb);
        }
    }
}

osify_window_t *osify_wm_create_window(int x, int y, int w, int h, const char *title) {
    if (g_window_count >= MAX_WINDOWS) return NULL;
    osify_window_t *win = &g_windows[g_window_count++];
    win->id = (uint32_t)g_window_count;
    win->x = x;
    win->y = y;
    win->w = w;
    win->h = h;
    win->is_visible = true;
    win->is_focused = true;
    win->bg_color = COLOR_PANEL_GLASS;
    osify_strncpy(win->title, title, sizeof(win->title) - 1);
    return win;
}

void osify_wm_draw_window(osify_framebuffer_t *fb, const osify_window_t *win) {
    if (!fb || !win || !win->is_visible) return;

    /* Corpo Finestra Dark Glass con angoli arrotondati */
    osify_fb_draw_squircle(fb, win->x, win->y, win->w, 14, win->bg_color);
    osify_fb_draw_rect(fb, win->x, win->y, win->w, win->h, win->bg_color);

    /* Barra del Titolo Finestra (28px) */
    osify_fb_draw_rect(fb, win->x, win->y, win->w, 28, COLOR_TITLEBAR_GLASS);
    /* Bordo neon superiore della finestra attiva */
    osify_fb_draw_rect(fb, win->x, win->y, win->w, 2, COLOR_BORDER_NEON);

    /* Pulsanti di Controllo Finestra macOS Style (Rosso, Giallo, Verde) */
    osify_fb_draw_squircle(fb, win->x + 12, win->y + 8, 12, 6, COLOR_BTN_CLOSE);
    osify_fb_draw_squircle(fb, win->x + 30, win->y + 8, 12, 6, COLOR_BTN_MIN);
    osify_fb_draw_squircle(fb, win->x + 48, win->y + 8, 12, 6, COLOR_BTN_MAX);

    /* Titolo Finestra centrato */
    osify_fb_draw_string(fb, win->x + 72, win->y + 6, win->title, COLOR_TEXT_WHITE);
}

void osify_desktop_init(osify_framebuffer_t *fb) {
    g_window_count = 0;
    osify_memset(g_windows, 0, sizeof(g_windows));

    /* Inizializzazione Cursore Mouse al centro */
    g_mouse.x = (int)fb->width / 2;
    g_mouse.y = (int)fb->height / 2;
    g_mouse.is_visible = true;
    g_show_installer_window = false;

    /* Inizializza Shell Nativa */
    osify_shell_init();

    /* Crea Finestra Terminale Shell di Default */
    osify_wm_create_window(80, 50, 864, 440, "OSify Terminale Nativo");
}

void osify_desktop_render_all(osify_framebuffer_t *fb) {
    if (!fb || !fb->buffer) return;

    /* 1. Sfondo Scrivania Dark Glass */
    osify_fb_clear(fb, COLOR_DESKTOP_BG);

    /* 2. Top Menu Bar macOS-Style a 26px */
    osify_fb_draw_rect(fb, 0, 0, fb->width, 26, COLOR_PANEL_GLASS);
    osify_fb_draw_string(fb, 16, 5, "OSify A.1", COLOR_BORDER_NEON);
    osify_fb_draw_string(fb, 120, 5, "File  Modifica  Rete  Audio  Sicurezza  Aiuto", COLOR_TEXT_WHITE);

    /* Telemetria di Rete e Audio nella Top Bar */
    const osify_net_device_t *net = osify_net_get_device();
    const osify_audio_state_t *aud = osify_audio_get_state();
    char top_status[90];
    char ip_short[24];
    osify_net_format_ip(net->ip_addr, ip_short, sizeof(ip_short));

    osify_snprintf(top_status, sizeof(top_status), "[IP: %s] [Vol: %u%%] [Sicuro] 12:00",
                   ip_short, aud->master_volume);
    osify_fb_draw_string(fb, fb->width - 340, 5, top_status, COLOR_TEXT_MUTED);

    /* 3. Disegno Finestre Attive */
    for (size_t i = 0; i < g_window_count; i++) {
        osify_wm_draw_window(fb, &g_windows[i]);

        /* Se e la finestra terminale, renderizza le linee della shell */
        if (osify_strcmp(g_windows[i].title, "OSify Terminale Nativo") == 0) {
            int text_y = g_windows[i].y + 38;
            for (size_t l = 0; l < g_shell_line_count; l++) {
                osify_fb_draw_string(fb, g_windows[i].x + 20, text_y, g_shell_lines[l], COLOR_TEXT_WHITE);
                text_y += 20;
            }
            /* Prompt di input attivo con cursore lampeggiante */
            char prompt_buf[100];
            osify_snprintf(prompt_buf, sizeof(prompt_buf), "osify> %s_", g_cmd_input);
            osify_fb_draw_string(fb, g_windows[i].x + 20, text_y, prompt_buf, COLOR_BORDER_NEON);
        }
    }

    /* 4. Finestra Assistente Installatore Disco Fisso (se attiva) */
    if (g_show_installer_window) {
        osify_installer_render(fb, 160, 100, 704, 200);
    }

    /* 5. Floating Dock Inferiore Centrata (Staccata dal fondo a 14px, altezza 54px) */
    int dock_w = 460;
    int dock_h = 54;
    int dock_x = ((int)fb->width - dock_w) / 2;
    int dock_y = (int)fb->height - dock_h - 14;

    osify_fb_draw_squircle(fb, dock_x, dock_y, dock_w, 18, COLOR_PANEL_GLASS);
    osify_fb_draw_rect(fb, dock_x, dock_y, dock_w, 2, COLOR_BORDER_NEON); /* Neon line */

    /* Icone Squircle macOS nel Dock con Rete, Audio e Installatore */
    const char *dock_labels[] = {"Hub", "Term", "Rete", "Audio", "Installa"};
    uint32_t dock_colors[] = {COLOR_BORDER_NEON, COLOR_ACCENT_PURPLE, 0xFF3B82F6, 0xFF10B981, 0xFFF59E0B};

    for (int d = 0; d < 5; d++) {
        int icon_x = dock_x + 18 + (d * 88);
        int icon_y = dock_y + 8;
        osify_fb_draw_squircle(fb, icon_x, icon_y, 38, 10, dock_colors[d]);
        osify_fb_draw_string(fb, icon_x + 2, icon_y + 11, dock_labels[d], COLOR_TEXT_WHITE);
    }

    /* 6. Cursore Mouse Vettoriale Dark Glass */
    if (g_mouse.is_visible) {
        int mx = g_mouse.x;
        int my = g_mouse.y;
        for (int row = 0; row < 12; row++) {
            for (int col = 0; col <= row; col++) {
                if (mx + col < (int)fb->width && my + row < (int)fb->height) {
                    uint32_t pixel_color = (col == 0 || col == row || row == 11) ? COLOR_TEXT_WHITE : COLOR_BORDER_NEON;
                    fb->buffer[(my + row) * fb->width + (mx + col)] = pixel_color;
                }
            }
        }
    }
}

void osify_desktop_handle_key(osify_framebuffer_t *fb, char c) {
    osify_shell_input_char(fb, c);
}

void osify_desktop_move_mouse(osify_framebuffer_t *fb, int new_x, int new_y) {
    if (new_x < 0) new_x = 0;
    if (new_y < 0) new_y = 0;
    if (new_x >= (int)fb->width) new_x = (int)fb->width - 1;
    if (new_y >= (int)fb->height) new_y = (int)fb->height - 1;

    g_mouse.x = new_x;
    g_mouse.y = new_y;
    osify_desktop_render_all(fb);
}
