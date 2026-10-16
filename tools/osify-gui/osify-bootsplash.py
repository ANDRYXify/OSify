#!/usr/bin/env python3
"""
==============================================================================
OSify OLED Boot Splash & System Initializer
==============================================================================
Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
Offre un'esperienza di avvio in stile Apple macOS:
- Schermo nero profondo (OLED #000000)
- Logo OSify luminescente centrato
- Sottile barra di caricamento minimalista a capsula
- Transizione fluida e silenziosa verso l'OOBE o il Desktop
==============================================================================
"""

import os
import sys
import time
import tkinter as tk
from PIL import Image, ImageTk

# Ricerca del logo OSify
LOGO_CANDIDATES = [
    "/usr/share/pixmaps/osify.png",
    "/usr/share/pixmaps/OSify.png",
    "/usr/share/icons/hicolor/256x256/apps/osify.png",
    "/usr/share/icons/hicolor/128x128/apps/osify.png",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../OSify.png")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../desktop/branding/icons/256/osify.png")),
]

STATUS_STEPS = [
    (0.05, "Avvio del sottosistema HAL OSify..."),
    (0.25, "Inizializzazione driver grafici e accelerazione..."),
    (0.50, "Caricamento stack di rete e audio a bassa latenza..."),
    (0.75, "Preparazione ambiente desktop macOS 2050..."),
    (1.00, "Pronto."),
]

class OSifyBootSplash:
    def __init__(self, root):
        self.root = root
        self.root.title("OSify Boot")
        self.root.configure(bg="#000000")
        
        # Copertura a tutto schermo
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        self.root.geometry(f"{self.sw}x{self.sh}+0+0")
        self.root.attributes("-fullscreen", True)
        self.root.config(cursor="none")

        # Possibilità di saltare premendo Esc, Spazio o Invio
        self.root.bind("<Escape>", lambda e: self.finish())
        self.root.bind("<space>", lambda e: self.finish())
        self.root.bind("<Return>", lambda e: self.finish())

        self.canvas = tk.Canvas(
            self.root,
            width=self.sw,
            height=self.sh,
            bg="#000000",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.cx = self.sw // 2
        self.cy = self.sh // 2 - 30

        # Carica Logo
        self.logo_img = None
        for cand in LOGO_CANDIDATES:
            if os.path.exists(cand):
                try:
                    pil_img = Image.open(cand).convert("RGBA")
                    # Scala logo appropriatamente (es. 120x120 o 140x140)
                    target_size = min(140, int(self.sh * 0.22))
                    pil_img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(pil_img)
                    break
                except Exception:
                    pass

        if self.logo_img:
            self.canvas.create_image(self.cx, self.cy, image=self.logo_img)
        else:
            self.canvas.create_text(
                self.cx, self.cy,
                text="OSify",
                font=("Helvetica", 36, "bold"),
                fill="#ffffff"
            )

        # Barra di avanzamento minimalista Apple Style
        self.bar_w = min(280, int(self.sw * 0.35))
        self.bar_h = 4
        self.bar_x0 = self.cx - self.bar_w // 2
        self.bar_y0 = self.cy + 90
        self.bar_x1 = self.cx + self.bar_w // 2
        self.bar_y1 = self.bar_y0 + self.bar_h

        # Sfondo barra (grigio scuro tenue)
        self.canvas.create_rectangle(
            self.bar_x0, self.bar_y0, self.bar_x1, self.bar_y1,
            fill="#27272a", outline=""
        )

        # Barra riempimento
        self.fill_rect = self.canvas.create_rectangle(
            self.bar_x0, self.bar_y0, self.bar_x0, self.bar_y1,
            fill="#f4f4f5", outline=""
        )

        # Testo di stato
        self.status_text = self.canvas.create_text(
            self.cx, self.bar_y0 + 26,
            text="Avvio di OSify...",
            font=("Helvetica", 9),
            fill="#71717a"
        )

        self.progress = 0.0
        self.start_time = time.time()
        self.duration = 1.6 # secondi totali di boot animation
        self.update_animation()

    def update_animation(self):
        elapsed = time.time() - self.start_time
        self.progress = min(1.0, elapsed / self.duration)

        # Aggiorna larghezza barra
        cur_w = int(self.bar_w * self.progress)
        self.canvas.coords(
            self.fill_rect,
            self.bar_x0, self.bar_y0, self.bar_x0 + cur_w, self.bar_y1
        )

        # Aggiorna testo di stato
        for threshold, msg in STATUS_STEPS:
            if self.progress <= threshold:
                self.canvas.itemconfig(self.status_text, text=msg)
                break

        if self.progress < 1.0:
            self.root.after(25, self.update_animation)
        else:
            self.root.after(150, self.finish)

    def finish(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

def main():
    root = tk.Tk()
    app = OSifyBootSplash(root)
    root.mainloop()

if __name__ == "__main__":
    main()
