#!/usr/bin/env python3
"""
==============================================================================
OSify Out-of-Box Experience (OOBE) — Assistente di Primo Avvio macOS Style
==============================================================================
Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
Guida l'utente al primissimo avvio del sistema operativo:
1. Benvenuto & Selezione Lingua
2. Layout Tastiera & Fuso Orario
3. Connessione Wi-Fi & Rete
4. Creazione Profilo Utente & Avatar Squircle
5. Selezione Aspetto & Tema
6. Finalizzazione e Ingresso Diretto nel Desktop
==============================================================================
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CONFIG_DIR = os.path.expanduser("~/.config/osify")
SETUP_FLAG = os.path.join(CONFIG_DIR, "setup_done")
USER_CONFIG_FILE = os.path.join(CONFIG_DIR, "user-config.json")

# Palette Colori Dark Glass macOS
COLOR_BG_DARK = "#090d16"
COLOR_SIDEBAR = "#0d1322"
COLOR_CARD = "#141c2e"
COLOR_CARD_BORDER = "#1e293b"
COLOR_ACCENT = "#06b6d4"
COLOR_ACCENT_PURPLE = "#8b5cf6"
COLOR_TEXT_WHITE = "#f8fafc"
COLOR_TEXT_MUTED = "#94a3b8"
COLOR_SUCCESS = "#10b981"

STEPS = [
    ("Benvenuto", "Panoramica di benvenuto"),
    ("Tastiera", "Layout e fuso orario"),
    ("Wi-Fi & Rete", "Connettività Internet"),
    ("Account", "Profilo e Avatar"),
    ("Aspetto", "Tema e accenti di colore"),
    ("Pronto", "Finalizzazione sistema"),
]

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

class OSifyOOBEApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Assistente di Configurazione OSify")
        self.configure(bg=COLOR_BG_DARK)

        # Dimensionamento reattivo ottimizzato per netbook 1024x600 e monitor 4K
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(880, sw - 20)
        h = min(560, sh - 40)
        x = (sw - w) // 2
        y = max(10, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(720, 480)

        self.current_step = 0
        self.config_data = {
            "lang": "it_IT",
            "keyboard": "it",
            "timezone": "Europe/Rome",
            "wifi_ssid": "",
            "wifi_pass": "",
            "fullname": "Utente OSify",
            "username": "osify",
            "avatar": "osify",
            "theme": "dark_obsidian",
            "accent": "cyan"
        }

        self.step_labels = []
        self.avatar_imgs = {}
        self.logo_img = None

        self.load_assets()
        self.build_skeleton()
        self.show_step(0)

    def load_assets(self):
        # Carica logo principale
        logo_candidates = [
            "/usr/share/pixmaps/osify.png",
            "/usr/share/pixmaps/osify-hub.png",
            "/Sistema/Icone/osify.png",
            os.path.join(REPO_ROOT, "desktop/branding/icons/64/osify.png"),
            os.path.join(REPO_ROOT, "OSify.png"),
        ]
        for c in logo_candidates:
            if os.path.exists(c):
                try:
                    im = Image.open(c).convert("RGBA")
                    im.thumbnail((52, 52), Image.Resampling.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(im)
                    break
                except Exception:
                    pass

        # Carica avatar dalle icone squircle
        icon_names = ["osify", "osify-games", "osify-terminal", "osify-audio", "osify-settings"]
        for name in icon_names:
            p_cands = [
                f"/usr/share/pixmaps/{name}.png",
                f"/Sistema/Icone/{name}.png",
                os.path.join(REPO_ROOT, f"desktop/branding/icons/48/{name}.png"),
                f"/usr/share/icons/hicolor/48x48/apps/{name}.png"
            ]
            p = next((x for x in p_cands if os.path.exists(x)), None)
            if p:
                try:
                    im = Image.open(p).convert("RGBA")
                    im.thumbnail((44, 44), Image.Resampling.LANCZOS)
                    self.avatar_imgs[name] = ImageTk.PhotoImage(im)
                except Exception:
                    pass

    def build_skeleton(self):
        # Layout orizzontale: Sidebar sinistra + Contenitore principale destro
        self.sidebar = tk.Frame(self, bg=COLOR_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Header Sidebar con Logo OSify
        sb_hdr = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        sb_hdr.pack(fill="x", padx=16, pady=20)
        if self.logo_img:
            lbl_logo = tk.Label(sb_hdr, image=self.logo_img, bg=COLOR_SIDEBAR)
            lbl_logo.pack(anchor="w")
        
        lbl_brand = tk.Label(
            sb_hdr,
            text="OSify",
            font=("Helvetica", 15, "bold"),
            fg=COLOR_TEXT_WHITE,
            bg=COLOR_SIDEBAR
        )
        lbl_brand.pack(anchor="w", pady=(6, 0))

        lbl_edition = tk.Label(
            sb_hdr,
            text="Configurazione Iniziale",
            font=("Helvetica", 9),
            fg=COLOR_ACCENT,
            bg=COLOR_SIDEBAR
        )
        lbl_edition.pack(anchor="w")

        # Separatore sottile
        sep = tk.Frame(self.sidebar, bg=COLOR_CARD_BORDER, height=1)
        sep.pack(fill="x", padx=16, pady=(10, 15))

        # Lista Step
        self.steps_container = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        self.steps_container.pack(fill="x", padx=16)

        for i, (title, desc) in enumerate(STEPS):
            item_frame = tk.Frame(self.steps_container, bg=COLOR_SIDEBAR)
            item_frame.pack(fill="x", pady=6)

            dot = tk.Label(item_frame, text="•", font=("Helvetica", 14), fg=COLOR_TEXT_MUTED, bg=COLOR_SIDEBAR)
            dot.pack(side="left", padx=(0, 8))

            text_frame = tk.Frame(item_frame, bg=COLOR_SIDEBAR)
            text_frame.pack(side="left", fill="x")

            lbl_t = tk.Label(text_frame, text=title, font=("Helvetica", 10, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_SIDEBAR)
            lbl_t.pack(anchor="w")

            self.step_labels.append((dot, lbl_t))

        # Area Contenuto a destra
        self.content_area = tk.Frame(self, bg=COLOR_BG_DARK)
        self.content_area.pack(side="right", fill="both", expand=True, padx=24, pady=20)

        # Footer con pulsanti Indietro / Avanti
        self.footer = tk.Frame(self.content_area, bg=COLOR_BG_DARK)
        self.footer.pack(side="bottom", fill="x", pady=(15, 0))

        self.btn_back = tk.Button(
            self.footer,
            text="Indietro",
            font=("Helvetica", 10),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
            activebackground=COLOR_CARD_BORDER,
            activeforeground=COLOR_TEXT_WHITE,
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            command=self.prev_step
        )
        self.btn_back.pack(side="left")

        self.btn_next = tk.Button(
            self.footer,
            text="Continua",
            font=("Helvetica", 10, "bold"),
            bg=COLOR_ACCENT,
            fg="#000000",
            activebackground="#22d3ee",
            activeforeground="#000000",
            relief="flat",
            bd=0,
            padx=20,
            pady=6,
            command=self.next_step
        )
        self.btn_next.pack(side="right")

        # Container dinamico per le viste dei singoli step
        self.step_view_frame = tk.Frame(self.content_area, bg=COLOR_BG_DARK)
        self.step_view_frame.pack(fill="both", expand=True)

    def update_sidebar_indicators(self):
        for i, (dot, lbl) in enumerate(self.step_labels):
            if i == self.current_step:
                dot.config(fg=COLOR_ACCENT)
                lbl.config(fg=COLOR_TEXT_WHITE)
            elif i < self.current_step:
                dot.config(fg=COLOR_SUCCESS)
                lbl.config(fg=COLOR_TEXT_MUTED)
            else:
                dot.config(fg="#334155")
                lbl.config(fg="#64748b")

        self.btn_back.config(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == len(STEPS) - 1:
            self.btn_next.config(text="Entra in OSify", bg=COLOR_SUCCESS, fg="#ffffff")
        else:
            self.btn_next.config(text="Continua", bg=COLOR_ACCENT, fg="#000000")

    def show_step(self, idx):
        self.current_step = idx
        self.update_sidebar_indicators()

        for w in self.step_view_frame.winfo_children():
            w.destroy()

        if idx == 0:
            self.render_step_welcome()
        elif idx == 1:
            self.render_step_keyboard()
        elif idx == 2:
            self.render_step_wifi()
        elif idx == 3:
            self.render_step_account()
        elif idx == 4:
            self.render_step_appearance()
        elif idx == 5:
            self.render_step_finish()

    # STEP 1: BENVENUTO
    def render_step_welcome(self):
        lbl_h = tk.Label(
            self.step_view_frame,
            text="Benvenuto nel tuo nuovo computer",
            font=("Helvetica", 18, "bold"),
            fg=COLOR_TEXT_WHITE,
            bg=COLOR_BG_DARK
        )
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(
            self.step_view_frame,
            text="OSify è stato progettato per offrirti velocità estrema, sicurezza e un'esperienza visiva fluida e raffinata. Seleziona la tua lingua principale per iniziare.",
            font=("Helvetica", 10),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_DARK,
            wraplength=560,
            justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(0, 16))

        card = tk.Frame(self.step_view_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        card.pack(fill="both", expand=True, pady=4)

        lbl_card_title = tk.Label(card, text="LINGUA PRINCIPALE DEL SISTEMA", font=("Helvetica", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_CARD)
        lbl_card_title.pack(anchor="w", padx=16, pady=(14, 8))

        self.lang_var = tk.StringVar(value=self.config_data["lang"])
        langs = [
            ("Italiano (Italia) — Predefinito", "it_IT"),
            ("English (United States)", "en_US"),
            ("Español (España)", "es_ES"),
            ("Français (France)", "fr_FR"),
            ("Deutsch (Deutschland)", "de_DE")
        ]
        for name, code in langs:
            rb = tk.Radiobutton(
                card,
                text=name,
                variable=self.lang_var,
                value=code,
                font=("Helvetica", 10),
                fg=COLOR_TEXT_WHITE,
                bg=COLOR_CARD,
                selectcolor=COLOR_SIDEBAR,
                activebackground=COLOR_CARD,
                activeforeground=COLOR_ACCENT
            )
            rb.pack(anchor="w", padx=20, pady=4)

    # STEP 2: TASTIERA & FUSO ORARIO
    def render_step_keyboard(self):
        lbl_h = tk.Label(self.step_view_frame, text="Layout Tastiera e Fuso Orario", font=("Helvetica", 18, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_DARK)
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(self.step_view_frame, text="Scegli la mappatura dei tasti per digitare correttamente accenti e caratteri speciali.", font=("Helvetica", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_desc.pack(anchor="w", pady=(0, 14))

        card = tk.Frame(self.step_view_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        card.pack(fill="x", pady=4)

        lbl_k_title = tk.Label(card, text="SELEZIONA DISPOSIZIONE TASTI", font=("Helvetica", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_CARD)
        lbl_k_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.kmap_var = tk.StringVar(value=self.config_data["keyboard"])
        kmaps = [
            ("Italiana (QWERTY standard con lettere accentate à è ì ò ù)", "it"),
            ("Inglese USA (QWERTY universale)", "us"),
            ("Inglese UK (Regno Unito)", "gb"),
            ("Tedesca (QWERTZ)", "de"),
            ("Francese (AZERTY)", "fr"),
        ]
        for name, code in kmaps:
            rb = tk.Radiobutton(
                card,
                text=name,
                variable=self.kmap_var,
                value=code,
                font=("Helvetica", 10),
                fg=COLOR_TEXT_WHITE,
                bg=COLOR_CARD,
                selectcolor=COLOR_SIDEBAR,
                activebackground=COLOR_CARD,
                activeforeground=COLOR_ACCENT,
                command=self.apply_keymap_test
            )
            rb.pack(anchor="w", padx=20, pady=3)

        # Test interattivo
        test_frame = tk.Frame(self.step_view_frame, bg=COLOR_BG_DARK)
        test_frame.pack(fill="x", pady=10)

        lbl_test = tk.Label(test_frame, text="Prova di battitura immediata:", font=("Helvetica", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_test.pack(anchor="w", pady=(0, 4))

        self.txt_test = tk.Entry(test_frame, font=("Helvetica", 11), bg=COLOR_CARD, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_ACCENT, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        self.txt_test.pack(fill="x", ipady=4)
        self.txt_test.insert(0, "Premi i tasti qui per testare la tastiera...")

    def apply_keymap_test(self):
        k = self.kmap_var.get()
        run_cmd(f"setxkbmap {k} 2>/dev/null")

    # STEP 3: WI-FI & RETE
    def render_step_wifi(self):
        lbl_h = tk.Label(self.step_view_frame, text="Connettività Wi-Fi", font=("Helvetica", 18, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_DARK)
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(self.step_view_frame, text="Connettiti a una rete wireless per scaricare aggiornamenti e navigare con OSify Browser.", font=("Helvetica", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_desc.pack(anchor="w", pady=(0, 12))

        card = tk.Frame(self.step_view_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        card.pack(fill="both", expand=True, pady=4)

        lbl_w_title = tk.Label(card, text="RETI WIRELESS DISPONIBILI", font=("Helvetica", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_CARD)
        lbl_w_title.pack(anchor="w", padx=16, pady=(12, 6))

        # Scansione reti reali
        self.wifi_listbox = tk.Listbox(
            card,
            bg=COLOR_SIDEBAR,
            fg=COLOR_TEXT_WHITE,
            selectbackground=COLOR_ACCENT,
            selectforeground="#000000",
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0,
            height=5
        )
        self.wifi_listbox.pack(fill="x", padx=16, pady=(0, 8))

        networks = self.scan_wifi()
        if not networks:
            networks = ["[Cablata] Connessione Ethernet Attiva", "OSify-Mesh-FastNet", "Wi-Fi Casa (WPA2)", "Altra Rete..."]
        for net in networks:
            self.wifi_listbox.insert(tk.END, f"  📶  {net}")
        self.wifi_listbox.selection_set(0)

        # Inserimento Password
        pwd_frame = tk.Frame(card, bg=COLOR_CARD)
        pwd_frame.pack(fill="x", padx=16, pady=6)

        lbl_pwd = tk.Label(pwd_frame, text="Chiave di Sicurezza:", font=("Helvetica", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD)
        lbl_pwd.pack(side="left", padx=(0, 8))

        self.wifi_pwd_entry = tk.Entry(pwd_frame, font=("Helvetica", 10), show="•", bg=COLOR_SIDEBAR, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_ACCENT, bd=1, relief="solid")
        self.wifi_pwd_entry.pack(side="left", fill="x", expand=True, ipady=3)

    def scan_wifi(self):
        out = run_cmd("nmcli -t -f SSID dev wifi list 2>/dev/null | grep -v '^--$' | head -n 6")
        if not out:
            out = run_cmd("iwlist scan 2>/dev/null | grep 'ESSID:' | cut -d: -f2 | tr -d '\"' | head -n 6")
        lines = [l.strip() for l in out.split("\n") if l.strip()]
        return lines

    # STEP 4: ACCOUNT UTENTE & AVATAR
    def render_step_account(self):
        lbl_h = tk.Label(self.step_view_frame, text="Crea il tuo Profilo Personale", font=("Helvetica", 18, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_DARK)
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(self.step_view_frame, text="Questo account ti permetterà di accedere al computer e proteggere i tuoi file personali.", font=("Helvetica", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_desc.pack(anchor="w", pady=(0, 12))

        card = tk.Frame(self.step_view_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        card.pack(fill="both", expand=True, pady=4)

        form_frame = tk.Frame(card, bg=COLOR_CARD)
        form_frame.pack(fill="x", padx=20, pady=12)

        tk.Label(form_frame, text="Nome Completo:", font=("Helvetica", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_fullname = tk.Entry(form_frame, font=("Helvetica", 10), bg=COLOR_SIDEBAR, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_ACCENT)
        self.entry_fullname.grid(row=0, column=1, sticky="ew", padx=10, pady=4)
        self.entry_fullname.insert(0, self.config_data["fullname"])

        tk.Label(form_frame, text="Nome Utente (login):", font=("Helvetica", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_username = tk.Entry(form_frame, font=("Helvetica", 10), bg=COLOR_SIDEBAR, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_ACCENT)
        self.entry_username.grid(row=1, column=1, sticky="ew", padx=10, pady=4)
        self.entry_username.insert(0, self.config_data["username"])

        tk.Label(form_frame, text="Password:", font=("Helvetica", 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD).grid(row=2, column=0, sticky="w", pady=4)
        self.entry_pass = tk.Entry(form_frame, font=("Helvetica", 10), show="•", bg=COLOR_SIDEBAR, fg=COLOR_TEXT_WHITE, insertbackground=COLOR_ACCENT)
        self.entry_pass.grid(row=2, column=1, sticky="ew", padx=10, pady=4)

        form_frame.columnconfigure(1, weight=1)

        # Scelta Avatar
        lbl_av = tk.Label(card, text="SCEGLI IL TUO AVATAR SQUIRCLE", font=("Helvetica", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_CARD)
        lbl_av.pack(anchor="w", padx=20, pady=(8, 6))

        av_row = tk.Frame(card, bg=COLOR_CARD)
        av_row.pack(fill="x", padx=20, pady=(0, 10))

        self.selected_avatar = tk.StringVar(value="osify")
        for name, img in self.avatar_imgs.items():
            btn = tk.Radiobutton(
                av_row,
                image=img,
                indicatoron=0,
                variable=self.selected_avatar,
                value=name,
                bg=COLOR_CARD,
                selectcolor=COLOR_ACCENT,
                activebackground=COLOR_CARD_BORDER,
                bd=2,
                relief="ridge"
            )
            btn.pack(side="left", padx=8)

    # STEP 5: ASPETTO & TEMA
    def render_step_appearance(self):
        lbl_h = tk.Label(self.step_view_frame, text="Aspetto e Personalizzazione", font=("Helvetica", 18, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_DARK)
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(self.step_view_frame, text="Scegli lo stile visivo dell'interfaccia. Potrai sempre modificarlo in seguito nelle Impostazioni.", font=("Helvetica", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_desc.pack(anchor="w", pady=(0, 14))

        theme_frame = tk.Frame(self.step_view_frame, bg=COLOR_BG_DARK)
        theme_frame.pack(fill="x", pady=6)

        # Card 1: Dark Obsidian (macOS Style)
        c1 = tk.Frame(theme_frame, bg=COLOR_CARD, bd=2, relief="solid", highlightbackground=COLOR_ACCENT)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=4)

        tk.Label(c1, text="DARK OBSIDIAN", font=("Helvetica", 11, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(c1, text="Vetro scuro, contrasto profondo e Traffic Lights in stile Apple macOS.", font=("Helvetica", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD, wraplength=220, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

        # Card 2: Cyber Neon
        c2 = tk.Frame(theme_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_CARD_BORDER)
        c2.pack(side="right", fill="both", expand=True, padx=(8, 0), pady=4)

        tk.Label(c2, text="CYBER NEON", font=("Helvetica", 11, "bold"), fg=COLOR_ACCENT_PURPLE, bg=COLOR_CARD).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(c2, text="Accenti ciano luminescenti, gradiente viola e feedback visivo ad alto impatto.", font=("Helvetica", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_CARD, wraplength=220, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

    # STEP 6: PRONTO & FINALIZZAZIONE
    def render_step_finish(self):
        lbl_h = tk.Label(self.step_view_frame, text="Tutto Pronto per Iniziare!", font=("Helvetica", 18, "bold"), fg=COLOR_TEXT_WHITE, bg=COLOR_BG_DARK)
        lbl_h.pack(anchor="w", pady=(0, 6))

        lbl_desc = tk.Label(self.step_view_frame, text="Il tuo profilo è stato registrato. Clicca su 'Entra in OSify' per aprire la tua nuova Scrivania.", font=("Helvetica", 10), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_DARK)
        lbl_desc.pack(anchor="w", pady=(0, 16))

        card = tk.Frame(self.step_view_frame, bg=COLOR_CARD, bd=1, relief="solid", highlightbackground=COLOR_SUCCESS)
        card.pack(fill="both", expand=True, pady=4)

        tk.Label(card, text="RIEPILOGO CONFIGURAZIONE", font=("Helvetica", 10, "bold"), fg=COLOR_SUCCESS, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(14, 8))

        summary = [
            f"• Lingua di Sistema: {self.config_data.get('lang', 'it_IT')}",
            f"• Disposizione Tastiera: {self.config_data.get('keyboard', 'it')}",
            f"• Utente Predefinito: {self.config_data.get('fullname', 'Utente OSify')} ({self.config_data.get('username', 'osify')})",
            f"• Ambiente Desktop: OSify Dual-Panel",
            f"• Gestore Icone: Squircle HD Native Engine",
        ]
        for s in summary:
            tk.Label(card, text=s, font=("Helvetica", 10), fg=COLOR_TEXT_WHITE, bg=COLOR_CARD).pack(anchor="w", padx=20, pady=3)

    def prev_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def next_step(self):
        # Salva stato step corrente
        if self.current_step == 0:
            self.config_data["lang"] = self.lang_var.get()
        elif self.current_step == 1:
            self.config_data["keyboard"] = self.kmap_var.get()
        elif self.current_step == 2:
            sel = self.wifi_listbox.curselection()
            if sel:
                self.config_data["wifi_ssid"] = self.wifi_listbox.get(sel[0]).replace("  📶  ", "")
            self.config_data["wifi_pass"] = self.wifi_pwd_entry.get()
        elif self.current_step == 3:
            self.config_data["fullname"] = self.entry_fullname.get().strip() or "Utente OSify"
            self.config_data["username"] = self.entry_username.get().strip() or "osify"
            self.config_data["avatar"] = self.selected_avatar.get()

        if self.current_step < len(STEPS) - 1:
            self.show_step(self.current_step + 1)
        else:
            self.complete_setup()

    def complete_setup(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            with open(USER_CONFIG_FILE, "w") as f:
                json.dump(self.config_data, f, indent=2)
            with open(SETUP_FLAG, "w") as f:
                f.write("SETUP_COMPLETED_V1\n")
        except Exception as e:
            print("Errore salvataggio config:", e)

        # Applica keymap reale
        run_cmd(f"setxkbmap {self.config_data.get('keyboard', 'it')} 2>/dev/null")

        # Connessione Wi-Fi se fornita
        ssid = self.config_data.get("wifi_ssid")
        pwd = self.config_data.get("wifi_pass")
        if ssid and pwd and not ssid.startswith("[Cablata]"):
            run_cmd(f"nmcli dev wifi connect '{ssid}' password '{pwd}' 2>/dev/null &")

        self.destroy()
        sys.exit(0)

def main():
    app = OSifyOOBEApp()
    app.mainloop()

if __name__ == "__main__":
    main()
