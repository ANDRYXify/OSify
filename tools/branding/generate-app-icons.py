#!/usr/bin/env python3
"""
OSify Native Vector App Icon Generator
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Genera icone PNG native ad altissima risoluzione con super-sampling (antialiasing)
specifiche per ogni applicativo OSify, eliminando qualsiasi icona bianca generica.
=============================================================================
"""

import os
import math
from PIL import Image, ImageDraw

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ICONS_BASE = os.path.join(REPO_ROOT, "desktop/branding/icons")

# Palette Ufficiale OSify (Cyber Dark & Neon Accents)
BG_OBSIDIAN = "#0d1117"
BG_CARD = "#161b22"
BORDER_COLOR = "#30363d"

COLOR_HUB = "#8b5cf6"       # Viola Cyber Matrix
COLOR_BROWSER = "#38bdf8"   # Electric Sky Blue
COLOR_WIFI = "#10b981"      # Smeraldo / Menta Wireless
COLOR_GAMES = "#a855f7"     # Viola Neon Gaming
COLOR_DEV = "#f59e0b"       # Ambra / Oro Coding
COLOR_APPEARANCE = "#ec4899" # Magenta / Display
COLOR_TASKMGR = "#ef4444"   # Corallo / Rosso Telemetria
COLOR_TERM = "#22c55e"      # Verde Matrix Terminale
COLOR_INSTALL = "#10b981"   # Smeraldo Installazione Disco
COLOR_UPDATE = "#0ea5e9"    # Azzurro Sincronizzazione
COLOR_SETTINGS = "#94a3b8"  # Argento / Slate Impostazioni
COLOR_FILES = "#3b82f6"     # Blu Cobalto File Manager
COLOR_AUDIO = "#06b6d4"     # Ciano Brillante Suono
COLOR_DRAWER = "#a855f7"    # Viola App Drawer

def draw_squircle_tile(draw, size, bg_fill, border_color, radius):
    """Disegna la piastrella di sfondo arrotondata stile icona moderna OS."""
    draw.rounded_rectangle([2, 2, size - 3, size - 3], radius=radius, fill=bg_fill, outline=border_color, width=max(2, size // 32))

def create_icon(name, draw_symbol_fn, color_accent, size=64):
    scale = 4
    hi_size = size * scale
    im = Image.new("RGBA", (hi_size, hi_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # 1. Piastrella di sfondo stile squircle scura con bordo accento leggero
    tile_radius = int(hi_size * 0.22)
    d.rounded_rectangle([4, 4, hi_size - 5, hi_size - 5], radius=tile_radius, fill="#121620", outline="#252d3d", width=scale * 2)

    # 2. Cerchio di bagliore interno colorato (accent glow)
    glow_pad = int(hi_size * 0.12)
    d.ellipse([glow_pad, glow_pad, hi_size - glow_pad, hi_size - glow_pad], outline=color_accent, width=max(1, scale))

    # 3. Disegno simbolo specifico vettoriale
    draw_symbol_fn(d, hi_size, color_accent, scale)

    # 4. Ridimensionamento con super-sampling Lanczos per nitidezza perfetta
    resampled = im.resize((size, size), Image.Resampling.LANCZOS)
    return resampled

# --- Simboli Vettoriali Specifici ---

def sym_hub(d, sz, col, sc):
    # Razzo Cyber Matrix lanciato verso l'alto a destra
    cx, cy = sz // 2, sz // 2
    w = sz * 0.35
    # Corpo razzo (ogiva triangolare arrotondata)
    pts = [
        (cx + w * 0.6, cy - w * 0.6),
        (cx + w * 0.4, cy + w * 0.1),
        (cx - w * 0.1, cy + w * 0.4),
        (cx - w * 0.6, cy + w * 0.6),
        (cx - w * 0.4, cy - w * 0.1),
        (cx - w * 0.1, cy - w * 0.4),
    ]
    d.polygon(pts, fill=col)
    # Oblò centrale
    d.ellipse([cx - sc * 4, cy - sc * 4, cx + sc * 4, cy + sc * 4], fill="#ffffff")

def sym_browser(d, sz, col, sc):
    # Globo con meridiani e paralleli
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.28)
    lw = sc * 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=lw)
    d.line([(cx - r, cy), (cx + r, cy)], fill=col, width=lw)
    # Meridiano
    d.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=col, width=lw)

def sym_wifi(d, sz, col, sc):
    # Onde radio ad arco concentrico
    cx = sz // 2
    by = sz // 2 + int(sz * 0.18)
    # Punto base
    d.ellipse([cx - sc * 4, by - sc * 4, cx + sc * 4, by + sc * 4], fill=col)
    # 2 archi superiori
    for r in [int(sz * 0.18), int(sz * 0.32)]:
        d.arc([cx - r, by - r, cx + r, by + r], start=215, end=325, fill=col, width=sc * 3)

def sym_games(d, sz, col, sc):
    # Gamepad minimalista
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.32)
    h = int(sz * 0.18)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 6, outline=col, width=sc * 3)
    # D-pad sinistro
    d.line([(cx - w + sc * 8, cy), (cx - w + sc * 18, cy)], fill=col, width=sc * 2)
    d.line([(cx - w + sc * 13, cy - sc * 5), (cx - w + sc * 13, cy + sc * 5)], fill=col, width=sc * 2)
    # Tasti destra
    d.ellipse([cx + w - sc * 14, cy - sc * 6, cx + w - sc * 10, cy - sc * 2], fill=col)
    d.ellipse([cx + w - sc * 8, cy, cx + w - sc * 4, cy + sc * 4], fill=col)

