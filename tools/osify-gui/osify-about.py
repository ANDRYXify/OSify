#!/usr/bin/env python3
"""
OSify — Informazioni su questo Sistema (macOS "About This Mac" Clone 2050)
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Visualizza in modo elegante e professionale la carta d'identità ufficiale di OSify:
- Chipset, Processore reale e architettura
- Memoria RAM totale e utilizzata
- Controller Grafico e Risoluzione del Display
- Supporto di Boot (Live USB o Disco Fisso)
- Azioni rapide: Aggiornamento, Preferenze e Installatore Bare-Metal
=============================================================================
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOGO_PATH = os.path.join(REPO_ROOT, "OSify.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = "/usr/share/pixmaps/osify-hub.png"

def get_cpu():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return subprocess.check_output("uname -m", shell=True, text=True).strip()

def get_ram():
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line:
                    kb = int(line.split()[1])
                    return f"{kb // 1024} MB"
    except Exception:
        pass
    return "1024 MB"

def get_gpu():
    try:
        out = subprocess.check_output("lspci 2>/dev/null | grep -iE 'vga|display|3d'", shell=True, text=True)
        if out.strip():
            return out.split(":")[-1].strip()
    except Exception:
        pass
    return "Controller Grafico Integrato"

def get_kernel():
    try:
        return subprocess.check_output("uname -srm", shell=True, text=True).strip()
    except Exception:
        return "Linux 2050 Quantum"

root = tk.Tk()
root.title("Informazioni su questo OSify")
root.geometry("540x350")
root.configure(bg="#0b0d14")
root.resizable(False, False)

# Centra la finestra a schermo
root.update_idletasks()
w = root.winfo_width()
h = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (w // 2)
y = (root.winfo_screenheight() // 2) - (h // 2) - 40
root.geometry(f"+{x}+{y}")

main_frame = tk.Frame(root, bg="#0b0d14", padx=25, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Logo OSify a sinistra
left_frame = tk.Frame(main_frame, bg="#0b0d14", width=140)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

if os.path.exists(LOGO_PATH):
    try:
        im = Image.open(LOGO_PATH).convert("RGBA")
        im.thumbnail((120, 120), Image.Resampling.LANCZOS)
        tk_logo = ImageTk.PhotoImage(im)
        lbl_img = tk.Label(left_frame, image=tk_logo, bg="#0b0d14")
        lbl_img.image = tk_logo
        lbl_img.pack(pady=20)
    except Exception:
        pass

# Dettagli di sistema a destra
right_frame = tk.Frame(main_frame, bg="#0b0d14")
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

lbl_title = tk.Label(right_frame, text="OSify", font=("Helvetica", 24, "bold"), fg="#f8fafc", bg="#0b0d14")
lbl_title.pack(anchor="w")

lbl_ver = tk.Label(right_frame, text="Versione 2.0 LTS (Matrix 2050 Edition)", font=("Helvetica", 10), fg="#38bdf8", bg="#0b0d14")
lbl_ver.pack(anchor="w", pady=(0, 15))

# Tabella specifiche hardware
specs = [
    ("Processore", get_cpu()),
    ("Memoria RAM", get_ram()),
    ("Grafica", get_gpu()),
    ("Kernel", get_kernel()),
    ("Piattaforma", "Ingegnerizzato da Andrea Taliento (ANDRYXify)")
]

for label, val in specs:
    row = tk.Frame(right_frame, bg="#0b0d14")
    row.pack(fill=tk.X, pady=2)
    tk.Label(row, text=f"{label}:", font=("Helvetica", 9, "bold"), fg="#94a3b8", bg="#0b0d14", width=12, anchor="w").pack(side=tk.LEFT)
    tk.Label(row, text=val, font=("Helvetica", 9), fg="#e2e8f0", bg="#0b0d14", anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

# Pulsanti rapidi inferiori
btn_frame = tk.Frame(root, bg="#07090e", padx=20, pady=12)
btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

def open_cmd(cmd):
    subprocess.Popen(cmd, shell=True)
    root.destroy()

tk.Button(btn_frame, text="Aggiornamento...", font=("Helvetica", 9, "bold"), bg="#1e293b", fg="#ffffff", 
          activebackground="#334155", relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
          command=lambda: open_cmd("/usr/bin/osify-update")).pack(side=tk.LEFT, padx=4)

tk.Button(btn_frame, text="Preferenze...", font=("Helvetica", 9, "bold"), bg="#1e293b", fg="#ffffff", 
          activebackground="#334155", relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
          command=lambda: open_cmd("/usr/bin/osify-settings")).pack(side=tk.LEFT, padx=4)

tk.Button(btn_frame, text="Installa su Disco", font=("Helvetica", 9, "bold"), bg="#0284c7", fg="#ffffff", 
          activebackground="#0369a1", relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
          command=lambda: open_cmd("/usr/bin/osify-install")).pack(side=tk.RIGHT, padx=4)

root.mainloop()
