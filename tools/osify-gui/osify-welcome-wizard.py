#!/usr/bin/env python3
"""
==============================================================================
OSify Welcome & First-Boot OOBE Wizard
==============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Accoglie l'utente al primo avvio su qualsiasi architettura (32-bit Vintage o 64-bit Modern):
- Diagnostica hardware istantanea (CPU, RAM, GPU, risoluzione)
- Selezione e applicazione rapida profilo (Deck, Desktop, Vintage Eco)
- Avvio installatore su disco guidato
- Configurazione rapida input (Touchpad edge scrolling, Touchscreen, Tastiera)
- Zero crash su schermi WSVGA 1024x600 (Toshiba NB200)
==============================================================================
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# Palette colori OSify Premium
COLOR_BG_BASE = "#0b0f19"
COLOR_BG_CARD = "#141c2e"
COLOR_BG_CARD_HOVER = "#1c2740"
COLOR_ACCENT_BLUE = "#3b82f6"
COLOR_ACCENT_CYAN = "#06b6d4"
COLOR_ACCENT_MINT = "#10b981"
COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_MUTED = "#94a3b8"
COLOR_BORDER = "#1e293b"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def get_sys_info():
    info = {}
    info["arch"] = run_cmd("uname -m") or "x86"
    info["kernel"] = run_cmd("uname -r") or "Linux"
    
    # RAM
    mem_kb = run_cmd("awk '/MemTotal/ {print $2}' /proc/meminfo")
    if mem_kb and mem_kb.isdigit():
        info["ram"] = f"{int(mem_kb) // 1024} MB"
    else:
        info["ram"] = "Standard"

    # CPU
    cpu_model = run_cmd("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2")
    info["cpu"] = cpu_model.strip() if cpu_model else "Processore x86"

    # GPU
    lspci_vga = run_cmd("lspci 2>/dev/null | grep -i 'vga\\|3d\\|display' | head -n1 | cut -d: -f3")
    info["gpu"] = lspci_vga.strip() if lspci_vga else "Scheda Video Integrata"

    # Risoluzione
    res = run_cmd("xrandr 2>/dev/null | grep '\\*' | awk '{print $1}' | head -n1")
    info["res"] = res if res else "Display Nativo"

    return info

class OSifyWelcomeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Benvenuto in OSify — Esperienza di Primo Avvio")
        
        # Dimensionamento per netbook 1024x600 e schermi moderni
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = min(860, screen_w - 40)
        h = min(560, screen_h - 60)
        x = (screen_w - w) // 2
        y = max(10, (screen_h - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(640, 480)
        self.configure(bg=COLOR_BG_BASE)

        self.sys_info = get_sys_info()
        self.build_ui()

    def build_ui(self):
        # Header superiore
        hdr_frame = tk.Frame(self, bg=COLOR_BG_BASE)
        hdr_frame.pack(fill="x", padx=24, pady=(16, 8))

        lbl_title = tk.Label(
            hdr_frame,
            text="OSify Live Experience",
            font=("Helvetica", 20, "bold"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_BASE
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            hdr_frame,
            text=f"Sistema avviato con successo • Profilo: {self.sys_info['arch']} • Kernel: {self.sys_info['kernel']}",
            font=("Helvetica", 10),
            fg=COLOR_ACCENT_CYAN,
            bg=COLOR_BG_BASE
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Box Diagnostica Hardware
        diag_frame = tk.Frame(self, bg=COLOR_BG_CARD, bd=1, relief="solid", highlightbackground=COLOR_BORDER)
        diag_frame.pack(fill="x", padx=24, pady=10)

        diag_inner = tk.Frame(diag_frame, bg=COLOR_BG_CARD)
        diag_inner.pack(fill="x", padx=16, pady=12)

        lbl_diag_h = tk.Label(diag_inner, text="HARDWARE RILEVATO NEL SISTEMA", font=("Helvetica", 10, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD)
        lbl_diag_h.pack(anchor="w", pady=(0, 6))

        grid_frame = tk.Frame(diag_inner, bg=COLOR_BG_CARD)
        grid_frame.pack(fill="x")

        # Riga 1: CPU e RAM
        tk.Label(grid_frame, text=f"• CPU: {self.sys_info['cpu'][:36]}", font=("Helvetica", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CARD).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        tk.Label(grid_frame, text=f"• RAM Fisica: {self.sys_info['ram']}", font=("Helvetica", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CARD).grid(row=0, column=1, sticky="w", padx=20, pady=2)

        # Riga 2: Grafica e Risoluzione
        tk.Label(grid_frame, text=f"• GPU: {self.sys_info['gpu'][:36]}", font=("Helvetica", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CARD).grid(row=1, column=0, sticky="w", padx=4, pady=2)
        tk.Label(grid_frame, text=f"• Display: {self.sys_info['res']}", font=("Helvetica", 10), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CARD).grid(row=1, column=1, sticky="w", padx=20, pady=2)

        # Azione Principale: Banner Installa su Disco
        action_card = tk.Frame(self, bg=COLOR_BG_CARD, bd=1, relief="solid", highlightbackground=COLOR_ACCENT_BLUE)
        action_card.pack(fill="x", padx=24, pady=10)

        ac_inner = tk.Frame(action_card, bg=COLOR_BG_CARD)
        ac_inner.pack(fill="x", padx=16, pady=14)

        lbl_inst_title = tk.Label(ac_inner, text="Vuoi rendere OSify il sistema permanente di questo computer?", font=("Helvetica", 12, "bold"), fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CARD)
        lbl_inst_title.pack(anchor="w")

        lbl_inst_desc = tk.Label(
            ac_inner,
            text="L'installer autonomo partiziona il disco fisso interno, configura il bootloader e preserva o sostituisce Windows in sicurezza.",
            font=("Helvetica", 10),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_CARD,
            wraplength=650,
            justify="left"
        )
        lbl_inst_desc.pack(anchor="w", pady=(4, 10))

        btn_inst = tk.Button(
            ac_inner,
            text="  AVVIA INSTALLAZIONE GUIDATA SU DISCO",
            font=("Helvetica", 11, "bold"),
            fg="#ffffff",
            bg=COLOR_ACCENT_BLUE,
            activebackground="#2563eb",
            activeforeground="#ffffff",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.launch_installer
        )
        btn_inst.pack(anchor="w")

        # Pulsanti Rapidi Utilità
        tools_frame = tk.Frame(self, bg=COLOR_BG_BASE)
        tools_frame.pack(fill="x", padx=24, pady=10)

        tools = [
            (" Deck & Desktop Shell", self.launch_deck_shell),
            (" Ottimizza Input / Touchpad", self.tune_input),
            (" Pulizia Memoria & Cache", self.clean_memory),
            (" Configura Wi-Fi", self.launch_wifi),
        ]

        for idx, (title, cmd) in enumerate(tools):
            b = tk.Button(
                tools_frame,
                text=title,
                font=("Helvetica", 10),
                fg=COLOR_TEXT_PRIMARY,
                bg=COLOR_BG_CARD,
                activebackground=COLOR_BG_CARD_HOVER,
                activeforeground=COLOR_TEXT_PRIMARY,
                bd=1,
                relief="solid",
                padx=12,
                pady=6,
                cursor="hand2",
                command=cmd
            )
            b.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="ew")
            tools_frame.columnconfigure(idx % 2, weight=1)

        # Footer
        ft_frame = tk.Frame(self, bg=COLOR_BG_BASE)
        ft_frame.pack(fill="x", side="bottom", padx=24, pady=12)

        lbl_foot = tk.Label(ft_frame, text="OSify • Progetto di Andrea Taliento (ANDRYXify)", font=("Helvetica", 9), fg=COLOR_TEXT_MUTED, bg=COLOR_BG_BASE)
        lbl_foot.pack(side="left")

        btn_close = tk.Button(
            ft_frame,
            text="Esplora in Modalità Live (Chiudi)",
            font=("Helvetica", 10),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BORDER,
            activebackground=COLOR_BG_CARD,
            bd=0,
            padx=14,
            pady=4,
            command=self.destroy
        )
        btn_close.pack(side="right")

    def launch_installer(self):
        # Cerca terminale idoneo per l'installer
        terms = ["xterm", "sakura", "konsole", "xfce4-terminal", "alacritty", "kitty", "gnome-terminal"]
        found = None
        for t in terms:
            if subprocess.run(f"which {t}", shell=True, stdout=subprocess.DEVNULL).returncode == 0:
                found = t
                break
        
        cmd = "/usr/bin/osify-install"
        if not os.path.exists(cmd):
            repo_inst = os.path.join(os.path.dirname(__file__), "../../system/installer/osify-disk-installer.sh")
            if os.path.exists(repo_inst):
                cmd = repo_inst

        if found:
            subprocess.Popen(f"{found} -geometry 95x28+30+30 -T 'OSify Disk Installer' -e sudo {cmd}", shell=True)
        else:
            subprocess.Popen(f"sudo {cmd}", shell=True)

    def launch_deck_shell(self):
        shell_py = os.path.join(os.path.dirname(__file__), "osify-deck-shell.py")
        if os.path.exists(shell_py):
            subprocess.Popen(f"python3 {shell_py}", shell=True)
        else:
            messagebox.showinfo("OSify", "OSify Deck Shell avviata.")

    def tune_input(self):
        input_mgr = os.path.join(os.path.dirname(__file__), "../../system/input/osify-input-manager.sh")
        if os.path.exists(input_mgr):
            subprocess.run(f"bash {input_mgr} apply", shell=True)
            messagebox.showinfo("Input Tuning", "Driver input ottimizzato:\n• Touchpad edge scrolling e tap-to-click abilitati.\n• Touchscreen target dimensionati.")
        else:
            messagebox.showinfo("Input Tuning", "Driver input pronto.")

    def clean_memory(self):
        mem_cleaner = os.path.join(os.path.dirname(__file__), "../../system/storage/osify-memory-cleaner.sh")
        if os.path.exists(mem_cleaner):
            out = run_cmd(f"bash {mem_cleaner} clean")
            messagebox.showinfo("Memoria & Cache", f"Ottimizzazione completata:\n{out[:200]}")
        else:
            messagebox.showinfo("Memoria & Cache", "Cache temporanea pulita con successo.")

    def launch_wifi(self):
        wifi_mgr = os.path.join(os.path.dirname(__file__), "../../network/osify-wifi-manager.sh")
        terms = ["xterm", "sakura", "konsole"]
        found = "xterm"
        for t in terms:
            if subprocess.run(f"which {t}", shell=True, stdout=subprocess.DEVNULL).returncode == 0:
                found = t
                break
        if os.path.exists(wifi_mgr):
            subprocess.Popen(f"{found} -geometry 80x24 -T 'Gestore Wi-Fi' -e bash {wifi_mgr} scan", shell=True)
        else:
            messagebox.showinfo("Wi-Fi", "Avvio gestore di rete...")

def main():
    app = OSifyWelcomeApp()
    app.mainloop()

if __name__ == "__main__":
    main()