def sym_developer(d, sz, col, sc):
    # Prompt '</>'
    cx, cy = sz // 2, sz // 2
    lw = sc * 3
    # '<'
    d.line([(cx - sc * 12, cy), (cx - sc * 22, cy - sc * 10)], fill=col, width=lw)
    d.line([(cx - sc * 12, cy), (cx - sc * 22, cy + sc * 10)], fill=col, width=lw)
    # '/'
    d.line([(cx - sc * 4, cy + sc * 14), (cx + sc * 4, cy - sc * 14)], fill="#ffffff", width=lw)
    # '>'
    d.line([(cx + sc * 12, cy), (cx + sc * 22, cy - sc * 10)], fill=col, width=lw)
    d.line([(cx + sc * 12, cy), (cx + sc * 22, cy + sc * 10)], fill=col, width=lw)

def sym_appearance(d, sz, col, sc):
    # Monitor e slider regolazione
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.28)
    h = int(sz * 0.20)
    d.rounded_rectangle([cx - w, cy - h - sc * 4, cx + w, cy + h - sc * 4], radius=sc * 4, outline=col, width=sc * 2)
    d.line([(cx, cy + h - sc * 4), (cx, cy + h + sc * 6)], fill=col, width=sc * 2)
    d.line([(cx - sc * 10, cy + h + sc * 6), (cx + sc * 10, cy + h + sc * 6)], fill=col, width=sc * 2)
    # Pennello / slider interno
    d.line([(cx - sc * 12, cy - sc * 4), (cx + sc * 12, cy - sc * 4)], fill="#ffffff", width=sc * 2)

def sym_taskmanager(d, sz, col, sc):
    # Elettrocardiogramma / telemetria CPU
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.32)
    lw = sc * 2
    pts = [
        (cx - w, cy),
        (cx - w * 0.5, cy),
        (cx - w * 0.25, cy - sc * 12),
        (cx, cy + sc * 16),
        (cx + w * 0.25, cy - sc * 8),
        (cx + w * 0.5, cy),
        (cx + w, cy)
    ]
    d.line(pts, fill=col, width=lw, joint="curve")

def sym_terminal(d, sz, col, sc):
    # Finestra shell con prompt >_
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.30)
    h = int(sz * 0.22)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 4, outline=col, width=sc * 2)
    # Prompt >
    d.line([(cx - w + sc * 6, cy - sc * 6), (cx - w + sc * 14, cy)], fill=col, width=sc * 2)
    d.line([(cx - w + sc * 14, cy), (cx - w + sc * 6, cy + sc * 6)], fill=col, width=sc * 2)
    # Underscore _
    d.line([(cx - w + sc * 18, cy + sc * 6), (cx - w + sc * 28, cy + sc * 6)], fill="#ffffff", width=sc * 2)

def sym_install(d, sz, col, sc):
    # Disco fisso con freccia rivolta verso il basso
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.28)
    h = int(sz * 0.12)
    # Drive HDD
    d.rounded_rectangle([cx - w, cy + sc * 2, cx + w, cy + sc * 2 + h], radius=sc * 3, outline=col, width=sc * 2)
    d.ellipse([cx + w - sc * 10, cy + sc * 6, cx + w - sc * 6, cy + sc * 10], fill=col)
    # Freccia in giù
    d.line([(cx, cy - sc * 16), (cx, cy - sc * 2)], fill="#ffffff", width=sc * 3)
    d.line([(cx - sc * 8, cy - sc * 8), (cx, cy - sc * 2)], fill="#ffffff", width=sc * 3)
    d.line([(cx + sc * 8, cy - sc * 8), (cx, cy - sc * 2)], fill="#ffffff", width=sc * 3)

