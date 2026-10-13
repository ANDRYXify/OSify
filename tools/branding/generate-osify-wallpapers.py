#!/usr/bin/env python3
"""
=============================================================================
OSify Wallpaper Generator Engine — Clean Minimal Edition (by Andryx)
=============================================================================
Genera sfondi puri, minimalisti ed eleganti privi di sottotitoli o scritte:
- Solo artwork ufficiale: base dark obsidian, alone radiale cyberpunk viola/ciano,
  logo OSify centrale in alta fedeltà.
- Risoluzioni multiple:
  • 1024x600 (WSVGA Netbook / Toshiba NB200)
  • 1024x768 (Vintage 4:3 CRT / Monitor Legacy)
  • 1280x800 (Steam Deck / Handheld 16:10)
  • 1920x1080 (Full HD 16:9)
  • 2560x1440 (2K QHD 16:9)
  • 3840x2160 (4K UHD 16:9)
=============================================================================
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
LOGO_SRC = os.path.join(REPO_ROOT, "OSify.png")
OUT_DIR = os.path.join(REPO_ROOT, "desktop/branding/wallpapers")
os.makedirs(OUT_DIR, exist_ok=True)

def generate_clean_wallpaper(width, height, filename):
    print(f"[+] Generazione sfondo clean (solo immagine, zero testo): {width}x{height} -> {filename}...")
    
    # 1. Base Dark Obsidian
    base = Image.new("RGBA", (width, height), (10, 12, 18, 255))
    
    # 2. Alone di luce radiale cyberpunk centrale (#7C3AED e sfumatura profonda)
    glow_size = int(min(width, height) * 0.95)
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    radius = glow_size // 2
    for r in range(radius, 0, -2):
        alpha = int(40 * (1 - (r / radius)))
        glow_draw.ellipse(
            [radius - r, radius - r, radius + r, radius + r],
            fill=(124, 58, 237, alpha)
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=int(min(width, height) * 0.05)))
    glow_pos = ((width - glow_size) // 2, (height - glow_size) // 2)
    base.paste(glow, glow_pos, glow)

    # 3. Logo OSify perfettamente centrato
    if os.path.exists(LOGO_SRC):
        logo = Image.open(LOGO_SRC).convert("RGBA")
        # Proporzione bilanciata: 48% dell'altezza dello schermo
        logo_target_h = int(height * 0.48)
        logo_aspect = logo.width / logo.height
        logo_target_w = int(logo_target_h * logo_aspect)
        resample_filter = getattr(getattr(Image, 'Resampling', None), 'LANCZOS', getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1)))
        logo_resized = logo.resize((logo_target_w, logo_target_h), resample_filter)
        
        logo_x = (width - logo_target_w) // 2
        logo_y = (height - logo_target_h) // 2
        base.paste(logo_resized, (logo_x, logo_y), logo_resized)

    # 4. Salvataggio in PNG RGB alta qualità
    out_path = os.path.join(OUT_DIR, filename)
    base.convert("RGB").save(out_path, quality=95)
    print(f"[✓] Salvato sfondo clean: {out_path}")

def main():
    resolutions = [
        (1024, 600, "osify-netbook-1024x600.png"),
        (1024, 600, "osify-clean-1024x600.png"),
        (1024, 768, "osify-clean-1024x768.png"),
        (1280, 800, "osify-clean-1280x800.png"),
        (1920, 1080, "osify-dark-1920x1080.png"),
        (1920, 1080, "osify-clean-1920x1080.png"),
        (2560, 1440, "osify-clean-2560x1440.png"),
        (3840, 2160, "osify-clean-3840x2160.png"),
    ]
    for w, h, fname in resolutions:
        generate_clean_wallpaper(w, h, fname)

if __name__ == "__main__":
    main()
