"""
Modulo di Generazione Asset Grafici Vettoriali e Capsule per OSify UI
=============================================================================
Ingegnerizzato per eliminare completamente qualsiasi dipendenza da emoji,
icone a bassa risoluzione o contrasti sgradevoli. Produce una grafica nitida,
anti-aliased in puro stile SteamOS e KDE Plasma 6 Breeze Dark.
=============================================================================
"""

import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Palette Ufficiale SteamOS / KDE Plasma 6 Dark Slate
COLOR_BG_BASE = "#0b0e14"        # Sfondo profondo slate
COLOR_BG_SURFACE = "#141a24"     # Superfici schede e pannelli
COLOR_BG_CARD = "#192231"        # Sfondo card inattiva
COLOR_BG_CARD_HOVER = "#202c3f"  # Sfondo card con focus
COLOR_ACCENT_BLUE = "#1a9fff"    # Steam Electric Blue
COLOR_ACCENT_CYAN = "#38bdf8"    # Sky Blue
COLOR_ACCENT_MINT = "#10b981"    # Verde smeraldo soft (Verified)
COLOR_TEXT_PRIMARY = "#f1f5f9"   # Bianco slate morbido
COLOR_TEXT_MUTED = "#8292a4"     # Grigio slate secondario
COLOR_BORDER_SUBTLE = "#222d3d"  # Bordo 1px discreto
COLOR_BORDER_FOCUS = "#1a9fff"   # Bordo attivo al focus
COLOR_PILL_BG = "#1e293b"        # Sfondo capsule badge

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    """Disegna un rettangolo con angoli arrotondati e antialiasing."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def create_vector_icon(icon_type, size=32, color="#94a3b8", scale=4):
    """
    Genera un'icona vettoriale pulita ad altissima definizione con super-sampling.
    Nessuna emoji, nessun glifo degradato. 100% grafica geometrica pura.
    """
    hi_size = size * scale
    im = Image.new("RGBA", (hi_size, hi_size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(2, int(scale * 1.8))

    pad = int(hi_size * 0.15)
    w = hi_size - 2 * pad
    h = hi_size - 2 * pad

    if icon_type == "gamepad":
        # Sagoma minimalista di un controller handheld / Steam Deck
        rx0, ry0 = pad, pad + int(h * 0.2)
        rx1, ry1 = hi_size - pad, pad + int(h * 0.8)
        draw_rounded_rect(d, (rx0, ry0, rx1, ry1), radius=int(scale * 6), outline=color, width=lw)
        # D-pad (croce sinistra)
        cx, cy = rx0 + int(w * 0.25), ry0 + int((ry1 - ry0) * 0.5)
        cs = int(scale * 4)
        d.line([(cx - cs, cy), (cx + cs, cy)], fill=color, width=lw)
        d.line([(cx, cy - cs), (cx, cy + cs)], fill=color, width=lw)
        # Tasti ABXY (punti destra)
        bx, by = rx1 - int(w * 0.25), cy
        bs = int(scale * 2.5)
        d.ellipse([bx - bs, by - bs, bx + bs, by + bs], fill=color)

    elif icon_type == "desktop":
        # Monitor con base elegante
        mx0, my0 = pad, pad + int(h * 0.1)
        mx1, my1 = hi_size - pad, pad + int(h * 0.7)
        draw_rounded_rect(d, (mx0, my0, mx1, my1), radius=int(scale * 3), outline=color, width=lw)
        # Supporto e base
        cx = hi_size // 2
        d.line([(cx, my1), (cx, my1 + int(h * 0.15))], fill=color, width=lw)
        d.line([(cx - int(w * 0.25), my1 + int(h * 0.15)), (cx + int(w * 0.25), my1 + int(h * 0.15))], fill=color, width=lw)

    elif icon_type == "terminal":
        # Finestra shell con prompt >_
        draw_rounded_rect(d, (pad, pad, hi_size - pad, hi_size - pad), radius=int(scale * 4), outline=color, width=lw)
        # Prompt '>'
        px0 = pad + int(w * 0.2)
        py0 = pad + int(h * 0.35)
        d.line([(px0, py0), (px0 + int(w * 0.15), py0 + int(h * 0.15))], fill=color, width=lw)
        d.line([(px0 + int(w * 0.15), py0 + int(h * 0.15)), (px0, py0 + int(h * 0.3))], fill=color, width=lw)
        # Cursore '_'
        cx0 = px0 + int(w * 0.25)
        cy0 = py0 + int(h * 0.3)
        d.line([(cx0, cy0), (cx0 + int(w * 0.25), cy0)], fill=color, width=lw)

    elif icon_type == "browser":
        # Globo con paralleli e meridiani puliti
        cx, cy = hi_size // 2, hi_size // 2
        r = int(w * 0.45)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=lw)
        # Linea equatoriale
        d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=lw)
        # Meridiano centrale ellittico
        mr = int(r * 0.5)
        d.ellipse([cx - mr, cy - r, cx + mr, cy + r], outline=color, width=lw)

    elif icon_type == "folder":
        # Cartella moderna a tab
        fx0, fy0 = pad, pad + int(h * 0.25)
        fx1, fy1 = hi_size - pad, pad + int(h * 0.85)
        # Tab superiore
        tab_w = int(w * 0.4)
        tab_h = int(h * 0.15)
        draw_rounded_rect(d, (fx0, fy0 - tab_h, fx0 + tab_w, fy0 + 2), radius=int(scale * 2), fill=color)
        draw_rounded_rect(d, (fx0, fy0, fx1, fy1), radius=int(scale * 3), outline=color, width=lw)

    elif icon_type == "chip":
        # Microchip UEM con pin perimetrali
        cx0, cy0 = pad + int(w * 0.2), pad + int(h * 0.2)
        cx1, cy1 = hi_size - pad - int(w * 0.2), hi_size - pad - int(h * 0.2)
        draw_rounded_rect(d, (cx0, cy0, cx1, cy1), radius=int(scale * 3), outline=color, width=lw)
        # Pin esterni
        step = int((cx1 - cx0) / 4)
        for i in range(1, 4):
            # Sopra e sotto
            x = cx0 + i * step
            d.line([(x, cy0 - int(h * 0.12)), (x, cy0)], fill=color, width=lw)
            d.line([(x, cy1), (x, cy1 + int(h * 0.12))], fill=color, width=lw)
            # Sinistra e destra
            y = cy0 + i * step
            d.line([(cx0 - int(w * 0.12), y), (cx0, y)], fill=color, width=lw)
            d.line([(cx1, y), (cx1 + int(w * 0.12), y)], fill=color, width=lw)

    elif icon_type == "sliders":
        # Equalizzatore / impostazioni
        step = w / 3
        # Canale 1
        x1 = pad + int(step * 0.5)
        d.line([(x1, pad), (x1, hi_size - pad)], fill=color, width=lw)
        d.ellipse([x1 - int(scale * 3), pad + int(h * 0.3) - int(scale * 3), x1 + int(scale * 3), pad + int(h * 0.3) + int(scale * 3)], fill=color)
        # Canale 2
        x2 = pad + int(step * 1.5)
        d.line([(x2, pad), (x2, hi_size - pad)], fill=color, width=lw)
        d.ellipse([x2 - int(scale * 3), pad + int(h * 0.7) - int(scale * 3), x2 + int(scale * 3), pad + int(h * 0.7) + int(scale * 3)], fill=color)
        # Canale 3
        x3 = pad + int(step * 2.5)
        d.line([(x3, pad), (x3, hi_size - pad)], fill=color, width=lw)
        d.ellipse([x3 - int(scale * 3), pad + int(h * 0.4) - int(scale * 3), x3 + int(scale * 3), pad + int(h * 0.4) + int(scale * 3)], fill=color)

    elif icon_type == "wifi":
        # Onde radio ad arco
        cx = hi_size // 2
        base_y = hi_size - pad - int(scale * 2)
        # Punto base
        d.ellipse([cx - int(scale * 2), base_y - int(scale * 2), cx + int(scale * 2), base_y + int(scale * 2)], fill=color)
        # Archi
        for r_step in [int(w * 0.25), int(w * 0.45)]:
            bbox = [cx - r_step, base_y - r_step, cx + r_step, base_y + r_step]
            d.arc(bbox, start=220, end=320, fill=color, width=lw)

    elif icon_type == "battery":
        # Rettangolo batteria con polo
        bx0, by0 = pad, pad + int(h * 0.25)
        bx1, by1 = hi_size - pad - int(w * 0.1), pad + int(h * 0.75)
        draw_rounded_rect(d, (bx0, by0, bx1, by1), radius=int(scale * 3), outline=color, width=lw)
        # Polo positivo
        d.rectangle([bx1, by0 + int((by1 - by0) * 0.3), bx1 + int(w * 0.08), by1 - int((by1 - by0) * 0.3)], fill=color)
        # Livello di carica (barre interne piene)
        d.rectangle([bx0 + int(scale * 4), by0 + int(scale * 3), bx0 + int((bx1 - bx0) * 0.75), by1 - int(scale * 3)], fill=color)

    elif icon_type == "power":
        # Simbolo universale Power IEC 5009 (cerchio aperto con segmento verticale)
        cx, cy = hi_size // 2, hi_size // 2
        r = int(w * 0.40)
        # Arco cerchio da 45 gradi a 315 gradi
        d.arc([cx - r, cy - r, cx + r, cy + r], start=125, end=415, fill=color, width=lw)
        # Linea verticale superiore
        d.line([(cx, cy - r - int(scale * 2)), (cx, cy)], fill=color, width=lw)

    elif icon_type == "gear" or icon_type == "settings":
        # Ingranaggio / ruota dentata geometrica pulita
        cx, cy = hi_size // 2, hi_size // 2
        r_out = int(w * 0.42)
        r_in = int(w * 0.22)
        # Cerchio centrale vuoto
        d.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in], outline=color, width=lw)
        # Denti esterni
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            x1 = cx + int((r_in + 2) * math.cos(rad))
            y1 = cy + int((r_in + 2) * math.sin(rad))
            x2 = cx + int(r_out * math.cos(rad))
            y2 = cy + int(r_out * math.sin(rad))
            d.line([(x1, y1), (x2, y2)], fill=color, width=int(lw * 1.2))

    elif icon_type == "verified":
        # Badge verificato: cerchio con spunta nitida
        cx, cy = hi_size // 2, hi_size // 2
        r = int(w * 0.45)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLOR_ACCENT_MINT)
        # Spunta bianca
        pts = [
            (cx - int(r * 0.45), cy),
            (cx - int(r * 0.1), cy + int(r * 0.35)),
            (cx + int(r * 0.45), cy - int(r * 0.35))
        ]
        d.line(pts, fill="#ffffff", width=int(lw * 1.4), joint="curve")

    elif icon_type == "play":
        # Triangolo di avvio
        cx, cy = hi_size // 2, hi_size // 2
        s = int(w * 0.35)
        pts = [(cx - int(s * 0.7), cy - s), (cx + s, cy), (cx - int(s * 0.7), cy + s)]
        d.polygon(pts, fill=color)

    # Downsampling di alta qualità per perfetto anti-aliasing
    return im.resize((size, size), Image.Resampling.LANCZOS)

def create_capsule_cover(title, subtitle, runtime_tag, theme_gradient, width=200, height=290, is_verified=True):
    """
    Genera un'immagine artistica per la card di gioco/software in aspect ratio 2:3,
    con illuminazione volumetrica, gradiente elegante, grafica astratta e badge tecnici.
    """
    scale = 2
    w, h = width * scale, height * scale
    im = Image.new("RGBA", (w, h), COLOR_BG_CARD)
    d = ImageDraw.Draw(im)

    # Gradiente di sfondo personalizzato per il tema
    c_start, c_end = theme_gradient
    for y in range(h):
        factor = y / float(h)
        # Interpolazione RGB
        r = int(c_start[0] * (1 - factor) + c_end[0] * factor)
        g = int(c_start[1] * (1 - factor) + c_end[1] * factor)
        b = int(c_start[2] * (1 - factor) + c_end[2] * factor)
        d.line([(0, y), (w, y)], fill=(r, g, b, 255))

    # Grafica geometrica astratta di profondità
    d.polygon([(0, int(h * 0.6)), (w, int(h * 0.2)), (w, int(h * 0.65)), (0, int(h * 0.95))], fill=(0, 0, 0, 45))
    d.polygon([(0, 0), (w, int(h * 0.4)), (0, int(h * 0.45))], fill=(255, 255, 255, 15))

    # Sfumatura scura verso la parte inferiore per leggibilità testo
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_ov = ImageDraw.Draw(overlay)
    dark_start = int(h * 0.40)
    for y in range(dark_start, h):
        factor = (y - dark_start) / float(h - dark_start)
        alpha = int(250 * (factor ** 1.1))
        d_ov.line([(0, y), (w, y)], fill=(12, 16, 24, min(255, alpha)))
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im)

    # Top Tag: Runtime Badge Pill (es. "PROTON-GE", "WAYDROID", "UEM-N64")
    pill_w = int(len(runtime_tag) * 9.5 * scale) + int(18 * scale)
    pill_h = int(24 * scale)
    pill_x = int(12 * scale)
    pill_y = int(12 * scale)
    draw_rounded_rect(d, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=int(6 * scale), fill=(12, 18, 30, 230), outline=(56, 189, 248, 180), width=scale)

    try:
        font_tag = ImageFont.truetype("/System/Library/Fonts/SFCompact.ttf", int(11 * scale))
    except Exception:
        font_tag = ImageFont.load_default()
    d.text((pill_x + int(9 * scale), pill_y + int(4 * scale)), runtime_tag.upper(), fill=COLOR_ACCENT_CYAN, font=font_tag)

    # Verified Badge in alto a destra
    if is_verified:
        v_size = int(20 * scale)
        v_x = w - int(12 * scale) - v_size
        v_y = int(12 * scale)
        v_ico = create_vector_icon("verified", size=v_size, scale=2)
        im.paste(v_ico, (v_x, v_y), v_ico)

    # Titolo dell'applicazione / gioco (Tipografia decisa in stile SteamOS AAA)
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/SFProText-Bold.otf", int(17 * scale))
        font_sub = ImageFont.truetype("/System/Library/Fonts/SFProText-Medium.otf", int(11 * scale))
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    text_y = h - int(64 * scale)
    # Glow / shadow sottile per il testo del titolo
    d.text((int(14 * scale) + 1, text_y + 1), title, fill=(0, 0, 0, 220), font=font_title)
    d.text((int(14 * scale), text_y), title, fill="#ffffff", font=font_title)

    d.text((int(14 * scale), text_y + int(24 * scale)), subtitle, fill=COLOR_TEXT_MUTED, font=font_sub)

    # Bordo esterno sottile 1px perimetrale
    draw_rounded_rect(d, (0, 0, w - 1, h - 1), radius=int(10 * scale), outline=(34, 45, 61, 255), width=scale)

    # Ridimensionamento ad alta qualità
    return im.resize((width, height), Image.Resampling.LANCZOS)
