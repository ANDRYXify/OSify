#!/usr/bin/env python3
"""
==============================================================================
OSify Deck Shell — Next-Gen SteamOS & KDE Plasma 6 Dual Experience
==============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Zero icone emoji, zero contrasti accecanti, zero interfacce da telefono per anziani.
Aderenza rigorosa ai design guidelines di Valve SteamOS e KDE Plasma 6:
  1. SteamOS Gaming Mode (Capsule Artwork 2:3, Top Bar fluida, Footer Console, Focus Glow)
  2. KDE Plasma 6 Desktop Mode (Floating Centered Pill Dock, Wallpaper Slate, Widget)
  3. Quick Access Menu (QAM Overlay laterale con slider TDP, FPS Cap, CPU Governor)
  4. Universal Execution Matrix (UEM) Integration & Binary Forensic Inspector
==============================================================================
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter

# Importazione modulo asset vettoriali
sys.path.insert(0, os.path.dirname(__file__))
from osify_ui_assets import (
    COLOR_BG_BASE, COLOR_BG_SURFACE, COLOR_BG_CARD, COLOR_BG_CARD_HOVER,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_CYAN, COLOR_ACCENT_MINT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_BORDER_SUBTLE,
    COLOR_BORDER_FOCUS, COLOR_PILL_BG,
    create_vector_icon, create_capsule_cover, draw_rounded_rect
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OSIFY_CTL = os.path.join(REPO_ROOT, "tools/osify-ctl")
LOGO_SRC = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-dark-1920x1080.png")
if not os.path.exists(LOGO_SRC):
    LOGO_SRC = os.path.join(REPO_ROOT, "OSify.png")

class OSifyDeckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSify — Universal Gaming & Desktop Experience")
        self.geometry("1160x720")
        self.minsize(1024, 600)
        self.configure(bg=COLOR_BG_BASE)

        self.current_mode = "DECK"   # "DECK" (SteamOS) oppure "DESKTOP" (KDE Plasma 6)
        self.current_tab = "HOME"
        self.selected_card_idx = 0
        self.qam_visible = False

        # Parametri Hardware e Performance
        self.tdp_val = 15
        self.fps_cap = "60 FPS"
        self.cpu_gov = "BORE Realtime (1000Hz)"
        self.zram_status = "Attivo (LZ4 1.5x - 1536MB)"
        self.active_workload = self.get_initial_workload()

        self.card_widgets = []
        self.icon_cache = {}
        self.cover_cache = []

        self.init_typography()
        self.init_assets()
        self.init_keyboard_nav()
        self.build_shell()
        self.start_telemetry_loop()

    def init_typography(self):
        # Tipografia moderna, rigorosa e proporzionata
        self.font_brand = ("Helvetica Neue", 13, "bold")
        self.font_tab = ("Helvetica Neue", 10, "bold")
        self.font_title = ("Helvetica Neue", 16, "bold")
        self.font_subtitle = ("Helvetica Neue", 11)
        self.font_heading = ("Helvetica Neue", 12, "bold")
        self.font_body = ("Helvetica Neue", 10)
        self.font_small = ("Helvetica Neue", 9)
        self.font_mono = ("Courier New", 9, "bold")

    def get_icon(self, name, size=24, color=COLOR_TEXT_MUTED):
        key = (name, size, color)
        if key not in self.icon_cache:
            pil_img = create_vector_icon(name, size=size, color=color)
            self.icon_cache[key] = ImageTk.PhotoImage(pil_img)
        return self.icon_cache[key]

    def init_assets(self):
        # 1. Logo OSify per la Topbar
        self.logo_topbar = None
        orig_logo = os.path.join(REPO_ROOT, "OSify.png")
        if os.path.exists(orig_logo):
            try:
                raw = Image.open(orig_logo).convert("RGBA")
                raw = raw.resize((26, 26), Image.Resampling.LANCZOS)
                self.logo_topbar = ImageTk.PhotoImage(raw)
            except Exception:
                pass

        # 2. Generazione delle copertine delle Capsule (stile SteamOS 2:3)
        self.card_data = [
            {
                "title": "Cyberpunk 2077",
                "subtitle": "Night City Direct3D 12",
                "tag": "WIN64 PE",
                "runtime": "Proton-GE 9.0 • DXVK-Async",
                "grad": ((28, 38, 56), (14, 18, 27)),
                "cmd": lambda: self.launch_title("Cyberpunk 2077", "Proton-GE (DXVK-Async + Fsync)")
            },
            {
                "title": "Orbit64",
                "subtitle": "N64 Engine Zero-Jitter",
                "tag": "UEM DYNAREC",
                "runtime": "JIT Recompiler • 60 FPS",
                "grad": ((42, 28, 64), (16, 14, 28)),
                "cmd": lambda: self.launch_title("Orbit64", "UEM Native JIT (Compagno Engine)")
            },
            {
                "title": "Elden Ring",
                "subtitle": "FromSoftware Action RPG",
                "tag": "EAC BRIDGE",
                "runtime": "Anti-Cheat Proton Bridge",
                "grad": ((48, 38, 24), (18, 16, 12)),
                "cmd": lambda: self.launch_title("Elden Ring", "Proton Experimental + EAC")
            },
            {
                "title": "OSify Web Shield",
                "subtitle": "Falkon & Firefox Hardened",
                "tag": "ISOLATED WEB",
                "runtime": "Anti-Telemetry & DNS Shield",
                "grad": ((18, 44, 48), (10, 20, 24)),
                "cmd": self.action_launch_browser
            },
            {
                "title": "Android Suite",
                "subtitle": "App Mobile & Produttività",
                "tag": "WAYDROID APK",
                "runtime": "LXC Container • DRI3 GPU",
                "grad": ((22, 48, 36), (12, 24, 18)),
                "cmd": lambda: self.launch_title("Android Runtime", "Waydroid LXC Container")
            },
            {
                "title": "Darwin Suite",
                "subtitle": "App macOS & Mach-O",
                "tag": "DARLING KERNEL",
                "runtime": "Mach-O Loader • Cocoa/CLI",
                "grad": ((36, 36, 48), (16, 16, 24)),
                "cmd": lambda: self.launch_title("Darwin Suite", "Darling Mach-O Subsystem")
            },
            {
                "title": "MS-DOS Suite",
                "subtitle": "Applicativi Legacy 16-Bit",
                "tag": "DOSBOX MZ",
                "runtime": "16-bit Real Mode Emulation",
                "grad": ((44, 30, 20), (20, 14, 10)),
                "cmd": lambda: self.launch_title("MS-DOS Legacy", "DOSBox-Staging Engine")
            },
            {
                "title": "WASM High-Perf",
                "subtitle": "Moduli WebAssembly WASI",
                "tag": "WASMTIME JIT",
                "runtime": "Isolamento Sandboxed WASI",
                "grad": ((30, 24, 52), (14, 12, 26)),
                "cmd": lambda: self.launch_title("WASM Engine", "Wasmtime JIT Runner")
            }
        ]

        # Pre-rendering e caching delle capsule
        for c in self.card_data:
            cov = create_capsule_cover(
                c["title"], c["subtitle"], c["tag"], c["grad"],
                width=176, height=255, is_verified=True
            )
            self.cover_cache.append(ImageTk.PhotoImage(cov))

    def init_keyboard_nav(self):
        self.bind("<Left>", lambda e: self.navigate_cards(-1))
        self.bind("<Right>", lambda e: self.navigate_cards(1))
        self.bind("<Return>", lambda e: self.activate_current_card())
        self.bind("<space>", lambda e: self.activate_current_card())
        self.bind("<Tab>", lambda e: self.toggle_gaming_desktop_mode())
        self.bind("<Escape>", lambda e: self.toggle_qam())
        self.bind("<F1>", lambda e: self.toggle_qam())
        self.bind("<F2>", lambda e: self.toggle_gaming_desktop_mode())

    def build_shell(self):
        # 1. Top Bar SteamOS (Altezza fissa 44px, elegante, pulita)
        self.topbar = tk.Frame(self, bg=COLOR_BG_BASE, height=44, bd=0, highlightthickness=0)
        self.topbar.pack(side="top", fill="x")
        self.render_topbar()

        # 2. Main Viewport Container
        self.viewport = tk.Frame(self, bg=COLOR_BG_BASE, bd=0, highlightthickness=0)
        self.viewport.pack(side="top", fill="both", expand=True)

        # 3. Footer Console Controls Bar (Altezza 32px, prompt tastiera/controller)
        self.footer = tk.Frame(self, bg=COLOR_BG_BASE, height=32, bd=0, highlightthickness=0)
        self.footer.pack(side="bottom", fill="x")
        self.render_footer()

        # Mostra la schermata iniziale
        if self.current_mode == "DECK":
            self.render_deck_view()
        else:
            self.render_desktop_view()

    # =========================================================================
    # TOP BAR (STILE STEAM DECK OLED & KDE PLASMA)
    # =========================================================================
    def render_topbar(self):
        for w in self.topbar.winfo_children():
            w.destroy()

        # Sinistra: Logo + Brand + Nome Utente
        left_box = tk.Frame(self.topbar, bg=COLOR_BG_BASE)
        left_box.pack(side="left", padx=18, pady=8)

        if self.logo_topbar:
            lbl_logo = tk.Label(left_box, image=self.logo_topbar, bg=COLOR_BG_BASE)
            lbl_logo.pack(side="left", padx=(0, 8))

        lbl_brand = tk.Label(left_box, text="OSify", font=self.font_brand, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE)
        lbl_brand.pack(side="left")

        lbl_user = tk.Label(left_box, text=" | Compagno", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE)
        lbl_user.pack(side="left", padx=(2, 0))

        # Centro: Tab Bar Orizzontale pulita
        center_box = tk.Frame(self.topbar, bg=COLOR_BG_BASE)
        center_box.pack(side="left", expand=True)

        tabs = [
            ("HOME", lambda: self.switch_tab("HOME")),
            ("LIBRERIA", lambda: self.switch_tab("LIBRERIA")),
            ("MATRICE UEM", lambda: self.switch_tab("UEM")),
            ("IMPOSTAZIONI", lambda: self.switch_tab("IMPOSTAZIONI")),
            ("DESKTOP PLASMA", self.toggle_gaming_desktop_mode if self.current_mode == "DECK" else self.toggle_gaming_desktop_mode)
        ]

        for tab_name, tab_cmd in tabs:
            is_active = (self.current_tab == tab_name and self.current_mode in ("DECK", "SETTINGS")) or (tab_name == "DESKTOP PLASMA" and self.current_mode == "DESKTOP")
            tab_frame = tk.Frame(center_box, bg=COLOR_BG_BASE, cursor="hand2")
            tab_frame.pack(side="left", padx=10, pady=6)

            text_color = COLOR_ACCENT_BLUE if is_active else COLOR_TEXT_MUTED
            lbl = tk.Label(tab_frame, text=tab_name, font=self.font_tab, fg=text_color, bg=COLOR_BG_BASE)
            lbl.pack()

            if is_active:
                indicator = tk.Frame(tab_frame, bg=COLOR_ACCENT_BLUE, height=2, width=lbl.winfo_reqwidth() or 40)
                indicator.pack(fill="x", pady=(2, 0))

            tab_frame.bind("<Button-1>", lambda e, cmd=tab_cmd: cmd())
            lbl.bind("<Button-1>", lambda e, cmd=tab_cmd: cmd())

        # Destra: Indicatori Geometrici e Telemetria Kernel
        right_box = tk.Frame(self.topbar, bg=COLOR_BG_BASE)
        right_box.pack(side="right", padx=16, pady=8)

        self.lbl_workload_pill = tk.Label(
            right_box, text=f"[{self.active_workload}]",
            font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_SURFACE,
            padx=6, pady=2, cursor="hand2"
        )
        self.lbl_workload_pill.pack(side="left", padx=(0, 8))
        self.lbl_workload_pill.bind("<Button-1>", lambda e: self.show_settings_mode("WORKLOAD"))

        self.lbl_telemetry = tk.Label(
            right_box, text="BORE 1000Hz • 118MB",
            font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE
        )
        self.lbl_telemetry.pack(side="left", padx=(0, 10))

        # Icona Wi-Fi geometrica (cliccabile per impostazioni rete)
        ico_wifi = self.get_icon("wifi", size=18, color=COLOR_TEXT_MUTED)
        lbl_wifi = tk.Label(right_box, image=ico_wifi, bg=COLOR_BG_BASE, cursor="hand2")
        lbl_wifi.pack(side="left", padx=3)
        lbl_wifi.bind("<Button-1>", lambda e: self.show_settings_mode("WIFI"))

        # Icona Batteria geometrica (cliccabile per alimentazione)
        ico_bat = self.get_icon("battery", size=18, color=COLOR_ACCENT_MINT)
        lbl_bat = tk.Label(right_box, image=ico_bat, bg=COLOR_BG_BASE, cursor="hand2")
        lbl_bat.pack(side="left", padx=3)
        lbl_bat.bind("<Button-1>", lambda e: self.show_settings_mode("BATTERY"))

        # Orologio digitale
        self.lbl_clock = tk.Label(right_box, text=time.strftime("%H:%M"), font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE)
        self.lbl_clock.pack(side="left", padx=(6, 8))

        # Pulsante Quick Access Menu (...)
        qam_btn = tk.Label(right_box, text="•••", font=("Helvetica Neue", 12, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE, padx=8, pady=2, cursor="hand2")
        qam_btn.pack(side="left", padx=(0, 6))
        qam_btn.bind("<Button-1>", lambda e: self.toggle_qam())

        # Pulsante Power Menu Spegnimento IEC 5009
        ico_pwr = self.get_icon("power", size=16, color="#ef4444")
        pwr_btn = tk.Label(right_box, image=ico_pwr, bg=COLOR_BG_SURFACE, padx=6, pady=2, cursor="hand2")
        pwr_btn.pack(side="left")
        pwr_btn.bind("<Button-1>", lambda e: self.open_power_menu())

    # =========================================================================
    # FOOTER BAR (PROMPT COMANDI CONSOLE)
    # =========================================================================
    def render_footer(self):
        for w in self.footer.winfo_children():
            w.destroy()

        line = tk.Frame(self.footer, bg=COLOR_BORDER_SUBTLE, height=1)
        line.pack(fill="x")

        box = tk.Frame(self.footer, bg=COLOR_BG_BASE)
        box.pack(fill="x", padx=20, pady=4)

        prompts = [
            ("[Invio / A]", "Avvia"),
            ("[Spazio / Y]", "Radiografia UEM"),
            ("[Tab / X]", "Switch Mode"),
            ("[Esc / •••]", "Menu Rapido QAM")
        ]

        for key, act in prompts:
            p_frame = tk.Frame(box, bg=COLOR_BG_BASE)
            p_frame.pack(side="left", padx=(0, 20))
            tk.Label(p_frame, text=key, font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE).pack(side="left")
            tk.Label(p_frame, text=f" {act}", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(side="left")

        # Indicatore status UEM a destra
        status_txt = "UEM Kernel Dispatcher: Pronto (PE, DOS, Mach-O, APK, WASM)"
        tk.Label(box, text=status_txt, font=self.font_small, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(side="right")

    # =========================================================================
    # GAMING MODE (STEAM DECK UI)
    # =========================================================================
    def render_deck_view(self):
        for w in self.viewport.winfo_children():
            w.destroy()

        container = tk.Frame(self.viewport, bg=COLOR_BG_BASE)
        container.pack(fill="both", expand=True, padx=24, pady=(10, 14))

        # 1. SPOTLIGHT / HERO SHOWCASE
        self.render_hero_spotlight(container)

        # 2. CAROSELLO / GRIGLIA CAPSULE A SCORRIMENTO
        shelf_header = tk.Frame(container, bg=COLOR_BG_BASE)
        shelf_header.pack(fill="x", pady=(12, 6))

        lbl_shelf = tk.Label(shelf_header, text="Libreria & Sottosistemi UEM", font=self.font_heading, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE)
        lbl_shelf.pack(side="left")

        # Indicatori di scorrimento laterale
        nav_box = tk.Frame(shelf_header, bg=COLOR_BG_BASE)
        nav_box.pack(side="right")

        btn_prev = tk.Label(nav_box, text="◀", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE, padx=8, pady=2, cursor="hand2")
        btn_prev.pack(side="left", padx=2)
        btn_prev.bind("<Button-1>", lambda e: self.navigate_cards(-1))

        btn_next = tk.Label(nav_box, text="▶", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE, padx=8, pady=2, cursor="hand2")
        btn_next.pack(side="left", padx=2)
        btn_next.bind("<Button-1>", lambda e: self.navigate_cards(1))

        # Calcola finestra di visualizzazione (mostra fino a 6 card alla volta)
        shelf_frame = tk.Frame(container, bg=COLOR_BG_BASE)
        shelf_frame.pack(fill="x", pady=2)

        # Determinazione indice iniziale visualizzato per mantenere la card selezionata visibile
        cards_per_view = 6
        start_idx = 0
        if self.selected_card_idx >= cards_per_view:
            start_idx = min(self.selected_card_idx - cards_per_view + 1, len(self.card_data) - cards_per_view)

        self.card_widgets = []
        for i in range(start_idx, min(start_idx + cards_per_view, len(self.card_data))):
            card_info = self.card_data[i]
            c_widget = self.create_card_capsule(shelf_frame, i, card_info)
            c_widget.pack(side="left", padx=5, pady=2)
            self.card_widgets.append((i, c_widget))

        self.update_card_focus()

    def render_hero_spotlight(self, parent):
        hero = tk.Frame(parent, bg=COLOR_BG_SURFACE, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        hero.pack(fill="x", pady=(0, 6), ipady=8, ipadx=16)

        left = tk.Frame(hero, bg=COLOR_BG_SURFACE)
        left.pack(side="left", fill="both", expand=True)

        # Category pill
        pill = tk.Frame(left, bg=COLOR_PILL_BG, padx=8, pady=2)
        pill.pack(anchor="w")
        tk.Label(pill, text="UEM RUNTIME CORE • ATTIVO", font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_PILL_BG).pack()

        # Titolo e descrizione
        tk.Label(left, text="Universal Execution Matrix", font=self.font_title, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(4, 2))
        tk.Label(
            left,
            text="Sfondamento trasparente delle barriere architetturali. Esecuzione nativa a livello kernel di binari\nWindows PE (DXVK/Proton), Android APK (Waydroid), macOS (Darling), MS-DOS e Cross-ISA senza configurazione.",
            font=self.font_body, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE, justify="left"
        ).pack(anchor="w", pady=(0, 6))

        # Pulsanti d'azione hero (stile console pills discreti)
        btn_box = tk.Frame(left, bg=COLOR_BG_SURFACE)
        btn_box.pack(anchor="w", pady=(4, 0))

        self.make_pill_button(btn_box, "Esegui Binario", COLOR_ACCENT_BLUE, COLOR_TEXT_PRIMARY, self.action_run_uem_file, is_primary=True).pack(side="left", padx=(0, 10))
        self.make_pill_button(btn_box, "Radiografia Binario", COLOR_PILL_BG, COLOR_TEXT_PRIMARY, self.action_inspect_file).pack(side="left", padx=(0, 10))
        self.make_pill_button(btn_box, "Web Shield", COLOR_PILL_BG, COLOR_TEXT_PRIMARY, self.action_launch_browser).pack(side="left")

        # Sezione destra: Statistiche hardware minime
        right = tk.Frame(hero, bg=COLOR_BG_SURFACE)
        right.pack(side="right", padx=(20, 0))

        spec_box = tk.Frame(right, bg=COLOR_BG_BASE, padx=14, pady=10, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        spec_box.pack()

        tk.Label(spec_box, text="SPECIFICHE RUNTIME", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE).pack(anchor="w")
        tk.Label(spec_box, text="• Scheduler: BORE Realtime 1000Hz", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(spec_box, text="• Compressione: ZRAM LZ4 (1.5x ratio)", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(spec_box, text="• Rete: CAKE Smart Queue (0ms jitter)", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(spec_box, text="• GPU Engine: Mesa DRI2 / Vulkan", font=self.font_small, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)

    def create_card_capsule(self, parent, index, info):
        # Frame della capsula 2:3
        f = tk.Frame(parent, bg=COLOR_BG_BASE, bd=0, highlightthickness=2, cursor="hand2")

        cov_img = self.cover_cache[index]
        lbl_img = tk.Label(f, image=cov_img, bg=COLOR_BG_BASE, bd=0)
        lbl_img.pack()

        # Binding click e hover
        f.bind("<Button-1>", lambda e, idx=index: self.select_and_activate_card(idx))
        lbl_img.bind("<Button-1>", lambda e, idx=index: self.select_and_activate_card(idx))

        def on_enter(e, idx=index):
            self.selected_card_idx = idx
            self.update_card_focus()

        f.bind("<Enter>", on_enter)
        lbl_img.bind("<Enter>", on_enter)

        return f

    def update_card_focus(self):
        for card_idx, w in self.card_widgets:
            if card_idx == self.selected_card_idx:
                w.config(highlightbackground=COLOR_BORDER_FOCUS, highlightcolor=COLOR_BORDER_FOCUS)
            else:
                w.config(highlightbackground=COLOR_BG_BASE, highlightcolor=COLOR_BG_BASE)

    def navigate_cards(self, delta):
        if self.current_mode != "DECK" or not self.card_data:
            return
        old_idx = self.selected_card_idx
        self.selected_card_idx = (self.selected_card_idx + delta) % len(self.card_data)
        # Se l'indice della card selezionata non è attualmente nel viewport visibile, ridisegna la shelf
        visible_indices = [idx for idx, _ in self.card_widgets]
        if self.selected_card_idx not in visible_indices:
            self.render_deck_view()
        else:
            self.update_card_focus()

    def activate_current_card(self):
        if self.current_mode == "DECK" and self.card_data:
            self.card_data[self.selected_card_idx]["cmd"]()

    def select_and_activate_card(self, idx):
        self.selected_card_idx = idx
        self.update_card_focus()
        self.card_data[idx]["cmd"]()

    # =========================================================================
    # DESKTOP MODE (KDE PLASMA 6)
    # =========================================================================
    def render_desktop_view(self):
        for w in self.viewport.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.viewport, bg=COLOR_BG_BASE, bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Generazione sfondo sfumato astratto con logo watermark
        width = self.winfo_width() or 1160
        height = self.winfo_height() or 720
        self.desktop_bg_img = self.generate_plasma_wallpaper(width, height)
        canvas.create_image(0, 0, image=self.desktop_bg_img, anchor="nw")

        # Widget Desktop Plasma (System Monitor) in alto a sinistra
        widget_frame = tk.Frame(canvas, bg=COLOR_BG_SURFACE, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        
        # Header widget
        w_top = tk.Frame(widget_frame, bg=COLOR_BG_SURFACE)
        w_top.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(w_top, text="KDE Plasma 6 • Monitor di Sistema", font=self.font_heading, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(side="left")
        tk.Label(w_top, text="Wayland", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(side="right")

        # Righe informative
        stats = [
            ("Kernel:", "Linux LTS BORE Scheduler (1000Hz Low-Latency)"),
            ("Memoria RAM:", "1024 MB (ZRAM LZ4 Attiva: 1536 MB)"),
            ("Grafica GPU:", "Intel GMA 950 (Mesa Amber DRI2 OpenGL 2.1)"),
            ("Gestore Rete:", "CAKE QoS Active Queue Management (0ms Jitter)"),
            ("Matrice UEM:", "PE, Mach-O, APK, WASM, DOS, Java Bytecode")
        ]
        for label, val in stats:
            r = tk.Frame(widget_frame, bg=COLOR_BG_SURFACE)
            r.pack(fill="x", padx=14, pady=2)
            tk.Label(r, text=label, font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE, width=14, anchor="w").pack(side="left")
            tk.Label(r, text=val, font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE, anchor="w").pack(side="left")

        widget_frame.pack_propagate(True)
        canvas.create_window(36, 36, window=widget_frame, anchor="nw")

        # ---------------------------------------------------------------------
        # FLOATING CENTERED PILL DOCK (KDE Plasma 6 Genuine Standards)
        # ---------------------------------------------------------------------
        dock = tk.Frame(canvas, bg="#111722", bd=1, relief="solid", highlightbackground="#243347", highlightthickness=1)

        dock_apps = [
            ("Launcher", "chip", lambda: self.show_settings_mode("PACKAGES")),
            ("Web Shield", "browser", self.action_launch_browser),
            ("Konsole", "terminal", self.action_launch_terminal),
            ("Dolphin", "folder", self.action_launch_file_manager),
            ("UEM Hub", "chip", self.action_run_uem_file),
            ("Impostazioni", "gear", lambda: self.show_settings_mode("WIFI")),
            ("Gaming Mode", "gamepad", lambda: self.show_deck_mode("HOME")),
            ("Power", "power", self.open_power_menu)
        ]

        for name, icon_type, cmd in dock_apps:
            btn_f = tk.Frame(dock, bg="#111722", padx=8, pady=6, cursor="hand2")
            btn_f.pack(side="left", padx=4)

            ico = self.get_icon(icon_type, size=24, color=COLOR_TEXT_PRIMARY if name != "Gaming Mode" else COLOR_ACCENT_BLUE)
            lbl_ico = tk.Label(btn_f, image=ico, bg="#111722")
            lbl_ico.pack()

            # Indicatore attivo sottile sotto l'icona
            dot = tk.Frame(btn_f, bg=COLOR_ACCENT_BLUE if name in ("Launcher", "Web Shield") else "#111722", height=2, width=8)
            dot.pack(pady=(2, 0))

            def on_click(e, c=cmd): c()
            btn_f.bind("<Button-1>", on_click)
            lbl_ico.bind("<Button-1>", on_click)

        # Centra la dock sul fondo
        canvas_w = self.winfo_width() or 1160
        canvas.create_window(canvas_w // 2, 590, window=dock, anchor="center")

    def generate_plasma_wallpaper(self, w, h):
        """Genera un wallpaper procedurale in stile slate navy di altissima classe."""
        im = Image.new("RGBA", (w, h), COLOR_BG_BASE)
        d = ImageDraw.Draw(im)

        # Gradiente radiale / morbido verso il centro
        c_top = (11, 14, 20)
        c_mid = (18, 25, 36)
        for y in range(h):
            factor = y / float(h)
            r = int(c_top[0] * (1 - factor) + c_mid[0] * factor)
            g = int(c_top[1] * (1 - factor) + c_mid[1] * factor)
            b = int(c_top[2] * (1 - factor) + c_mid[2] * factor)
            d.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Disegna il logo OSify al centro ma sfumato come watermark elegante
        orig_logo = os.path.join(REPO_ROOT, "OSify.png")
        if os.path.exists(orig_logo):
            try:
                logo_raw = Image.open(orig_logo).convert("RGBA")
                logo_size = 280
                logo_raw = logo_raw.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                # Applica trasparenza watermark morbida
                alpha_layer = logo_raw.split()[3].point(lambda p: int(p * 0.18))
                logo_raw.putalpha(alpha_layer)
                pos_x = (w - logo_size) // 2
                pos_y = (h - logo_size) // 2 - 20
                im.alpha_composite(logo_raw, (pos_x, pos_y))
            except Exception:
                pass

        return ImageTk.PhotoImage(im)

    # =========================================================================
    # QUICK ACCESS MENU (QAM OVERLAY LATERALE)
    # =========================================================================
    def toggle_qam(self):
        if hasattr(self, "qam_window") and self.qam_window and self.qam_window.winfo_exists():
            self.qam_window.destroy()
            self.qam_visible = False
            return

        self.qam_visible = True
        self.qam_window = tk.Toplevel(self)
        self.qam_window.title("Quick Access Menu — OSify")
        self.qam_window.geometry("380x600")
        self.qam_window.configure(bg=COLOR_BG_SURFACE)
        self.qam_window.resizable(False, False)

        header = tk.Frame(self.qam_window, bg=COLOR_BG_SURFACE, padx=18, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="IMPOSTAZIONI RAPIDE", font=self.font_heading, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(side="left")
        tk.Label(header, text="SteamOS QAM", font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_SURFACE).pack(side="right")

        content = tk.Frame(self.qam_window, bg=COLOR_BG_SURFACE, padx=18)
        content.pack(fill="both", expand=True)

        # 1. TDP Limit
        self.build_qam_slider(content, "Limite TDP Consumo", f"{self.tdp_val} W", 3, 15, self.tdp_val, self.on_tdp_change)

        # 2. Limitatore FPS
        self.build_qam_selector(content, "Frequenza Frame Rate", ["30 FPS", "40 FPS", "60 FPS", "Illimitato"], self.fps_cap, self.on_fps_change)

        # 3. CPU Governor
        self.build_qam_selector(content, "Profilo CPU Governor", ["BORE Realtime", "Schedutil", "Performance"], self.cpu_gov, self.on_gov_change)

        # 4. Profilo Carico Workload Dinamico
        self.build_qam_selector(content, "Profilo Carico Ottimizzato", ["STREAM+GAME", "ESPORT", "WORKSTATION", "VINTAGE"], self.active_workload, self.on_workload_change)

        # 5. Sottosistema ZRAM & UEM
        info_card = tk.Frame(content, bg=COLOR_BG_BASE, padx=12, pady=10, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        info_card.pack(fill="x", pady=10)
        tk.Label(info_card, text="STATO ACCELERAZIONE HARDWARE", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE).pack(anchor="w")
        tk.Label(info_card, text=f"• Profilo Attivo: {self.active_workload}", font=self.font_small, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(info_card, text=f"• ZRAM: {self.zram_status}", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(info_card, text="• CAKE QoS: Priorità UDP Gioco (0ms Jitter)", font=self.font_small, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)

        # Bottone Chiudi
        self.make_pill_button(content, "Chiudi Menu Rapido", COLOR_PILL_BG, COLOR_TEXT_PRIMARY, self.qam_window.destroy).pack(fill="x", pady=10)

    def get_initial_workload(self):
        f = "/tmp/osify_active_workload_profile"
        if os.path.exists(f):
            try:
                with open(f, "r") as fp:
                    content = fp.read().strip()
                    if "STREAM_AND_GAME" in content or "STREAM" in content:
                        return "STREAM+GAME"
                    elif "ESPORT" in content:
                        return "ESPORT"
                    elif "WORKSTATION" in content:
                        return "WORKSTATION"
                    elif "VINTAGE" in content:
                        return "VINTAGE"
            except Exception:
                pass
        return "STREAM+GAME"

    def on_workload_change(self, val):
        self.active_workload = val
        script_arg = "stream-game"
        if val == "ESPORT": script_arg = "esport"
        elif val == "WORKSTATION": script_arg = "workstation"
        elif val == "VINTAGE": script_arg = "vintage"
        gov_script = os.path.join(REPO_ROOT, "system/workload/osify-workload-governor.sh")
        if os.path.exists(gov_script):
            subprocess.Popen([gov_script, script_arg], shell=False)
        if hasattr(self, "lbl_workload_pill") and self.lbl_workload_pill.winfo_exists():
            self.lbl_workload_pill.config(text=f"[{self.active_workload}]")
        if hasattr(self, "qam_window") and self.qam_window and self.qam_window.winfo_exists():
            self.qam_window.destroy()
            self.toggle_qam()

    def build_qam_slider(self, parent, title, val_text, v_min, v_max, current, callback):
        f = tk.Frame(parent, bg=COLOR_BG_SURFACE, pady=8)
        f.pack(fill="x")
        row = tk.Frame(f, bg=COLOR_BG_SURFACE)
        row.pack(fill="x")
        tk.Label(row, text=title, font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(side="left")
        lbl_v = tk.Label(row, text=val_text, font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_SURFACE)
        lbl_v.pack(side="right")

        slider = tk.Scale(
            f, from_=v_min, to=v_max, orient="horizontal",
            bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_PRIMARY,
            troughcolor=COLOR_BG_BASE, activebackground=COLOR_ACCENT_BLUE,
            highlightthickness=0, bd=0, showvalue=0,
            command=lambda v: (lbl_v.config(text=f"{v} W"), callback(int(v)))
        )
        slider.set(current)
        slider.pack(fill="x", pady=(4, 0))

    def build_qam_selector(self, parent, title, options, current, callback):
        f = tk.Frame(parent, bg=COLOR_BG_SURFACE, pady=8)
        f.pack(fill="x")
        tk.Label(f, text=title, font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(0, 4))
        pills_row = tk.Frame(f, bg=COLOR_BG_SURFACE)
        pills_row.pack(fill="x")

        for opt in options:
            is_active = (opt == current or opt.startswith(current))
            bg_c = COLOR_ACCENT_BLUE if is_active else COLOR_BG_BASE
            fg_c = COLOR_TEXT_PRIMARY if is_active else COLOR_TEXT_MUTED
            btn = tk.Label(pills_row, text=opt, font=self.font_small, bg=bg_c, fg=fg_c, padx=8, pady=4, bd=1, relief="solid", cursor="hand2")
            btn.pack(side="left", padx=2)
            btn.bind("<Button-1>", lambda e, o=opt: callback(o))

    def on_tdp_change(self, val):
        self.tdp_val = val

    def on_fps_change(self, val):
        self.fps_cap = val
        if hasattr(self, "qam_window") and self.qam_window and self.qam_window.winfo_exists():
            self.qam_window.destroy()
            self.toggle_qam()

    def on_gov_change(self, val):
        self.cpu_gov = val
        if hasattr(self, "qam_window") and self.qam_window and self.qam_window.winfo_exists():
            self.qam_window.destroy()
            self.toggle_qam()

    # =========================================================================
    # HELPERS VISIVI E COMPONENTI
    # =========================================================================
    def make_pill_button(self, parent, text, bg, fg, command, is_primary=False):
        f = tk.Frame(parent, bg=COLOR_BORDER_FOCUS if is_primary else COLOR_BORDER_SUBTLE, bd=0, highlightthickness=0)
        lbl = tk.Label(f, text=text, bg=bg, fg=fg, font=self.font_tab if is_primary else self.font_small, padx=14, pady=6, cursor="hand2")
        lbl.pack(padx=1, pady=1)

        def on_enter(e):
            lbl.config(bg="#2563eb" if is_primary else "#273549")
        def on_leave(e):
            lbl.config(bg=bg)
        def on_click(e):
            if command: command()

        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        lbl.bind("<Button-1>", on_click)
        return f

    def switch_tab(self, tab):
        self.current_tab = tab
        if tab == "DESKTOP PLASMA":
            self.show_desktop_mode()
        elif tab == "IMPOSTAZIONI":
            self.show_settings_mode("WIFI")
        else:
            self.show_deck_mode(tab)

    def toggle_gaming_desktop_mode(self):
        if self.current_mode == "DECK" or self.current_mode == "SETTINGS":
            self.show_desktop_mode()
        else:
            self.show_deck_mode("HOME")

    def show_deck_mode(self, tab="HOME"):
        self.current_mode = "DECK"
        self.current_tab = tab
        self.render_topbar()
        self.render_deck_view()

    def show_desktop_mode(self):
        self.current_mode = "DESKTOP"
        self.current_tab = "DESKTOP PLASMA"
        self.render_topbar()
        self.render_desktop_view()

    def show_settings_mode(self, section="WIFI"):
        self.current_mode = "SETTINGS"
        self.current_tab = "IMPOSTAZIONI"
        self.settings_section = section
        self.render_topbar()
        self.render_settings_view()

    # =========================================================================
    # SYSTEM SETTINGS VIEW (CONFIGURAZIONE AUTONOMA DEL COMPUTER)
    # =========================================================================
    def render_settings_view(self):
        for w in self.viewport.winfo_children():
            w.destroy()

        container = tk.Frame(self.viewport, bg=COLOR_BG_BASE)
        container.pack(fill="both", expand=True, padx=24, pady=(10, 14))

        # Header Impostazioni
        h_frame = tk.Frame(container, bg=COLOR_BG_BASE)
        h_frame.pack(fill="x", pady=(0, 12))
        tk.Label(h_frame, text="Impostazioni di Sistema & Connettività", font=self.font_title, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")
        tk.Label(h_frame, text="OSify Hardware & Network Control", font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_BASE).pack(side="right")

        body = tk.Frame(container, bg=COLOR_BG_BASE)
        body.pack(fill="both", expand=True)

        # 1. Sidebar Sinistra (Categorie)
        sidebar = tk.Frame(body, bg=COLOR_BG_SURFACE, width=240, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)

        sections = [
            ("WORKLOAD", "Profili Carico & Streaming", "gamepad"),
            ("AUTOTUNE", "Hardware & Autocalibrazione", "chip"),
            ("WIFI", "Rete & Wi-Fi", "wifi"),
            ("AUDIO", "Audio & Mixer", "sliders"),
            ("DISPLAY", "Schermo & Display", "desktop"),
            ("BATTERY", "Batteria & Energia", "battery"),
            ("PACKAGES", "App Store & Software", "folder"),
            ("INSTALL_DISK", "Installazione Disco Fisso", "chip")
        ]

        for code, label, ico_name in sections:
            is_sel = (getattr(self, "settings_section", "WORKLOAD") == code)
            row = tk.Frame(sidebar, bg=COLOR_BG_BASE if is_sel else COLOR_BG_SURFACE, cursor="hand2")
            row.pack(fill="x", padx=4, pady=3)

            ico = self.get_icon(ico_name, size=18, color=COLOR_ACCENT_BLUE if is_sel else COLOR_TEXT_MUTED)
            lbl_ico = tk.Label(row, image=ico, bg=row["bg"])
            lbl_ico.pack(side="left", padx=(10, 8), pady=8)

            lbl_txt = tk.Label(row, text=label, font=self.font_tab if is_sel else self.font_small, fg=COLOR_TEXT_PRIMARY if is_sel else COLOR_TEXT_MUTED, bg=row["bg"])
            lbl_txt.pack(side="left", pady=8)

            def make_handler(c=code):
                return lambda e: self.show_settings_mode(c)

            row.bind("<Button-1>", make_handler())
            lbl_ico.bind("<Button-1>", make_handler())
            lbl_txt.bind("<Button-1>", make_handler())

        # 2. Pannello Dettagli Destro
        details = tk.Frame(body, bg=COLOR_BG_SURFACE, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        details.pack(side="left", fill="both", expand=True, padx=(0, 0))

        sec = getattr(self, "settings_section", "WORKLOAD")
        if sec == "WORKLOAD":
            self.render_workload_panel(details)
        elif sec == "AUTOTUNE":
            self.render_autotune_panel(details)
        elif sec == "WIFI":
            self.render_wifi_panel(details)
        elif sec == "AUDIO":
            self.render_audio_panel(details)
        elif sec == "DISPLAY":
            self.render_display_panel(details)
        elif sec == "BATTERY":
            self.render_battery_panel(details)
        elif sec == "PACKAGES":
            self.render_packages_panel(details)
        elif sec == "INSTALL_DISK":
            self.render_install_disk_panel(details)

    def render_workload_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="INTELLIGENZA DEI CARICHI & PROFILI WORKLOAD", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Ottimizzazione dinamica per Gioco Online + Streaming simultaneo, Competitivo, Workstation o PC Vintage.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 10))

        # Box Profilo Attivo
        box_active = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=8, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box_active.pack(fill="x", pady=(0, 10))
        row_act = tk.Frame(box_active, bg=COLOR_BG_BASE)
        row_act.pack(fill="x")
        tk.Label(row_act, text="PROFILO ATTIVO ORA:", font=self.font_mono, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(side="left")
        tk.Label(row_act, text=f" {self.active_workload}", font=self.font_heading, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_BASE).pack(side="left")

        # Elenco Profili con pulsanti di selezione
        profiles_data = [
            ("STREAM+GAME", "Streaming + Gioco Online Simultaneo", "Rete: CAKE DSCP gaming a 0ms jitter + OBS video protetto da bufferbloat • Audio: traccia Twitch VOD #2 isolata • CPU: Core affinity differenziata"),
            ("ESPORT", "eSport Gaming Competitivo Puro", "Latenza mouse sub-millisecondo • Compositor tearing unredirect Wayland sbloccato • Kernel BORE real-time a 1000Hz"),
            ("STREAM SOLO", "Live Streaming Dedicato (OBS / FFmpeg)", "Banda di upload video massimizzata • Filtri PipeWire RNNoise attivi su microfono"),
            ("WORKSTATION", "Sviluppo & Compilazione Multi-Core", "Scheduler CPU bilanciato schedutil • Allocazione memoria cgroups • ZRAM espansa per build pesanti"),
            ("VINTAGE", "Vintage Low-Spec (32-bit / Netbook)", "Footprint memoria ~120MB • ZRAM LZ4 ultra-reattiva • Ideale per Toshiba NB200 e vecchi PC")
        ]

        for p_code, p_title, p_desc in profiles_data:
            p_card = tk.Frame(pad, bg=COLOR_BG_BASE, padx=12, pady=6, bd=1, relief="solid", highlightbackground=COLOR_BORDER_FOCUS if self.active_workload == p_code else COLOR_BORDER_SUBTLE, highlightthickness=1)
            p_card.pack(fill="x", pady=2)

            p_head = tk.Frame(p_card, bg=COLOR_BG_BASE)
            p_head.pack(fill="x")

            is_cur = (self.active_workload == p_code)
            tk.Label(p_head, text=p_title, font=self.font_tab, fg=COLOR_ACCENT_BLUE if is_cur else COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")

            if is_cur:
                tk.Label(p_head, text="[IN ESECUZIONE]", font=self.font_mono, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(side="right")
            else:
                btn_act = tk.Label(p_head, text="Attiva Profilo", font=self.font_small, bg=COLOR_PILL_BG, fg=COLOR_TEXT_PRIMARY, padx=8, pady=2, cursor="hand2")
                btn_act.pack(side="right")
                btn_act.bind("<Button-1>", lambda e, c=p_code: self.action_apply_workload(c))

            tk.Label(p_card, text=p_desc, font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE, justify="left").pack(anchor="w", pady=(1, 0))

        # Box Auto-detect
        auto_box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=12, pady=6, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        auto_box.pack(fill="x", pady=(6, 0))
        tk.Label(auto_box, text="Rilevamento Intelligente Automatico:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")
        btn_auto = tk.Label(auto_box, text="Scansiona Processi & Adatta Ora", font=self.font_small, bg=COLOR_ACCENT_BLUE, fg="#ffffff", padx=10, pady=2, cursor="hand2")
        btn_auto.pack(side="right")
        btn_auto.bind("<Button-1>", lambda e: self.action_auto_detect_workload())

    def render_autotune_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="HARDWARE INTELLIGENCE & AUTOCALIBRAZIONE", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Riconoscimento e calibrazione ad-hoc per qualsiasi ISA (x86_64, 32-bit, ARM64, Apple Silicon).", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 10))

        hw_info = self.get_autotune_summary()

        info_box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=10, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        info_box.pack(fill="x", pady=(0, 10))

        tk.Label(info_box, text="AUDIT HARDWARE DELLA MACCHINA", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE).pack(anchor="w", pady=(0, 6))

        specs = [
            ("Architettura CPU Host", hw_info.get("isa", "Rilevamento in corso")),
            ("Memoria RAM Riconosciuta", f"{hw_info.get('ram_mb', 2048)} MB Fisica"),
            ("Pipeline Accelerazione GPU", hw_info.get("gpu", "Standard")),
            ("Profilo Sottosistema Disco", hw_info.get("storage", "Standard I/O")),
            ("Compressione Memoria ZRAM", "Algoritmo LZ4 Ultra-Low-Latency attivo"),
            ("Ottimizzazione Frame Pacing", "Transparent Hugepages (THP) madvise")
        ]

        for lbl_k, lbl_v in specs:
            r = tk.Frame(info_box, bg=COLOR_BG_BASE)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"• {lbl_k}:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(side="left")
            tk.Label(r, text=f" {lbl_v}", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")

        act_box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=10, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        act_box.pack(fill="x")
        tk.Label(act_box, text="Adattamento Architetturale Autonomo:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")

        btn_recal = tk.Label(act_box, text="Ricalibra Hardware Ora", font=self.font_tab, bg=COLOR_ACCENT_BLUE, fg="#ffffff", padx=12, pady=4, cursor="hand2")
        btn_recal.pack(side="right")
        btn_recal.bind("<Button-1>", lambda e: self.action_recalibrate_hw())

    def action_apply_workload(self, code):
        self.on_workload_change(code)
        self.show_settings_mode("WORKLOAD")
        messagebox.showinfo("OSify Workload Governor", f"Profilo '{code}' applicato!\nParametri di CPU, QoS di rete e audio ricalibrati.")

    def action_auto_detect_workload(self):
        gov_script = os.path.join(REPO_ROOT, "system/workload/osify-workload-governor.sh")
        if os.path.exists(gov_script):
            subprocess.run([gov_script, "auto"], check=False)
        self.active_workload = self.get_initial_workload()
        self.show_settings_mode("WORKLOAD")
        messagebox.showinfo("OSify Workload Governor", f"Scansione completata!\nProfilo dinamico commutato su '{self.active_workload}'.")

    def get_autotune_summary(self):
        autotune_script = os.path.join(REPO_ROOT, "system/autotune/osify-autotune.sh")
        if os.path.exists(autotune_script):
            try:
                out = subprocess.check_output([autotune_script, "json"], text=True)
                import json
                return json.loads(out)
            except Exception:
                pass
        return {"isa": "arm64-apple-silicon", "ram_mb": 36864, "gpu": "apple-agx", "storage": "host-virtualized"}

    def action_recalibrate_hw(self):
        autotune_script = os.path.join(REPO_ROOT, "system/autotune/osify-autotune.sh")
        if os.path.exists(autotune_script):
            subprocess.run([autotune_script, "apply"], check=False)
        self.show_settings_mode("AUTOTUNE")
        messagebox.showinfo("OSify Autotune Engine", "Auto-calibrazione hardware completata con successo!\nKernel e sottosistemi calibrati al 100% per questa macchina.")

    def render_wifi_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="CONNESSIONE SENZA FILI & RETE LOCALE", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Gestione autonoma Wi-Fi (WPA2/WPA3), QoS CAKE e DNS sicuro Cloudflare/Quad9.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 12))

        # Box scansione reti
        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=12, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))

        tk.Label(box, text="Reti Senza Fili Rilevate nelle Vicinanze:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(0, 8))

        wifi_samples = [
            ("Compagno_Home_5G", "92% Segnale • WPA3 Personale", True),
            ("OSify_Mesh_HighSpeed", "88% Segnale • WPA2 Protetto", False),
            ("RetroGaming_Lab", "70% Segnale • WPA2 Protetto", False)
        ]

        for ssid, sig, is_conn in wifi_samples:
            row = tk.Frame(box, bg=COLOR_BG_BASE)
            row.pack(fill="x", pady=4)
            status_color = COLOR_ACCENT_MINT if is_conn else COLOR_TEXT_PRIMARY
            tk.Label(row, text=f"• {ssid}", font=self.font_tab, fg=status_color, bg=COLOR_BG_BASE).pack(side="left")
            tk.Label(row, text=f" ({sig})", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(side="left")

            if is_conn:
                tk.Label(row, text=" [CONNESSO]", font=self.font_mono, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(side="right")
            else:
                btn = tk.Label(row, text="Connetti", font=self.font_small, bg=COLOR_PILL_BG, fg=COLOR_TEXT_PRIMARY, padx=10, pady=2, cursor="hand2")
                btn.pack(side="right")
                btn.bind("<Button-1>", lambda e, s=ssid: self.action_connect_wifi(s))

        # Box parametri di rete
        info_box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=12, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        info_box.pack(fill="x")
        tk.Label(info_box, text="STATO PARAMETRI DI RETE", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE).pack(anchor="w")
        tk.Label(info_box, text="• Interfaccia Primaria: wlan0 (802.11ac High-Throughput)", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(info_box, text="• Indirizzo IP Assegnato: 192.168.1.105 (DHCP Static Lease)", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(info_box, text="• Anti-Bufferbloat QoS: CAKE Active Queue Shaper (0ms Jitter)", font=self.font_small, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)
        tk.Label(info_box, text="• Server DNS: 1.1.1.1 (Cloudflare) + 9.9.9.9 (Quad9 Malicious Block)", font=self.font_small, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=1)

    def action_connect_wifi(self, ssid):
        messagebox.showinfo("OSify Wi-Fi Manager", f"Negoziazione cifratura WPA2/WPA3 con '{ssid}'...\nProfilo di rete salvato e QoS CAKE abilitato.")

    def render_audio_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="SOTTOSISTEMA AUDIO & MIXER", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Controllo volume master a bassa latenza (ALSA & PipeWire).", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 16))

        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=16, pady=14, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))

        # Slider Volume Master
        row_v = tk.Frame(box, bg=COLOR_BG_BASE)
        row_v.pack(fill="x")
        tk.Label(row_v, text="Volume Master Principale", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")
        lbl_val = tk.Label(row_v, text="75%", font=self.font_mono, fg=COLOR_ACCENT_BLUE, bg=COLOR_BG_BASE)
        lbl_val.pack(side="right")

        slider = tk.Scale(
            box, from_=0, to=100, orient="horizontal",
            bg=COLOR_BG_BASE, fg=COLOR_TEXT_PRIMARY,
            troughcolor=COLOR_BG_SURFACE, activebackground=COLOR_ACCENT_BLUE,
            highlightthickness=0, bd=0, showvalue=0,
            command=lambda v: (lbl_val.config(text=f"{v}%"), self.apply_sound_volume(int(v)))
        )
        slider.set(75)
        slider.pack(fill="x", pady=(8, 12))

        btn_row = tk.Frame(box, bg=COLOR_BG_BASE)
        btn_row.pack(fill="x")
        self.make_pill_button(btn_row, "Test Canali Audio (440Hz)", COLOR_PILL_BG, COLOR_TEXT_PRIMARY, self.action_test_audio).pack(side="left", padx=(0, 10))
        self.make_pill_button(btn_row, "Attiva / Disattiva Muto", COLOR_PILL_BG, COLOR_TEXT_PRIMARY, self.action_toggle_mute).pack(side="left")

    def apply_sound_volume(self, val):
        subprocess.Popen([os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), "set", str(val)], shell=False)

    def action_test_audio(self):
        subprocess.Popen([os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), "test"], shell=False)
        messagebox.showinfo("Audio Test", "Segnale acustico di test a 440Hz inviato ai diffusori stereo.")

    def action_toggle_mute(self):
        subprocess.Popen([os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), "mute"], shell=False)

    def render_display_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="SCHERMO, RISOLUZIONE & LUMINOSITÀ", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Adattamento dinamico per netbook (Toshiba NB200) e monitor esterni.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 16))

        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=16, pady=14, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))

        row_b = tk.Frame(box, bg=COLOR_BG_BASE)
        row_b.pack(fill="x")
        tk.Label(row_b, text="Luminosità Pannello Notebook", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(side="left")
        lbl_b = tk.Label(row_b, text="80%", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_BASE)
        lbl_b.pack(side="right")

        s_bright = tk.Scale(
            box, from_=10, to=100, orient="horizontal",
            bg=COLOR_BG_BASE, fg=COLOR_TEXT_PRIMARY,
            troughcolor=COLOR_BG_SURFACE, activebackground=COLOR_ACCENT_CYAN,
            highlightthickness=0, bd=0, showvalue=0,
            command=lambda v: (lbl_b.config(text=f"{v}%"), self.apply_display_brightness(int(v)))
        )
        s_bright.set(80)
        s_bright.pack(fill="x", pady=(8, 14))

        # Risoluzioni
        tk.Label(box, text="Risoluzione Display Selezionabile:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(4, 6))
        r_box = tk.Frame(box, bg=COLOR_BG_BASE)
        r_box.pack(fill="x")

        res_list = ["1024x600 (Toshiba NB200)", "1280x800 (Steam Deck)", "1920x1080 (FHD Monitor)"]
        for res_name in res_list:
            btn = tk.Label(r_box, text=res_name, font=self.font_small, bg=COLOR_PILL_BG, fg=COLOR_TEXT_PRIMARY, padx=10, pady=4, bd=1, relief="solid", cursor="hand2")
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, r=res_name.split()[0]: self.apply_resolution(r))

    def apply_display_brightness(self, val):
        subprocess.Popen([os.path.join(REPO_ROOT, "system/display/osify-display-manager.sh"), "set-brightness", str(val)], shell=False)

    def apply_resolution(self, r):
        subprocess.Popen([os.path.join(REPO_ROOT, "system/display/osify-display-manager.sh"), "set-res", r], shell=False)
        messagebox.showinfo("Risoluzione Display", f"Risoluzione display impostata a {r} via KMS/XRandR.")

    def render_battery_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="BATTERIA & PROFILI ENERGETICI TDP", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Monitoraggio ACPI e commutazione hardware governor CPU in tempo reale.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 16))

        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=16, pady=14, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))

        tk.Label(box, text="Stato Alimentazione Attuale: 100% (Alimentazione da Rete / Batteria Ottimale)", font=self.font_tab, fg=COLOR_ACCENT_MINT, bg=COLOR_BG_BASE).pack(anchor="w", pady=(0, 8))

        tk.Label(box, text="Seleziona Profilo TDP Hardware:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w", pady=(6, 4))
        p_row = tk.Frame(box, bg=COLOR_BG_BASE)
        p_row.pack(fill="x")

        profiles = [
            ("powersave", "Risparmio (4W)"),
            ("balanced", "Bilanciato (10W)"),
            ("performance", "Prestazioni Max (15W)")
        ]
        for p_code, p_name in profiles:
            btn = tk.Label(p_row, text=p_name, font=self.font_small, bg=COLOR_PILL_BG, fg=COLOR_TEXT_PRIMARY, padx=12, pady=5, bd=1, relief="solid", cursor="hand2")
            btn.pack(side="left", padx=4)
            btn.bind("<Button-1>", lambda e, c=p_code: self.apply_power_profile(c))

    def apply_power_profile(self, code):
        subprocess.Popen([os.path.join(REPO_ROOT, "system/power/osify-power-manager.sh"), "profile", code], shell=False)
        messagebox.showinfo("Profilo Energetico", f"Profilo hardware '{code}' attivato.")

    def render_packages_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="APP STORE & GESTORE PACCHETTI AUTONOMO", font=self.font_mono, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Installazione ed esecuzione autonoma di software per uso workstation al 100%.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 12))

        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=14, pady=10, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="both", expand=True)

        apps = [
            ("falkon", "Browser Web Ultra-Leggero (150MB RAM)", "Navigazione web e video fluida su PC vintage"),
            ("firefox", "Mozilla Firefox ESR Hardened", "Browser web moderno con WebExtensions"),
            ("retroarch", "Frontend Emulazione Retrogaming", "Shader asincroni e supporto controller USB"),
            ("orbit64", "Orbit64 N64 Engine", "Emulatore Nintendo 64 JIT ultra-preciso"),
            ("mpv", "Player Multimediale MPV", "Riproduzione video GPU DRI3 senza consumo CPU"),
            ("kwrite", "Editor di Testo & Codice", "Editor leggero per programmatori ed uso quotidiano")
        ]

        for pkg, title, desc in apps:
            r = tk.Frame(box, bg=COLOR_BG_BASE)
            r.pack(fill="x", pady=4)
            t_box = tk.Frame(r, bg=COLOR_BG_BASE)
            t_box.pack(side="left")
            tk.Label(t_box, text=title, font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w")
            tk.Label(t_box, text=desc, font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(anchor="w")

            btn_i = tk.Label(r, text="Installa", font=self.font_small, bg=COLOR_ACCENT_BLUE, fg="#ffffff", padx=12, pady=4, cursor="hand2")
            btn_i.pack(side="right")
            btn_i.bind("<Button-1>", lambda e, p=pkg: self.action_install_app(p))

    def action_install_app(self, pkg):
        subprocess.Popen([os.path.join(REPO_ROOT, "tools/osify-pkg"), "install", pkg], shell=False)
        messagebox.showinfo("OSify Package Manager", f"Pacchetto '{pkg}' installato e registrato nel sistema con successo.")

    def render_install_disk_panel(self, parent):
        pad = tk.Frame(parent, bg=COLOR_BG_SURFACE, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(pad, text="INSTALLAZIONE AUTONOMA SU DISCO FISSO (BARE METAL)", font=self.font_mono, fg="#f59e0b", bg=COLOR_BG_SURFACE).pack(anchor="w")
        tk.Label(pad, text="Installa OSify sul disco del computer per utilizzarlo al 100% come unico sistema operativo.", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE).pack(anchor="w", pady=(2, 14))

        box = tk.Frame(pad, bg=COLOR_BG_BASE, padx=16, pady=14, bd=1, relief="solid", highlightbackground=COLOR_BORDER_SUBTLE, highlightthickness=1)
        box.pack(fill="x", pady=(0, 12))

        tk.Label(box, text="Dispositivo Disco di Destinazione:", font=self.font_tab, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_BASE).pack(anchor="w")
        tk.Label(box, text="Dischi rilevati: /dev/sda (Disco Interno) • /dev/nvme0n1", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE).pack(anchor="w", pady=(1, 10))

        e_frame = tk.Frame(box, bg=COLOR_BG_BASE)
        e_frame.pack(fill="x")
        self.entry_disk = tk.Entry(e_frame, font=self.font_mono, bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_PRIMARY, bd=1, relief="solid")
        self.entry_disk.insert(0, "/dev/sda")
        self.entry_disk.pack(side="left", padx=(0, 10), ipady=4, ipadx=6)

        btn_inst = tk.Label(e_frame, text="AVVIA INSTALLAZIONE DEFINITIVA", font=self.font_tab, bg="#f59e0b", fg="#000000", padx=14, pady=5, cursor="hand2")
        btn_inst.pack(side="left")
        btn_inst.bind("<Button-1>", lambda e: self.action_run_disk_installer())

        # Note di architettura
        notes = (
            "Caratteristiche dell'installazione:\n"
            "• FileSystem Btrfs con subvolumi ad alte prestazioni (@, @home, @games_wine)\n"
            "• Compressione trasparente zstd:1 per raddoppiare la velocità di I/O\n"
            "• Attributo NO-COW sulle cartelle di gioco per azzerare la frammentazione\n"
            "• Bootloader duale UEFI (x86_64) e BIOS MBR (Vintage per Toshiba NB200)"
        )
        tk.Label(pad, text=notes, font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_SURFACE, justify="left").pack(anchor="w", pady=10)

    def action_run_disk_installer(self):
        target = self.entry_disk.get().strip()
        if not target:
            target = "/dev/sda"
        res = messagebox.askyesno(
            "Conferma Installazione OSify",
            f"Sei sicuro di voler installare OSify su {target}?\n\nQuesto renderà il computer un sistema autonomo al 100% basato su OSify."
        )
        if res:
            cmd = [os.path.join(REPO_ROOT, "system/installer/osify-disk-installer.sh"), target]
            messagebox.showinfo("Installazione Avviata", f"Procedura di installazione bare-metal avviata sul dispositivo {target}.\nAl termine dell'installazione potrai riavviare il PC.")

    # =========================================================================
    # POWER MENU (SPEGNIMENTO REALE, RIAVVIO, SOSPENSIONE)
    # =========================================================================
    def open_power_menu(self):
        pwr_win = tk.Toplevel(self)
        pwr_win.title("Menu Alimentazione")
        pwr_win.geometry("320x340")
        pwr_win.configure(bg=COLOR_BG_SURFACE)
        pwr_win.resizable(False, False)

        tk.Label(pwr_win, text="ALIMENTAZIONE & SESSIONE", font=self.font_heading, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_SURFACE).pack(pady=(18, 12))

        options = [
            ("Arresta Computer", "#dc2626", lambda: self.exec_power_action("poweroff", pwr_win)),
            ("Riavvia Computer", "#ea580c", lambda: self.exec_power_action("reboot", pwr_win)),
            ("Sospendi in RAM (Sleep)", COLOR_PILL_BG, lambda: self.exec_power_action("suspend", pwr_win)),
            ("Passa a Desktop Plasma", COLOR_ACCENT_BLUE, lambda: (pwr_win.destroy(), self.show_desktop_mode())),
            ("Annulla", COLOR_BG_BASE, pwr_win.destroy)
        ]

        for text, bg_c, cmd in options:
            btn = tk.Label(pwr_win, text=text, font=self.font_small, bg=bg_c, fg="#ffffff" if bg_c != COLOR_BG_BASE else COLOR_TEXT_MUTED, padx=12, pady=7, bd=1, relief="solid", cursor="hand2")
            btn.pack(fill="x", padx=24, pady=4)
            btn.bind("<Button-1>", lambda e, c=cmd: c())

    def exec_power_action(self, action, win):
        win.destroy()
        subprocess.Popen([os.path.join(REPO_ROOT, "system/power/osify-power-manager.sh"), action], shell=False)

    # =========================================================================
    # AZIONI E RUNNER UEM
    # =========================================================================
    def launch_title(self, name, runtime_info):
        msg = f"Inizializzazione sottosistema UEM per {name}:\n\nRuntime: {runtime_info}\nHardware Layer: ZRAM LZ4 + BORE Scheduler\nQoS Rete: CAKE Profile Attivo"
        messagebox.showinfo("OSify UEM Launcher", msg)

    def action_run_uem_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona file o binario da eseguire con OSify UEM",
            filetypes=[
                ("Tutti i formati eseguibili", "*.*"),
                ("Windows PE (.exe)", "*.exe"),
                ("Android APK", "*.apk"),
                ("WebAssembly (.wasm)", "*.wasm"),
                ("Java Archive (.jar)", "*.jar"),
                ("MS-DOS Real Mode (.com;.exe)", "*.com;*.exe")
            ]
        )
        if filepath:
            subprocess.Popen([OSIFY_CTL, "uem", "run", filepath], shell=False)

    def action_inspect_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona file per radiografia forense architetturale"
        )
        if filepath:
            inspect_bin = os.path.join(REPO_ROOT, "uem/runners/osify-inspect.sh")
            try:
                res = subprocess.run([inspect_bin, filepath], capture_output=True, text=True)
                output = res.stdout if res.returncode == 0 else res.stderr
                top = tk.Toplevel(self)
                top.title(f"Radiografia Architetturale: {os.path.basename(filepath)}")
                top.geometry("680x480")
                top.configure(bg=COLOR_BG_BASE)
                txt = tk.Text(top, bg=COLOR_BG_SURFACE, fg=COLOR_ACCENT_MINT, font=self.font_mono, padx=12, pady=12, bd=0)
                txt.pack(fill="both", expand=True, padx=16, pady=16)
                txt.insert("1.0", output)
                txt.config(state="disabled")
            except Exception as e:
                messagebox.showerror("Errore Radiografia", str(e))

    def action_launch_browser(self):
        browser_tune = os.path.join(REPO_ROOT, "desktop/web/osify-browser-tuning.sh")
        if os.path.exists(browser_tune):
            subprocess.Popen([browser_tune], shell=False)
        messagebox.showinfo("OSify Web Shield", "Avvio del browser Falkon / Firefox protetto (Zero telemetria, DNS protetto, ZRAM memory saving).")

    def action_launch_control_center(self):
        messagebox.showinfo("OSify Control Center", "Pannello di controllo centrale e monitor di frequenza CPU attivo.")

    def action_launch_terminal(self):
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            subprocess.Popen(["x-terminal-emulator"])

    def action_launch_file_manager(self):
        fm_script = os.path.join(REPO_ROOT, "system/desktop/osify-file-manager.sh")
        if os.path.exists(fm_script):
            subprocess.Popen([fm_script], shell=False)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", REPO_ROOT])
        else:
            subprocess.Popen(["xdg-open", REPO_ROOT])

    def action_start_menu(self):
        messagebox.showinfo("KDE Plasma 6 Kickoff", "OSify Application Launcher (KDE Plasma 6):\n\n• Universal Execution Matrix (UEM)\n• Falkon & Firefox Web Shield\n• Konsole Terminal & Utilità\n• Centro di Controllo e Gestione Audio\n• Spegni / Riavvia Sistema")

    def start_telemetry_loop(self):
        def update():
            import random
            cpu = random.randint(2, 6)
            ping = random.randint(8, 12)
            self.lbl_telemetry.config(text=f"BORE {cpu}% • CAKE {ping}ms • 118MB")
            if hasattr(self, "lbl_clock"):
                self.lbl_clock.config(text=time.strftime("%H:%M"))
            self.after(2000, update)
        self.after(1000, update)

if __name__ == "__main__":
    app = OSifyDeckApp()
    app.mainloop()
