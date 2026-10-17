#!/usr/bin/env python3
"""
==============================================================================
OSify Smart Media Processor & Zero-Burden Customizer Engine
==============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Gestisce autonomamente l'adattamento geometrico, il resampling ad alta
definizione e la normalizzazione cromatica per sfondi, avatar e icone.
L'utente non deve preoccuparsi di proporzioni, risoluzioni o formati:
il motore elabora qualsiasi file (JPG, PNG, WEBP, BMP, GIF) in tempo reale.
==============================================================================
"""

import sys
import os
import subprocess

def get_screen_resolution():
    try:
        out = subprocess.check_output("xrandr 2>/dev/null | grep '\\*' | awk '{print $1}' | head -n1", shell=True, text=True).strip()
        if "x" in out:
            w, h = out.split("x")
            return int(w), int(h)
    except Exception:
        pass
    return 1024, 600

def process_wallpaper(src_path, dst_path, mode="smart_blur"):
    target_w, target_h = get_screen_resolution()
    
    try:
        from PIL import Image, ImageFilter, ImageOps
        img = Image.open(src_path).convert("RGBA")
        src_w, src_h = img.size

        # Se le proporzioni coincidono quasi esattamente (+/- 2%)
        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        if abs(target_ratio - src_ratio) < 0.05 or mode == "crop":
            # Smart Center-Crop
            fitted = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            final_img = fitted.convert("RGB")
        elif mode == "smart_blur":
            # Sfondo con sfocatura artistica Bokeh per evitare bande nere
            bg = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.BILINEAR, centering=(0.5, 0.5))
            bg = bg.filter(ImageFilter.GaussianBlur(radius=25))
            
            # Immagine frontale centrata senza alcuna deformazione
            scale = min(target_w / src_w, target_h / src_h)
            fg_w = int(src_w * scale)
            fg_h = int(src_h * scale)
            fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
            
            pos_x = (target_w - fg_w) // 2
            pos_y = (target_h - fg_h) // 2
            bg.paste(fg, (pos_x, pos_y), fg)
            final_img = bg.convert("RGB")
        else: # Stretch
            final_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS).convert("RGB")

        os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
        final_img.save(dst_path, "JPEG", quality=92, optimize=True)
        print(f"[[OK]] Sfondo generato con successo: {dst_path} ({target_w}x{target_h})")
        return True
    except Exception as e:
        # Fallback ImageMagick / Netpbm
        print(f"[!] Fallback PIL non disponibile: {e}")
        if os.system(f"convert '{src_path}' -resize '{target_w}x{target_h}^' -gravity center -extent '{target_w}x{target_h}' '{dst_path}' 2>/dev/null") == 0:
            return True
        # Copia grezza diretta
        os.system(f"cp -f '{src_path}' '{dst_path}' 2>/dev/null")
        return False

def process_avatar(src_path, dst_path, size=128):
    try:
        from PIL import Image, ImageOps, ImageDraw
        img = Image.open(src_path).convert("RGBA")
        
        # Ritaglio quadrato centrato ad alta precisione
        square = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        
        # Maschera circolare smussata antialiasing
        mask = Image.new("L", (size * 4, size * 4), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size * 4, size * 4), fill=255)
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)

        avatar = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        avatar.paste(square, (0, 0), mask=mask)

        # Anello cromatico ciano Cyber OSify
        draw_border = ImageDraw.Draw(avatar)
        draw_border.ellipse((1, 1, size - 2, size - 2), outline=(6, 182, 212, 220), width=3)

        os.makedirs(os.path.dirname(os.path.abspath(dst_path)), exist_ok=True)
        avatar.save(dst_path, "PNG")
        print(f"[[OK]] Avatar utente normalizzato: {dst_path} ({size}x{size})")
        return True
    except Exception as e:
        print(f"[!] Fallback avatar: {e}")
        os.system(f"cp -f '{src_path}' '{dst_path}' 2>/dev/null")
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--wallpaper":
        mode = sys.argv[4] if len(sys.argv) > 4 else "smart_blur"
        process_wallpaper(sys.argv[2], sys.argv[3], mode)
    elif len(sys.argv) >= 4 and sys.argv[1] == "--avatar":
        process_avatar(sys.argv[2], sys.argv[3])
    else:
        print("Uso: osify-media-processor --wallpaper <input> <output> [smart_blur|crop|stretch]")
        print("     osify-media-processor --avatar <input> <output>")
