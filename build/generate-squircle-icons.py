#!/usr/bin/env python3
"""
==============================================================================
OSify macOS Squircle Icon Set Builder
==============================================================================
Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
Taglia le icone generate ad altissima definizione, applica una maschera
squircle perfetta con angoli arrotondati stile Apple macOS, riflessi
e le esporta in tutte le risoluzioni standard: 16, 24, 32, 48, 64, 128, 256, 512.
==============================================================================
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_SHEET1 = "/Users/andryxify/.gemini/antigravity-ide/brain/8e1ce86a-d1cb-440c-9e32-b5f414d5f7a9/osify_app_icons_1792175681091.jpg"
SRC_SHEET2 = "/Users/andryxify/.gemini/antigravity-ide/brain/8e1ce86a-d1cb-440c-9e32-b5f414d5f7a9/osify_extra_icons_1792175777304.jpg"
DEST_ICONS_DIR = os.path.join(REPO_ROOT, "desktop/branding/icons")

RESOLUTIONS = [16, 24, 32, 48, 64, 128, 256, 512]

def create_squircle_mask(size, radius_ratio=0.22):
    scale = 4
    large_size = (size[0] * scale, size[1] * scale)
    mask = Image.new("L", large_size, 0)
    draw = ImageDraw.Draw(mask)
    r = int(min(large_size) * radius_ratio)
    draw.rounded_rectangle([(0, 0), (large_size[0] - 1, large_size[1] - 1)], radius=r, fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)

def process_and_save_icon(img_crop, icon_name):
    w, h = img_crop.size
    dim = min(w, h)
    left = (w - dim) // 2
    top = (h - dim) // 2
    square = img_crop.crop((left, top, left + dim, top + dim)).convert("RGBA")

    # Applica maschera squircle
    mask = create_squircle_mask((dim, dim))
    output_base = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
    output_base.paste(square, (0, 0), mask=mask)

    for res in RESOLUTIONS:
        res_dir = os.path.join(DEST_ICONS_DIR, str(res))
        os.makedirs(res_dir, exist_ok=True)
        out_path = os.path.join(res_dir, f"{icon_name}.png")
        resized = output_base.resize((res, res), Image.Resampling.LANCZOS)
        resized.save(out_path, "PNG", optimize=True)
    print(f"[+] Generata icona squircle: {icon_name} (16px -> 512px)")

def main():
    print("[*] Caricamento sheet icone...")
    if not os.path.exists(SRC_SHEET1) or not os.path.exists(SRC_SHEET2):
        print("[-] Errore: file sorgente mancanti!")
        sys.exit(1)

    im1 = Image.open(SRC_SHEET1)
    im2 = Image.open(SRC_SHEET2)

    # Coordinate precise ritagli Sheet 1
    crops1 = {
        "osify-files": (78, 78, 338, 338),
        "osify-browser": (372, 78, 632, 338),
        "osify-terminal": (666, 78, 926, 338),
        "osify-settings": (78, 372, 338, 632),
        "osify-hub": (372, 372, 632, 632),
        "osify-games": (666, 372, 926, 632),
    }

    for name, box in crops1.items():
        cropped = im1.crop(box)
        process_and_save_icon(cropped, name)

    # Coordinate precise ritagli Sheet 2
    crops2 = {
        "osify-drawer": (55, 360, 335, 640),
        "osify-audio": (368, 360, 648, 640),
        "osify-wifi": (680, 360, 960, 640),
    }

    for name, box in crops2.items():
        cropped = im2.crop(box)
        process_and_save_icon(cropped, name)

    # Genera anche icone derivate collegate
    # Per osify.png generiamo la gemma/logo originale pulita
    logo_src = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(logo_src):
        logo_im = Image.open(logo_src)
        process_and_save_icon(logo_im, "osify")
        process_and_save_icon(logo_im, "osify-about")

    print("[OK] Tutte le icone squircle OSify sono state esportate con successo!")

if __name__ == "__main__":
    main()
