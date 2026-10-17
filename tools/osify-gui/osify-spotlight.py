#!/usr/bin/env python3
"""
OSify Spotlight Search 2050
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Ricerca universale e reattiva ispirata a macOS Spotlight:
- Indicizzazione istantanea di applicazioni, strumenti di sistema e scorciatoie
- Calcolatrice matematica in tempo reale
- Interfaccia Dark Glass fluttuante con chiusura automatica su Esc o FocusOut
- Scorciatoie predefinite: Super+Space / Ctrl+Space
=============================================================================
"""

import os
import sys
import glob
import subprocess
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Scansione applicazioni desktop
def load_applications():
    apps = []
    seen_execs = set()
    search_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.join(REPO_ROOT, "desktop/applications")
    ]
    
    # App integrate di default per garantire copertura anche in ambiente minimale
    builtins = [
        {"name": "Navigatore Web Safari/OSify", "exec": "/usr/bin/osify-browser", "icon": "/usr/share/pixmaps/osify-browser.png", "desc": "Navigazione Internet ultra-veloce e privata"},
        {"name": "Gestore File Finder", "exec": "pcmanfm", "icon": "/usr/share/pixmaps/osify-files.png", "desc": "Esplora dischi, documenti e cartelle"},
        {"name": "Terminale di Sistema", "exec": "/usr/bin/terminal", "icon": "/usr/share/pixmaps/osify-terminal.png", "desc": "Riga di comando Unix 2050"},
        {"name": "Informazioni su questo OSify", "exec": "/usr/bin/osify-about", "icon": "/usr/share/pixmaps/osify-about.png", "desc": "Specifiche hardware, memoria, chipset e release"},
        {"name": "Connessione Wi-Fi & Rete", "exec": "/usr/bin/osify-wifi", "icon": "/usr/share/pixmaps/osify-wifi.png", "desc": "Scansione e configurazione reti senza fili"},
        {"name": "OSify Hub & Dashboard", "exec": "/usr/bin/osify-hub", "icon": "/usr/share/pixmaps/osify-hub.png", "desc": "Pannello di controllo centrale e app store"},
        {"name": "Launchpad Tutte le App", "exec": "/usr/bin/osify-app-drawer", "icon": "/usr/share/pixmaps/osify-drawer.png", "desc": "Griglia visiva di tutti i software installati"},
        {"name": "Installa OSify su Disco", "exec": "/usr/bin/osify-install", "icon": "/usr/share/pixmaps/osify-install.png", "desc": "Installatore bare-metal per dischi fissi ed SSD"},
        {"name": "Impostazioni di Sistema", "exec": "/usr/bin/osify-settings", "icon": "/usr/share/pixmaps/osify-settings.png", "desc": "Preferenze generali, display, audio e periferiche"},
        {"name": "Scrivania e Aspetto", "exec": "/usr/bin/osify-appearance", "icon": "/usr/share/pixmaps/osify-appearance.png", "desc": "Sfondi 4K, temi scuri e personalizzazioni visive"},
        {"name": "Gaming Hub & Emulatori", "exec": "/usr/bin/osify-games", "icon": "/usr/share/pixmaps/osify-games.png", "desc": "Centro videogiochi retrò ed emulatori 2050"},
        {"name": "Strumenti Sviluppatore IDE", "exec": "/usr/bin/osify-developer", "icon": "/usr/share/pixmaps/osify-developer.png", "desc": "Compilatori, interpreti, editor e tool dev"},
        {"name": "Monitor Attivita e Risorse", "exec": "/usr/bin/osify-taskmanager", "icon": "/usr/share/pixmaps/osify-taskmanager.png", "desc": "Uso CPU, RAM, processi attivi e governor"},
        {"name": "Screenshot e Cattura Schermo", "exec": "/usr/bin/osify-screenshot --gui", "icon": "/usr/share/pixmaps/osify-capture.png", "desc": "Cattura istantanea dello schermo o di finestre"},
        {"name": "Riavvia Computer", "exec": "/usr/bin/osify-power reboot", "icon": "/usr/share/pixmaps/osify-update.png", "desc": "Riavvio ordinato del sistema operativo"},
        {"name": "Spegni Computer", "exec": "/usr/bin/osify-power off", "icon": "/usr/share/pixmaps/osify-power.png", "desc": "Arresto completo e sicuro della macchina"},
    ]
    for b in builtins:
        apps.append(b)
        seen_execs.add(b["exec"])

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        for dpath in glob.glob(os.path.join(sdir, "*.desktop")):
            try:
                name, cmd, icon, desc, nodisplay = "", "", "", "", False
                with open(dpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1]
                        elif line.startswith("Exec=") and not cmd:
                            cmd = line.split("=", 1)[1].split("%")[0].strip()
                        elif line.startswith("Icon=") and not icon:
                            icon = line.split("=", 1)[1]
                        elif line.startswith("Comment=") and not desc:
                            desc = line.split("=", 1)[1]
                        elif line.lower() == "nodisplay=true":
                            nodisplay = True
                if name and cmd and not nodisplay and cmd not in seen_execs:
                    seen_execs.add(cmd)
                    apps.append({"name": name, "exec": cmd, "icon": icon, "desc": desc or "Applicazione OSify"})
            except Exception:
                pass
    return apps

ALL_APPS = load_applications()

class SpotlightWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg="#0b0e17")
        self.root.attributes("-topmost", True)
        
        self.width = 620
        self.height = 420
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.width) // 2
        y = max(60, sh // 6)
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Bordo glassmorphism
        self.outer_frame = tk.Frame(self.root, bg="#1e293b", padx=1, pady=1)
        self.outer_frame.pack(fill=tk.BOTH, expand=True)
        
        self.container = tk.Frame(self.outer_frame, bg="#0d111c", padx=16, pady=14)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Search Box
        self.search_frame = tk.Frame(self.container, bg="#161e2e", highlightthickness=1, highlightbackground="#38bdf8", padx=12, pady=8)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_lens = tk.Label(self.search_frame, text="", font=("Helvetica", 16), bg="#161e2e", fg="#38bdf8")
        self.lbl_lens.pack(side=tk.LEFT, padx=(0, 10))
        
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self.on_text_changed)
        self.entry = tk.Entry(
            self.search_frame,
            textvariable=self.entry_var,
            font=("Helvetica", 15),
            bg="#161e2e",
            fg="#f8fafc",
            insertbackground="#38bdf8",
            relief=tk.FLAT,
            bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.focus_set()
        
        # Risultati Listbox / Frame
        self.results_frame = tk.Frame(self.container, bg="#0d111c")
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.items_widgets = []
        self.filtered_results = []
        self.selected_index = 0
        
        # Scorciatoie
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<FocusOut>", self.on_focus_out)
        self.entry.bind("<Down>", self.select_next)
        self.entry.bind("<Up>", self.select_prev)
        self.entry.bind("<Return>", self.launch_selected)
        
        self.update_results("")

    def on_focus_out(self, event):
        # Chiudi solo se il focus è uscito dalla finestra principale
        if self.root.focus_get() is None:
            self.root.destroy()

    def try_eval_math(self, query):
        q = query.strip()
        allowed = set("0123456789+-*/.% ()")
        if not set(q).issubset(allowed) or not any(c in q for c in "+-*/%"):
            return None
        try:
            val = eval(q, {"__builtins__": None}, {})
            if isinstance(val, (int, float)):
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                return str(val)
        except Exception:
            pass
        return None

    def on_text_changed(self, *args):
        self.update_results(self.entry_var.get())

    def update_results(self, query):
        query = query.strip().lower()
        self.filtered_results = []
        
        # 1. Controllo calcolatrice
        math_res = self.try_eval_math(query)
        if math_res is not None:
            self.filtered_results.append({
                "type": "calc",
                "name": f"= {math_res}",
                "desc": f"Risultato calcolo per '{query}' — Premi Invio per copiare",
                "exec": math_res,
                "icon": "/usr/share/pixmaps/osify-calculator.png"
            })
            
        # 2. Filtraggio applicazioni
        if query:
            for app in ALL_APPS:
                if query in app["name"].lower() or query in app["desc"].lower() or query in app["exec"].lower():
                    self.filtered_results.append(app)
        else:
            self.filtered_results = ALL_APPS[:8]
            
        self.selected_index = 0
        self.render_items()

    def render_items(self):
        for w in self.items_widgets:
            w.destroy()
        self.items_widgets = []
        
        max_show = 6
        shown = self.filtered_results[:max_show]
        
        if not shown:
            empty = tk.Label(self.results_frame, text="Nessun risultato trovato", font=("Helvetica", 12), fg="#64748b", bg="#0d111c", pady=30)
            empty.pack()
            self.items_widgets.append(empty)
            return

        for idx, item in enumerate(shown):
            is_sel = (idx == self.selected_index)
            bg_col = "#1e293b" if is_sel else "#0d111c"
            
            row = tk.Frame(self.results_frame, bg=bg_col, padx=10, pady=6, cursor="hand2")
            row.pack(fill=tk.X, pady=2)
            
            # Icona o pallino
            icon_lbl = tk.Label(row, text="" if item.get("type") != "calc" else "", font=("Helvetica", 14), bg=bg_col, fg="#38bdf8" if is_sel else "#94a3b8")
            icon_lbl.pack(side=tk.LEFT, padx=(4, 12))
            
            # Testi
            text_box = tk.Frame(row, bg=bg_col)
            text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            title_col = "#38bdf8" if is_sel else "#f8fafc"
            t_lbl = tk.Label(text_box, text=item["name"], font=("Helvetica", 12, "bold"), fg=title_col, bg=bg_col, anchor="w")
            t_lbl.pack(fill=tk.X)
            
            d_lbl = tk.Label(text_box, text=item["desc"], font=("Helvetica", 9), fg="#94a3b8", bg=bg_col, anchor="w")
            d_lbl.pack(fill=tk.X)
            
            # Clic sul mouse
            for widget in (row, icon_lbl, text_box, t_lbl, d_lbl):
                widget.bind("<Button-1>", lambda e, i=idx: self.click_item(i))
                
            self.items_widgets.append(row)

    def select_next(self, event=None):
        if self.filtered_results:
            max_show = min(len(self.filtered_results), 6)
            self.selected_index = (self.selected_index + 1) % max_show
            self.render_items()

    def select_prev(self, event=None):
        if self.filtered_results:
            max_show = min(len(self.filtered_results), 6)
            self.selected_index = (self.selected_index - 1) % max_show
            self.render_items()

    def click_item(self, idx):
        self.selected_index = idx
        self.launch_selected()

    def launch_selected(self, event=None):
        if not self.filtered_results:
            return
        item = self.filtered_results[self.selected_index]
        self.root.destroy()
        
        if item.get("type") == "calc":
            # Copia negli appunti se possibile
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(item["exec"].encode("utf-8"))
            except Exception:
                pass
            return

        cmd = item["exec"]
        subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    app = SpotlightWindow()
    app.root.mainloop()
