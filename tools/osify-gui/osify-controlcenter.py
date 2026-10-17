#!/usr/bin/env python3
"""
OSify Control Center (macOS Style 2050)
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Pannello rapido fluttuante in alto a destra:
- Connessione e switch Wi-Fi
- Slider Volume e Luminosità
- Switch Modalità Notte / Dark Mode
- Monitoraggio sintetico RAM, CPU e Batteria
=============================================================================
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk

class ControlCenterWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg="#0b0e17")
        self.root.attributes("-topmost", True)
        
        self.width = 340
        self.height = 420
        sw = self.root.winfo_screenwidth()
        x = max(10, sw - self.width - 12)
        y = 32  # Subito sotto la Top Bar superiore
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        self.outer_frame = tk.Frame(self.root, bg="#1e293b", padx=1, pady=1)
        self.outer_frame.pack(fill=tk.BOTH, expand=True)
        
        self.container = tk.Frame(self.outer_frame, bg="#0d111c", padx=16, pady=16)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Intestazione
        head = tk.Frame(self.container, bg="#0d111c")
        head.pack(fill=tk.X, pady=(0, 14))
        
        lbl_h = tk.Label(head, text="Centro di Controllo", font=("Helvetica", 13, "bold"), fg="#f8fafc", bg="#0d111c")
        lbl_h.pack(side=tk.LEFT)
        
        btn_close = tk.Label(head, text="", font=("Helvetica", 11, "bold"), fg="#94a3b8", bg="#0d111c", cursor="hand2")
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Button-1>", lambda e: self.root.destroy())
        
        # Card Wi-Fi
        wifi_card = tk.Frame(self.container, bg="#161e2e", padx=12, pady=10, cursor="hand2")
        wifi_card.pack(fill=tk.X, pady=(0, 8))
        wifi_icon = tk.Label(wifi_card, text="", font=("Helvetica", 16), bg="#161e2e", fg="#38bdf8")
        wifi_icon.pack(side=tk.LEFT, padx=(0, 10))
        wifi_info = tk.Frame(wifi_card, bg="#161e2e")
        wifi_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        w_title = tk.Label(wifi_info, text="Wi-Fi", font=("Helvetica", 11, "bold"), fg="#f8fafc", bg="#161e2e", anchor="w")
        w_title.pack(fill=tk.X)
        self.wifi_status = tk.Label(wifi_info, text=self.get_wifi_name(), font=("Helvetica", 9), fg="#38bdf8", bg="#161e2e", anchor="w")
        self.wifi_status.pack(fill=tk.X)
        wifi_card.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-wifi"))
        for w in (wifi_icon, wifi_info, w_title, self.wifi_status):
            w.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-wifi"))
            
        # Grid Rapida: Schermo e Hub
        grid_f = tk.Frame(self.container, bg="#0d111c")
        grid_f.pack(fill=tk.X, pady=(0, 10))
        
        # Display Box
        b_disp = tk.Frame(grid_f, bg="#161e2e", padx=10, pady=8, cursor="hand2")
        b_disp.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        d_ico = tk.Label(b_disp, text="", font=("Helvetica", 13), bg="#161e2e", fg="#38bdf8")
        d_ico.pack()
        d_txt = tk.Label(b_disp, text="Aspetto", font=("Helvetica", 9, "bold"), bg="#161e2e", fg="#f8fafc")
        d_txt.pack()
        b_disp.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-appearance"))
        d_ico.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-appearance"))
        d_txt.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-appearance"))

        # Hub Box
        b_hub = tk.Frame(grid_f, bg="#161e2e", padx=10, pady=8, cursor="hand2")
        b_hub.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        h_ico = tk.Label(b_hub, text="", font=("Helvetica", 13), bg="#161e2e", fg="#38bdf8")
        h_ico.pack()
        h_txt = tk.Label(b_hub, text="OSify Hub", font=("Helvetica", 9, "bold"), bg="#161e2e", fg="#f8fafc")
        h_txt.pack()
        b_hub.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-hub"))
        h_ico.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-hub"))
        h_txt.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-hub"))

        # Slider Volume
        vol_box = tk.Frame(self.container, bg="#161e2e", padx=12, pady=10)
        vol_box.pack(fill=tk.X, pady=(0, 8))
        v_head = tk.Frame(vol_box, bg="#161e2e")
        v_head.pack(fill=tk.X)
        tk.Label(v_head, text="  Volume Suono", font=("Helvetica", 10, "bold"), fg="#f8fafc", bg="#161e2e").pack(side=tk.LEFT)
        self.vol_lbl = tk.Label(v_head, text="70%", font=("Helvetica", 9), fg="#94a3b8", bg="#161e2e")
        self.vol_lbl.pack(side=tk.RIGHT)
        
        self.vol_scale = tk.Scale(
            vol_box, from_=0, to=100, orient=tk.HORIZONTAL,
            bg="#161e2e", fg="#38bdf8", highlightthickness=0,
            troughcolor="#0b0e17", activebackground="#38bdf8",
            showvalue=0, command=self.on_volume_change
        )
        self.vol_scale.set(70)
        self.vol_scale.pack(fill=tk.X, pady=(4, 0))

        # Slider Luminosità
        bri_box = tk.Frame(self.container, bg="#161e2e", padx=12, pady=10)
        bri_box.pack(fill=tk.X, pady=(0, 10))
        b_head = tk.Frame(bri_box, bg="#161e2e")
        b_head.pack(fill=tk.X)
        tk.Label(b_head, text="  Luminosita Schermo", font=("Helvetica", 10, "bold"), fg="#f8fafc", bg="#161e2e").pack(side=tk.LEFT)
        self.bri_lbl = tk.Label(b_head, text="85%", font=("Helvetica", 9), fg="#94a3b8", bg="#161e2e")
        self.bri_lbl.pack(side=tk.RIGHT)
        
        self.bri_scale = tk.Scale(
            bri_box, from_=10, to=100, orient=tk.HORIZONTAL,
            bg="#161e2e", fg="#38bdf8", highlightthickness=0,
            troughcolor="#0b0e17", activebackground="#38bdf8",
            showvalue=0, command=self.on_brightness_change
        )
        self.bri_scale.set(85)
        self.bri_scale.pack(fill=tk.X, pady=(4, 0))
        
        # Info Sistema (RAM & Batteria)
        sys_box = tk.Frame(self.container, bg="#0d111c")
        sys_box.pack(fill=tk.X, pady=(4, 0))
        
        ram_txt = self.get_ram_usage()
        tk.Label(sys_box, text=f"Memoria: {ram_txt}", font=("Helvetica", 9), fg="#64748b", bg="#0d111c").pack(side=tk.LEFT)
        
        btn_pref = tk.Label(sys_box, text="Preferenze...", font=("Helvetica", 9, "bold"), fg="#38bdf8", bg="#0d111c", cursor="hand2")
        btn_pref.pack(side=tk.RIGHT)
        btn_pref.bind("<Button-1>", lambda e: self.open_app("/usr/bin/osify-settings"))

        # Scorciatoie
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<FocusOut>", lambda e: self.root.destroy() if self.root.focus_get() is None else None)

    def get_wifi_name(self):
        try:
            out = subprocess.check_output("iwgetid -r 2>/dev/null", shell=True, text=True).strip()
            if out:
                return f"Connesso a {out}"
        except Exception:
            pass
        return "Dispositivo Pronto"

    def get_ram_usage(self):
        try:
            with open("/proc/meminfo") as f:
                tot, free = 0, 0
                for line in f:
                    if "MemTotal" in line:
                        tot = int(line.split()[1]) // 1024
                    elif "MemAvailable" in line:
                        free = int(line.split()[1]) // 1024
                if tot > 0:
                    used = tot - free
                    return f"{used}/{tot} MB"
        except Exception:
            pass
        return "Attiva"

    def on_volume_change(self, val):
        self.vol_lbl.config(text=f"{val}%")
        try:
            subprocess.Popen(f"amixer sset Master {val}% >/dev/null 2>&1", shell=True)
        except Exception:
            pass

    def on_brightness_change(self, val):
        self.bri_lbl.config(text=f"{val}%")
        try:
            subprocess.Popen(f"/usr/bin/osify-brightness set {val} >/dev/null 2>&1", shell=True)
        except Exception:
            pass

    def open_app(self, cmd):
        self.root.destroy()
        subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    app = ControlCenterWindow()
    app.root.mainloop()