def sym_update(d, sz, col, sc):
    # Frecce circolari sincronizzazione
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.24)
    lw = sc * 3
    d.arc([cx - r, cy - r, cx + r, cy + r], start=30, end=150, fill=col, width=lw)
    d.arc([cx - r, cy - r, cx + r, cy + r], start=210, end=330, fill=col, width=lw)

def sym_settings(d, sz, col, sc):
    # Ingranaggio geometrico
    cx, cy = sz // 2, sz // 2
    r_in = int(sz * 0.12)
    r_out = int(sz * 0.24)
    lw = sc * 2
    d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=col, width=lw)
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        x1 = cx + int(r_in * math.cos(rad))
        y1 = cy + int(r_in * math.sin(rad))
        x2 = cx + int(r_out * math.cos(rad))
        y2 = cy + int(r_out * math.sin(rad))
        d.line([(x1, y1), (x2, y2)], fill=col, width=sc * 3)

def sym_files(d, sz, col, sc):
    # Cartella documenti con tab
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.30)
    h = int(sz * 0.20)
    # Tab
    d.rounded_rectangle([cx - w, cy - h - sc * 4, cx - w + int(w * 0.8), cy - h + sc * 2], radius=sc * 2, fill=col)
    # Corpo
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 3, outline=col, width=sc * 2)

def sym_drawer(d, sz, col, sc):
    # Griglia di 9 quadratini (App Drawer / Launchpad)
    cx, cy = sz // 2, sz // 2
    step = int(sz * 0.16)
    r = sc * 4
    for dx in [-step, 0, step]:
        for dy in [-step, 0, step]:
            x = cx + dx
            y = cy + dy
            d.rounded_rectangle([x - r, y - r, x + r, y + r], radius=sc, fill=col)

def sym_profile(d, sz, col, sc):
    # Sagoma utente stilizzata: testa + spalle
    cx, cy = sz // 2, sz // 2
    r_head = int(sz * 0.12)
    # Testa
    d.ellipse([cx - r_head, cy - int(sz * 0.22), cx + r_head, cy - int(sz * 0.22) + r_head * 2], fill=col)
    # Spalle (arco / calotta arrotondata)
    w_body = int(sz * 0.26)
    d.pieslice([cx - w_body, cy - sc * 2, cx + w_body, cy + int(sz * 0.36)], start=180, end=360, fill=col)

def sym_users(d, sz, col, sc):
    # Due sagome utenti affiancate (Multiutenza)
    cx, cy = sz // 2, sz // 2
    # Utente sinistro (più piccolo, dietro)
    d.ellipse([cx - int(sz * 0.22), cy - int(sz * 0.20), cx - int(sz * 0.06), cy - int(sz * 0.04)], fill="#64748b")
    d.pieslice([cx - int(sz * 0.32), cy, cx + int(sz * 0.04), cy + int(sz * 0.32)], start=180, end=360, fill="#64748b")
    # Utente destro (in primo piano, accento)
    d.ellipse([cx - sc * 2, cy - int(sz * 0.16), cx + int(sz * 0.20), cy + int(sz * 0.06)], fill=col)
    d.pieslice([cx - int(sz * 0.14), cy + sc * 4, cx + int(sz * 0.28), cy + int(sz * 0.38)], start=180, end=360, fill=col)

def sym_audio(d, sz, col, sc):
    cx, cy = sz // 2, sz // 2
    # Cono altoparlante
    d.polygon([(cx - int(sz * 0.18), cy - int(sz * 0.08)),
               (cx - int(sz * 0.08), cy - int(sz * 0.08)),
               (cx + int(sz * 0.06), cy - int(sz * 0.20)),
               (cx + int(sz * 0.06), cy + int(sz * 0.20)),
               (cx - int(sz * 0.08), cy + int(sz * 0.08)),
               (cx - int(sz * 0.18), cy + int(sz * 0.08))], fill=col)
    # Onde sonore
    d.arc([cx, cy - int(sz * 0.16), cx + int(sz * 0.24), cy + int(sz * 0.16)], start=-60, end=60, fill="#ffffff", width=sc * 2)

