#!/usr/bin/env python3
"""
==============================================================================
OSify Deck Shell — SteamOS & KDE Plasma 6 Dual Experience
==============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Interfaccia di nuova generazione con switch istantaneo tra:
  1. SteamOS Gaming Mode (DeckUI Big Picture a card interattive, Quick Settings QAM)
  2. KDE Plasma 6 Desktop Mode (Floating Centered Dock, Dark Cyberpunk Theme)
Nessun elemento obsoleto, zero icone generiche o loghi estranei. 100% OSify.
==============================================================================
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OSIFY_CTL = os.path.join(REPO_ROOT, "tools/osify-ctl")
LOGO_SRC = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-netbook-1024x600.png")
if not os.path.exists(LOGO_SRC):
    LOGO_SRC = os.path.join(REPO_ROOT, "OSify.png")

# Palette Colori SteamOS / KDE Plasma 6 Cyberpunk
COLOR_BG_DARK = "#090b10"
COLOR_BG_CARD = "#121824"
COLOR_BG_CARD_HOVER = "#1c2538"
COLOR_ACCENT_PURPLE = "#8b5cf6"
COLOR_ACCENT_CYAN = "#06b6d4"
COLOR_ACCENT_GREEN = "#10b981"
COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_BORDER = "#1e293b"
COLOR_BORDER_ACTIVE = "#7c3aed"

def make_button(parent, text, bg, fg, command, font=("Helvetica Neue", 10, "bold"), padx=14, pady=6, bd=1, border_color="#334155"):
    f = tk.Frame(parent, bg=border_color, bd=0, highlightthickness=0)
    lbl = tk.Label(f, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady, cursor="hand2")
    lbl.pack(padx=bd, pady=bd)

    def on_enter(e):
        lbl.config(bg="#a855f7" if bg == COLOR_ACCENT_PURPLE else "#22d3ee" if bg == COLOR_ACCENT_CYAN else "#2a374f")
    def on_leave(e):
        lbl.config(bg=bg)
    def on_click(e):
        if command: command()

    lbl.bind("<Enter>", on_enter)
    lbl.bind("<Leave>", on_leave)
    lbl.bind("<Button-1>", on_click)
    return f

class OSifyDeckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSify — Next-Gen Gaming & Desktop Shell")
        self.geometry("1100x680")
        self.minsize(980, 600)
        self.configure(bg=COLOR_BG_DARK)

        self.current_mode = "DECK"  # "DECK" (SteamOS) oppure "DESKTOP" (KDE Plasma 6)
        self.qam_visible = False
        self.tdp_value = 15
        self.governor_value = "BORE Realtime"

        self.setup_fonts()
        self.load_assets()
        self.build_ui()
        self.start_telemetry_loop()

    def setup_fonts(self):
        self.font_title = ("Helvetica Neue", 18, "bold")
        self.font_heading = ("Helvetica Neue", 12, "bold")
        self.font_body = ("Helvetica Neue", 10)
        self.font_small = ("Helvetica Neue", 9)
        self.font_hud = ("Courier New", 10, "bold")

    def load_assets(self):
        self.logo_img = None
        self.bg_img = None
        if os.path.exists(LOGO_SRC):
            try:
                raw = Image.open(LOGO_SRC).convert("RGBA")
                small = raw.resize((36, 36), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(small)
                bg = raw.resize((1100, 680), Image.Resampling.LANCZOS)
                bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
                self.bg_img = ImageTk.PhotoImage(bg)
            except Exception as e:
                print("Errore caricamento asset:", e)

    def build_ui(self):
        # 1. Top Status Bar (Stile SteamOS Top Bar)
        self.topbar = tk.Frame(self, bg="#0d111a", height=52, bd=0, highlightthickness=0)
        self.topbar.pack(side="top", fill="x")
        self.build_topbar()

        # 2. Container Principale dinamico
        self.main_container = tk.Frame(self, bg=COLOR_BG_DARK, bd=0, highlightthickness=0)
        self.main_container.pack(side="top", fill="both", expand=True)

        self.show_deck_mode()

    def build_topbar(self):
        for widget in self.topbar.winfo_children():
            widget.destroy()

        # Sezione Sinistra: Logo OSify & Nome
        left_box = tk.Frame(self.topbar, bg="#0d111a")
        left_box.pack(side="left", padx=15, pady=8)

        if self.logo_img:
            lbl_logo = tk.Label(left_box, image=self.logo_img, bg="#0d111a")
            lbl_logo.pack(side="left", padx=(0, 10))

        lbl_brand = tk.Label(left_box, text="OSify", font=("Helvetica Neue", 15, "bold"), fg=COLOR_ACCENT_PURPLE, bg="#0d111a")
        lbl_brand.pack(side="left")
        lbl_sub = tk.Label(left_box, text=" • SteamOS / KDE Dual-Shell", font=self.font_small, fg=COLOR_TEXT_SECONDARY, bg="#0d111a")
        lbl_sub.pack(side="left", padx=5)

        # Sezione Centro: Mode Switcher (SteamOS Deck <-> KDE Plasma)
        center_box = tk.Frame(self.topbar, bg="#0d111a")
        center_box.pack(side="left", expand=True)

        deck_bg = COLOR_ACCENT_PURPLE if self.current_mode == "DECK" else "#161f30"
        deck_bdr = "#a855f7" if self.current_mode == "DECK" else "#2a374f"
        btn_deck = make_button(
            center_box, "🎮 Gaming Mode (DeckUI)", deck_bg, "#ffffff",
            self.show_deck_mode, font=self.font_heading, padx=16, pady=5, border_color=deck_bdr
        )
        btn_deck.pack(side="left", padx=6)

        desk_bg = COLOR_ACCENT_CYAN if self.current_mode == "DESKTOP" else "#161f30"
        desk_bdr = "#22d3ee" if self.current_mode == "DESKTOP" else "#2a374f"
        btn_desktop = make_button(
            center_box, "🖥️ Desktop Mode (KDE Plasma 6)", desk_bg, "#ffffff",
            self.show_desktop_mode, font=self.font_heading, padx=16, pady=5, border_color=desk_bdr
        )
        btn_desktop.pack(side="left", padx=6)

        # Sezione Destra: HUD Performance & Quick Access Menu Toggle
        right_box = tk.Frame(self.topbar, bg="#0d111a")
        right_box.pack(side="right", padx=15, pady=8)

        self.lbl_telemetry = tk.Label(
            right_box, text="CPU: 3% | RAM: 118MB (ZRAM: LZ4) | CAKE: 0ms",
            font=self.font_hud, fg=COLOR_ACCENT_GREEN, bg="#0d111a"
        )
        self.lbl_telemetry.pack(side="left", padx=15)

        btn_qam = make_button(
            right_box, "⚙️ Impostazioni", "#1e293b", "#ffffff",
            self.toggle_qam, font=self.font_small, padx=10, pady=5, border_color="#334155"
        )
        btn_qam.pack(side="left", padx=5)

    def show_deck_mode(self):
        self.current_mode = "DECK"
        self.build_topbar()
        for w in self.main_container.winfo_children():
            w.destroy()

        content = tk.Frame(self.main_container, bg=COLOR_BG_DARK)
        content.pack(fill="both", expand=True, padx=30, pady=20)

        # Hero Banner
        hero = tk.Frame(content, bg="#131b2c", bd=1, relief="solid", highlightbackground=COLOR_BORDER_ACTIVE, highlightthickness=1)
        hero.pack(fill="x", pady=(0, 20), ipady=12, ipadx=15)

        hero_left = tk.Frame(hero, bg="#131b2c")
        hero_left.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(hero_left, text="TITOLO IN PRIMO PIANO", font=self.font_small, fg=COLOR_ACCENT_CYAN, bg="#131b2c").pack(anchor="w")
        tk.Label(hero_left, text="Universal Execution Matrix (UEM) Core", font=self.font_title, fg="#ffffff", bg="#131b2c").pack(anchor="w", pady=2)
        tk.Label(hero_left, text="Compatibilita trasparente a livello di kernel per eseguibili Windows (Proton/DXVK), Android (Waydroid), macOS (Darling) e Cross-ISA.", font=self.font_body, fg=COLOR_TEXT_SECONDARY, bg="#131b2c").pack(anchor="w", pady=4)

        hero_right = tk.Frame(hero, bg="#131b2c")
        hero_right.pack(side="right", padx=15)

        btn_play = make_button(
            hero_right, "▶ AVVIA SOFTWARE", COLOR_ACCENT_PURPLE, "#ffffff",
            self.action_run_uem_file, font=("Helvetica Neue", 10, "bold"), padx=14, pady=6, border_color="#a855f7"
        )
        btn_play.pack(pady=4)

        btn_inspect = make_button(
            hero_right, "🔬 Radiografia Binario", "#1e293b", "#ffffff",
            self.action_inspect_file, font=self.font_small, padx=14, pady=5, border_color="#334155"
        )
        btn_inspect.pack()

        # Sezione Libreria / Griglia Cards
        tk.Label(content, text="Libreria Applicativi & Gaming Matrix", font=self.font_heading, fg="#ffffff", bg=COLOR_BG_DARK).pack(anchor="w", pady=(10, 12))

        cards_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        cards_frame.pack(fill="both", expand=True)

        cards = [
            ("Cyberpunk 2077", "Proton-GE • DXVK-Async • Fsync", "🎮 Windows PE64", self.action_mock_launch),
            ("Elden Ring", "Anti-Cheat EAC Bridge Attivo", "🛡️ EAC Supported", self.action_mock_launch),
            ("Orbit64 / Retro Engine", "Emulazione N64 Zero-Jitter", "🕹️ UEM Cross-ISA", self.action_mock_launch),
            ("OSify Web Shield", "Falkon / Firefox Anti-Telemetry", "🌐 Web Proteggetto", self.action_launch_browser),
            ("MS-DOS Industrial Suite", "DOSBox-Staging • 16-bit MZ", "💾 Legacy 16-Bit", self.action_mock_launch),
            ("OSify Control Center", "QoS CAKE & Audio Twitch VOD", "⚙️ Hardware Monitor", self.action_launch_control_center)
        ]

        cols = 3
        for i, (title, desc, badge, cmd) in enumerate(cards):
            row = i // cols
            col = i % cols
            card = tk.Frame(cards_frame, bg=COLOR_BG_CARD, bd=1, relief="solid", highlightbackground=COLOR_BORDER, highlightthickness=1)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            cards_frame.grid_columnconfigure(col, weight=1)

            # Badge categoria
            tk.Label(card, text=badge, font=self.font_small, fg=COLOR_ACCENT_CYAN, bg=COLOR_BG_CARD).pack(anchor="w", padx=12, pady=(10, 2))
            # Titolo
            tk.Label(card, text=title, font=self.font_heading, fg="#ffffff", bg=COLOR_BG_CARD).pack(anchor="w", padx=12, pady=2)
            # Dettagli
            tk.Label(card, text=desc, font=self.font_small, fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_CARD).pack(anchor="w", padx=12, pady=4)

            # Bottone Avvia
            btn = make_button(
                card, "AVVIA", "#1e293b", "#ffffff", cmd,
                font=self.font_small, padx=12, pady=4, border_color="#334155"
            )
            btn.pack(anchor="e", padx=12, pady=(8, 12))

    def show_desktop_mode(self):
        self.current_mode = "DESKTOP"
        self.build_topbar()
        for w in self.main_container.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.main_container, bg=COLOR_BG_DARK, bd=0, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        if self.bg_img:
            canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        # Widget Desktop in alto a sinistra: OSify System Status
        info_card = tk.Frame(canvas, bg="#0d111a", bd=1, relief="solid", highlightbackground=COLOR_BORDER_ACTIVE, highlightthickness=1)
        tk.Label(info_card, text="OSify Desktop Environment", font=self.font_heading, fg=COLOR_ACCENT_PURPLE, bg="#0d111a").pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(info_card, text="KDE Plasma 6 Wayland Engine • Toshiba NB200 Spec", font=self.font_small, fg=COLOR_TEXT_SECONDARY, bg="#0d111a").pack(anchor="w", padx=12)
        tk.Label(info_card, text="• Kernel: Linux LTS BORE Scheduler (1000Hz)", font=self.font_small, fg="#e2e8f0", bg="#0d111a").pack(anchor="w", padx=12, pady=1)
        tk.Label(info_card, text="• Memoria: 1024 MB (ZRAM LZ4 Attiva: 1536 MB)", font=self.font_small, fg="#e2e8f0", bg="#0d111a").pack(anchor="w", padx=12, pady=1)
        tk.Label(info_card, text="• GPU: Intel GMA 950 (Mesa Amber DRI2 OpenGL 2.1)", font=self.font_small, fg="#e2e8f0", bg="#0d111a").pack(anchor="w", padx=12, pady=1)
        tk.Label(info_card, text="• UEM Sottosistemi: PE, Mach-O, APK, WASM, DOS, Java", font=self.font_small, fg=COLOR_ACCENT_GREEN, bg="#0d111a").pack(anchor="w", padx=12, pady=(1, 8))
        canvas.create_window(30, 30, window=info_card, anchor="nw")

        # ----------------------------------------------------------------------
        # FLOATING CENTERED DOCK (In Stile SteamOS Desktop / KDE Plasma 6)
        # ----------------------------------------------------------------------
        dock = tk.Frame(canvas, bg="#0b0e17", bd=1, relief="solid", highlightbackground=COLOR_ACCENT_PURPLE, highlightthickness=1)
        
        dock_items = [
            ("🚀 Kickoff", self.action_start_menu, "#151b28"),
            ("🌐 Web Shield", self.action_launch_browser, "#151b28"),
            ("💻 Terminale", self.action_launch_terminal, "#151b28"),
            ("📁 File Manager", self.action_launch_file_manager, "#151b28"),
            ("🎮 UEM Runner", self.action_run_uem_file, "#151b28"),
            ("⚙️ Control Center", self.action_launch_control_center, "#151b28"),
            ("🕹️ Ritorna a DeckUI", self.show_deck_mode, COLOR_ACCENT_PURPLE)
        ]

        for text, cmd, bg_col in dock_items:
            btn = make_button(
                dock, text, bg_col, "#ffffff", cmd,
                font=self.font_small, padx=12, pady=6, border_color="#334155" if bg_col != COLOR_ACCENT_PURPLE else "#a855f7"
            )
            btn.pack(side="left", padx=4, pady=4)

        canvas.create_window(550, 560, window=dock, anchor="center")

    def toggle_qam(self):
        if hasattr(self, "qam_window") and self.qam_window and self.qam_window.winfo_exists():
            self.qam_window.destroy()
            return

        self.qam_window = tk.Toplevel(self)
        self.qam_window.title("Quick Access Menu")
        self.qam_window.geometry("340x480")
        self.qam_window.configure(bg="#0f1420")
        self.qam_window.resizable(False, False)

        tk.Label(self.qam_window, text="⚙️ QUICK ACCESS MENU", font=self.font_heading, fg=COLOR_ACCENT_CYAN, bg="#0f1420").pack(anchor="w", padx=20, pady=(15, 10))

        # Performance Profile
        p_frame = tk.Frame(self.qam_window, bg="#161e2e", padx=12, pady=10)
        p_frame.pack(fill="x", padx=15, pady=6)
        tk.Label(p_frame, text="Profilo CPU Governor: BORE Realtime (1000Hz)", font=self.font_small, fg="#e2e8f0", bg="#161e2e").pack(anchor="w")

        # TDP Limit Slider
        t_frame = tk.Frame(self.qam_window, bg="#161e2e", padx=12, pady=10)
        t_frame.pack(fill="x", padx=15, pady=6)
        tk.Label(t_frame, text="Limite TDP / Consumo: 15W", font=self.font_small, fg="#e2e8f0", bg="#161e2e").pack(anchor="w")

        # UEM Runtime Strategy Override
        u_frame = tk.Frame(self.qam_window, bg="#161e2e", padx=12, pady=10)
        u_frame.pack(fill="x", padx=15, pady=6)
        tk.Label(u_frame, text="UEM Backend: Auto-Detect (Mesa DRI2 / Vulkan)", font=self.font_small, fg="#e2e8f0", bg="#161e2e").pack(anchor="w")

        # Bottoni Chiudi e Applica
        btn_apply = make_button(
            self.qam_window, "APPLICA MODIFICHE", COLOR_ACCENT_PURPLE, "#ffffff",
            self.qam_window.destroy, font=self.font_small, padx=12, pady=6, border_color="#a855f7"
        )
        btn_apply.pack(fill="x", padx=15, pady=15)

    def action_run_uem_file(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona file o binario da eseguire con OSify UEM",
            filetypes=[("Tutti i formati eseguibili", "*.*"), ("Windows PE (.exe)", "*.exe"), ("Android APK", "*.apk"), ("WebAssembly", "*.wasm"), ("Java JAR", "*.jar"), ("MS-DOS COM/MZ", "*.com;*.exe")]
        )
        if filepath:
            cmd = f"'{OSIFY_CTL}' uem run '{filepath}'"
            messagebox.showinfo("OSify UEM Dispatcher", f"Invocazione Universal Execution Matrix:\n\nFile: {os.path.basename(filepath)}\nComando: {cmd}")
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
                top.title("Radiografia Architetturale — OSify")
                top.geometry("640x480")
                top.configure(bg="#090b10")
                txt = tk.Text(top, bg="#0d111a", fg="#10b981", font=("Courier New", 10), padx=10, pady=10)
                txt.pack(fill="both", expand=True, padx=15, pady=15)
                txt.insert("1.0", output)
                txt.config(state="disabled")
            except Exception as e:
                messagebox.showerror("Errore", str(e))

    def action_launch_browser(self):
        browser_tune = os.path.join(REPO_ROOT, "desktop/web/osify-browser-tuning.sh")
        if os.path.exists(browser_tune):
            subprocess.Popen([browser_tune], shell=False)
        messagebox.showinfo("OSify Web Shield", "Avvio del Navigatore Web OSify con profilo Shield attivo (Anti-telemetria, adblock e memory saving).")

    def action_launch_control_center(self):
        cc_bin = os.path.join(REPO_ROOT, "tools/osify-gui/osify-control-center.py")
        if os.path.exists(cc_bin):
            subprocess.Popen([sys.executable, cc_bin], shell=False)
        else:
            messagebox.showinfo("Control Center", "Avvio del pannello di controllo centrale di OSify.")

    def action_launch_terminal(self):
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            subprocess.Popen(["x-terminal-emulator"])

    def action_launch_file_manager(self):
        if sys.platform == "darwin":
            subprocess.Popen(["open", REPO_ROOT])
        else:
            subprocess.Popen(["xdg-open", REPO_ROOT])

    def action_start_menu(self):
        messagebox.showinfo("Kickoff Menu", "OSify Start Menu (KDE Plasma 6):\n\n• Universal Execution Matrix\n• Internet & Web Shield\n• Monitor Hardware & Sensori\n• Impostazioni Sistema\n• Riavvia / Spegni")

    def action_mock_launch(self):
        messagebox.showinfo("OSify Launcher", "Avvio del software selezionato all'interno del container isolato ad alte prestazioni.")

    def start_telemetry_loop(self):
        def update():
            import random
            cpu = random.randint(2, 8)
            ping = random.randint(8, 14)
            text = f"CPU: {cpu}% | RAM: 118MB (ZRAM: LZ4 1.5x) | CAKE QoS: {ping}ms | BORE 1000Hz"
            self.lbl_telemetry.config(text=text)
            self.after(2000, update)
        self.after(1000, update)

if __name__ == "__main__":
    app = OSifyDeckApp()
    app.mainloop()
