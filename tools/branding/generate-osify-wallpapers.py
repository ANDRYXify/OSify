#!/usr/bin/env python3
"""
OSify Wallpaper Generator Engine (by Andryx)
=============================================================================
Compone sfondi desktop all'avanguardia con gradiente dark obsidian,
glow radiale cibernetico, logo ufficiale OSify e tipografia professionale.
Genera sia la versione standard Full HD (1920x1080) sia la versione WSVGA (1024x600)
calibrata al millimetro per lo schermo del Toshiba NB200.
=============================================================================
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
LOGO_SRC = os.path.join(REPO_ROOT, "OSify.png")
OUT_DIR = os.path.join(REPO_ROOT, "desktop/branding/wallpapers")
os.makedirs(OUT_DIR, exist_ok=True)

def generate_wallpaper(width, height, filename):
    print(f"[+] Generazione sfondo OSify: {width}x{height} -> {filename}...")
    
    # 1. Base Dark Cyberpunk con Gradiente Radiale
    base = Image.new("RGBA", (width, height), (13, 13, 20, 255))
    draw = ImageDraw.Draw(base)

    # Disegna alone di luce viola centrale (#7C3AED con trasparenza)
    glow_size = int(min(width, height) * 0.85)
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    for r in range(glow_size // 2, 0, -2):
        alpha = int(45 * (1 - (r / (glow_size // 2))))
        glow_draw.ellipse(
            [glow_size // 2 - r, glow_size // 2 - r, glow_size // 2 + r, glow_size // 2 + r],
            fill=(124, 58, 237, alpha)
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=25))
    glow_pos = ((width - glow_size) // 2, (height - glow_size) // 2 - 20)
    base.paste(glow, glow_pos, glow)

    # 2. Caricamento e Sovrapposizione Logo OSify
    if os.path.exists(LOGO_SRC):
        logo = Image.open(LOGO_SRC).convert("RGBA")
        logo_target_h = int(height * 0.46)
        logo_aspect = logo.width / logo.height
        logo_target_w = int(logo_target_h * logo_aspect)
        logo_resized = logo.resize((logo_target_w, logo_target_h), Image.Resampling.LANCZOS)
        
        logo_x = (width - logo_target_w) // 2
        logo_y = (height - logo_target_h) // 2 - 30
        base.paste(logo_resized, (logo_x, logo_y), logo_resized)

    # 3. Tipografia e Firma Elegante
    draw = ImageDraw.Draw(base)
    text_sub = "OSify - Sistema Operativo ad Alte Prestazioni | Ingegnerizzato da Andrea Taliento"
    text_spec = f"Micro-Engine Edition • {width}x{height}" if height <= 600 else "Next-Gen Gaming & Multi-Runtime OS"
    
    # Calcolo coordinate centrate
    bbox_sub = draw.textbbox((0, 0), text_sub)
    sub_w = bbox_sub[2] - bbox_sub[0]
    
    bbox_spec = draw.textbbox((0, 0), text_spec)
    spec_w = bbox_spec[2] - bbox_spec[0]

    y_start = (height // 2) + int(height * 0.22)
    draw.text(((width - sub_w) // 2, y_start), text_sub, fill=(226, 232, 240, 230))
    draw.text(((width - spec_w) // 2, y_start + 24), text_spec, fill=(16, 185, 129, 210))

    out_path = os.path.join(OUT_DIR, filename)
    base.convert("RGB").save(out_path, quality=95)
    print(f"[✓] Salvato con successo: {out_path}")

if __name__ == "__main__":
    generate_wallpaper(1920, 1080, "osify-dark-1920x1080.png")
    generate_wallpaper(1024, 600, "osify-netbook-1024x600.png")