def sym_bluetooth(d, sz, col, sc):
    cx, cy = sz // 2, sz // 2
    h = int(sz * 0.25)
    w = int(sz * 0.14)
    # Linea verticale centrale
    d.line([(cx, cy - h), (cx, cy + h)], fill=col, width=sc * 3)
    # Triangoli runici incrociati
    d.line([(cx - w, cy - int(h * 0.5)), (cx + w, cy + int(h * 0.5))], fill=col, width=sc * 2)
    d.line([(cx + w, cy + int(h * 0.5)), (cx, cy)], fill=col, width=sc * 2)
    d.line([(cx, cy), (cx + w, cy - int(h * 0.5))], fill=col, width=sc * 2)
    d.line([(cx + w, cy - int(h * 0.5)), (cx - w, cy + int(h * 0.5))], fill=col, width=sc * 2)

def sym_snapshot(d, sz, col, sc):
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.22)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=sc * 2)
    # Lancette orologio Time Machine
    d.line([(cx, cy), (cx, cy - int(r * 0.65))], fill="#ffffff", width=sc * 2)
    d.line([(cx, cy), (cx + int(r * 0.50), cy)], fill="#ffffff", width=sc * 2)
    # Arco di rotazione rollback
    d.arc([cx - r - sc * 4, cy - r - sc * 4, cx + r + sc * 4, cy + r + sc * 4], start=220, end=350, fill=col, width=sc * 2)

def sym_capture(d, sz, col, sc):
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.26)
    h = int(sz * 0.18)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 3, outline=col, width=sc * 2)
    # Cerchio lente / HDMI stream
    d.ellipse([cx - int(sz * 0.08), cy - int(sz * 0.08), cx + int(sz * 0.08), cy + int(sz * 0.08)], fill=col)

def sym_phone(d, sz, col, sc):
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.15)
    h = int(sz * 0.27)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 4, outline=col, width=sc * 2)
    # Schermo
    d.rounded_rectangle([cx - w + sc * 3, cy - h + sc * 6, cx + w - sc * 3, cy + h - sc * 8], radius=sc * 2, fill="#1e293b")
    # Home button / barra
    d.ellipse([cx - sc * 3, cy + h - sc * 6, cx + sc * 3, cy + h - sc * 2], fill=col)

def sym_power(d, sz, col, sc):
    # Simbolo Power universale (cerchio aperto in alto con linea verticale)
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.22)
    lw = sc * 3
    # Arco di cerchio aperto in alto (da -60 a 240 gradi)
    d.arc([cx - r, cy - r + sc * 2, cx + r, cy + r + sc * 2], start=-55, end=235, fill=col, width=lw)
    # Linea verticale superiore
    d.line([(cx, cy - r - sc * 4), (cx, cy + sc * 2)], fill="#ffffff", width=lw)

def sym_notepad(d, sz, col, sc):
    # Foglio di testo con righe
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.22)
    h = int(sz * 0.28)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 3, outline=col, width=sc * 2)
    # Righe di testo
    for y_off in [-sc * 8, 0, sc * 8, sc * 16]:
        d.line([(cx - w + sc * 6, cy + y_off), (cx + w - sc * 6, cy + y_off)], fill="#ffffff", width=sc * 2)

def sym_calculator(d, sz, col, sc):
    # Calcolatrice con schermo e tasti
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.22)
    h = int(sz * 0.28)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 4, outline=col, width=sc * 2)
    # Display LCD
    d.rounded_rectangle([cx - w + sc * 4, cy - h + sc * 4, cx + w - sc * 4, cy - h + sc * 14], radius=sc * 2, fill="#0284c7")
    # Tasti
    for ry in [0, sc * 8, sc * 16]:
        for rx in [-sc * 7, 0, sc * 7]:
            d.rectangle([cx + rx - sc * 2, cy + ry - sc * 2, cx + rx + sc * 2, cy + ry + sc * 2], fill=col)

def sym_keyboard(d, sz, col, sc):
    # Tastiera orizzontale
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.32)
    h = int(sz * 0.18)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 4, outline=col, width=sc * 2)
    for ry in [-sc * 4, sc * 4]:
        for rx in [-sc * 18, -sc * 9, 0, sc * 9, sc * 18]:
            d.rectangle([cx + rx - sc * 2, cy + ry - sc * 2, cx + rx + sc * 2, cy + ry + sc * 2], fill=col)

def sym_archive(d, sz, col, sc):
    # Scatola / cartella con cerniera
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.26)
    h = int(sz * 0.22)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 3, outline=col, width=sc * 2)
    # Cerniera verticale
    d.line([(cx, cy - h), (cx, cy + h)], fill="#f59e0b", width=sc * 2)
    d.rectangle([cx - sc * 4, cy - sc * 3, cx + sc * 4, cy + sc * 3], fill=col)

def sym_printer(d, sz, col, sc):
    # Stampante con foglio superiore
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.28)
    h = int(sz * 0.16)
    # Corpo stampante
    d.rounded_rectangle([cx - w, cy - h + sc * 4, cx + w, cy + h + sc * 4], radius=sc * 3, outline=col, width=sc * 2)
    # Foglio superiore
    d.rounded_rectangle([cx - w + sc * 8, cy - h - sc * 12, cx + w - sc * 8, cy - h + sc * 4], radius=sc * 2, fill="#ffffff")
    # Fessura carta inferiore
    d.line([(cx - w + sc * 6, cy + sc * 6), (cx + w - sc * 6, cy + sc * 6)], fill=col, width=sc * 2)

def sym_share(d, sz, col, sc):
    # 3 nodi di rete connessi (AirDrop-like)
    cx, cy = sz // 2, sz // 2
    r = sc * 5
    # Nodo centrale e due periferici
    d.line([(cx - sc * 12, cy), (cx + sc * 12, cy - sc * 10)], fill=col, width=sc * 2)
    d.line([(cx - sc * 12, cy), (cx + sc * 12, cy + sc * 10)], fill=col, width=sc * 2)
    d.ellipse([cx - sc * 12 - r, cy - r, cx - sc * 12 + r, cy + r], fill="#38bdf8")
    d.ellipse([cx + sc * 12 - r, cy - sc * 10 - r, cx + sc * 12 + r, cy - sc * 10 + r], fill="#10b981")
    d.ellipse([cx + sc * 12 - r, cy + sc * 10 - r, cx + sc * 12 + r, cy + sc * 10 + r], fill="#f59e0b")

def sym_thermal(d, sz, col, sc):
    # Termometro graduato
    cx, cy = sz // 2, sz // 2
    r = sc * 7
    # Bulbo inferiore
    d.ellipse([cx - r, cy + sc * 6 - r, cx + r, cy + sc * 6 + r], fill=col)
    # Tubo verticale
    d.rounded_rectangle([cx - sc * 3, cy - sc * 18, cx + sc * 3, cy + sc * 6], radius=sc * 2, outline=col, width=sc * 2)
    d.line([(cx, cy - sc * 14), (cx, cy + sc * 6)], fill="#ffffff", width=sc * 2)

def sym_benchmark(d, sz, col, sc):
    # Tachimetro circolare con lancetta
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.26)
    d.arc([cx - r, cy - r, cx + r, cy + r], start=140, end=400, fill=col, width=sc * 3)
    # Lancetta verso l'alto a destra (alte prestazioni)
    d.line([(cx, cy), (cx + sc * 12, cy - sc * 12)], fill="#ef4444", width=sc * 3)
    d.ellipse([cx - sc * 4, cy - sc * 4, cx + sc * 4, cy + sc * 4], fill="#ffffff")

def sym_firewall(d, sz, col, sc):
    # Scudo di rete perimetrale
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.24)
    h = int(sz * 0.26)
    pts = [
        (cx - w, cy - h),
        (cx + w, cy - h),
        (cx + w, cy),
        (cx, cy + h),
        (cx - w, cy)
    ]
    d.polygon(pts, outline=col, fill="#0f172a")
    d.line([(cx - w + sc * 6, cy - sc * 4), (cx + w - sc * 6, cy - sc * 4)], fill="#ef4444", width=sc * 2)
    d.line([(cx, cy - h + sc * 4), (cx, cy + h - sc * 6)], fill="#ef4444", width=sc * 2)

def sym_time(d, sz, col, sc):
    # Orologio analogico circolare
    cx, cy = sz // 2, sz // 2
    r = int(sz * 0.26)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=sc * 3)
    # Lancette (10:10)
    d.line([(cx, cy), (cx - sc * 8, cy - sc * 12)], fill="#ffffff", width=sc * 2)
    d.line([(cx, cy), (cx + sc * 14, cy - sc * 6)], fill="#38bdf8", width=sc * 2)
    d.ellipse([cx - sc * 3, cy - sc * 3, cx + sc * 3, cy + sc * 3], fill=col)

def sym_touchpad(d, sz, col, sc):
    # Touchpad rettangolare con tasti sinistro/destro
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.28)
    h = int(sz * 0.22)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=sc * 3, outline=col, width=sc * 2)
    # Linea divisoria tasti inferiori
    d.line([(cx - w + sc * 4, cy + h - sc * 10), (cx + w - sc * 4, cy + h - sc * 10)], fill=col, width=sc * 2)
    d.line([(cx, cy + h - sc * 10), (cx, cy + h - sc * 2)], fill=col, width=sc * 2)

def sym_search(d, sz, col, sc):
    # Lente d'ingrandimento
    cx, cy = sz // 2 - sc * 4, sz // 2 - sc * 4
    r = int(sz * 0.18)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=sc * 3)
    # Manico inclinato a 45 gradi
    d.line([(cx + int(r * 0.7), cy + int(r * 0.7)), (cx + r + sc * 16, cy + r + sc * 16)], fill="#38bdf8", width=sc * 4)

def sym_usb(d, sz, col, sc):
    # Chiavetta USB con connettore metallico
    cx, cy = sz // 2, sz // 2
    w = int(sz * 0.16)
    h = int(sz * 0.24)
    # Corpo
    d.rounded_rectangle([cx - w, cy - h + sc * 10, cx + w, cy + h], radius=sc * 3, fill=col)
    # Connettore
    d.rectangle([cx - w + sc * 4, cy - h, cx + w - sc * 4, cy - h + sc * 10], outline="#ffffff", width=sc * 2)

ICONS_REGISTRY = {
    "osify-hub": (sym_hub, COLOR_HUB),
    "osify-browser": (sym_browser, COLOR_BROWSER),
    "osify-wifi": (sym_wifi, COLOR_WIFI),
    "osify-games": (sym_games, COLOR_GAMES),
    "osify-developer": (sym_developer, COLOR_DEV),
    "osify-appearance": (sym_appearance, COLOR_APPEARANCE),
    "osify-taskmanager": (sym_taskmanager, COLOR_TASKMGR),
    "osify-terminal": (sym_terminal, COLOR_TERM),
    "osify-install": (sym_install, COLOR_INSTALL),
    "osify-update": (sym_update, COLOR_UPDATE),
    "osify-settings": (sym_settings, COLOR_SETTINGS),
    "osify-files": (sym_files, COLOR_FILES),
    "osify-drawer": (sym_drawer, COLOR_DRAWER),
    "osify-profile": (sym_profile, "#06b6d4"),
    "osify-users": (sym_users, "#3b82f6"),
    "osify-audio": (sym_audio, COLOR_AUDIO),
    "osify-bluetooth": (sym_bluetooth, COLOR_WIFI),
    "osify-snapshot": (sym_snapshot, "#10b981"),
    "osify-capture": (sym_capture, "#f43f5e"),
    "osify-phone": (sym_phone, "#38bdf8"),
    "osify-power": (sym_power, "#ef4444"),
    "osify-notepad": (sym_notepad, "#38bdf8"),
    "osify-calculator": (sym_calculator, "#10b981"),
    "osify-keyboard": (sym_keyboard, "#a855f7"),
    "osify-archive": (sym_archive, "#f59e0b"),
    "osify-printer": (sym_printer, "#6366f1"),
    "osify-share": (sym_share, "#0ea5e9"),
    "osify-thermal": (sym_thermal, "#f97316"),
    "osify-benchmark": (sym_benchmark, "#ec4899"),
    "osify-firewall": (sym_firewall, "#ef4444"),
    "osify-time": (sym_time, "#38bdf8"),
    "osify-touchpad": (sym_touchpad, "#06b6d4"),
    "osify-search": (sym_search, "#f59e0b"),
    "osify-usb": (sym_usb, "#10b981"),
}

def main():
    print("[+] Generazione icone native vettoriali OSify in alta risoluzione...")
    for size in [48, 64, 128]:
        out_dir = os.path.join(ICONS_BASE, str(size))
        os.makedirs(out_dir, exist_ok=True)
        for name, (draw_fn, color) in ICONS_REGISTRY.items():
            img = create_icon(name, draw_fn, color, size=size)
            target_path = os.path.join(out_dir, f"{name}.png")
            img.save(target_path, "PNG")
    print(f"[✓] Generate con successo {len(ICONS_REGISTRY)} icone per i formati 48px, 64px e 128px!")

if __name__ == "__main__":
    main()
