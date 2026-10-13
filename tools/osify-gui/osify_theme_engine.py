#!/usr/bin/env python3
# ==============================================================================
# OSify Theme Engine & Appearance Architecture — Personalizzazione Totale
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Sistema di personalizzazione ad alta fedeltà visiva:
# 1. 5 Temi Completi: Obsidian Dark, OLED Midnight, Nordic Frost, Cyber Neon, Studio Light
# 2. 3 Stili Pulsanti Titolo: macOS Traffic Lights, Windows 11 Fluent, KDE Plasma 6 Breeze
# 3. Raggio di Curvatura Finestre regolabile (0px, 8px, 14px)
# 4. Dimensione e Stile Cursore Mouse / Touch (24px, 32px, 48px)
# 5. Window Snapping, Animazioni Micro-Transizione e Modalità Touchscreen
# 6. Salvataggio e Hot-Reload istantaneo in ~/.config/osify/appearance.json
# ==============================================================================

import os
import sys
import json
from PIL import Image, ImageDraw, ImageTk

CONFIG_DIR = os.path.expanduser("~/.config/osify")
CONFIG_FILE = os.path.join(CONFIG_DIR, "appearance.json")

# ==============================================================================
# CATALOGO TEMI UFFICIALI (PALETTE AD ALTA DENSITÀ ED ELEGANZA VISIVA)
# ==============================================================================
THEMES = {
    "obsidian_dark": {
        "name": "Obsidian Dark (Predefinito)",
        "desc": "Palette dark slate con accenti sky cyan e profonda pulizia geometrica",
        "bg_base": "#070a10",
        "bg_panel": "#0e1422",
        "bg_surface": "#121a2c",
        "bg_card": "#182238",
        "bg_card_hover": "#22304e",
        "titlebar_active": "#162035",
        "titlebar_inactive": "#0c121e",
        "border_active": "#38bdf8",
        "border_inactive": "#1e293b",
        "border_subtle": "#162032",
        "text_primary": "#f8fafc",
        "text_muted": "#94a3b8",
        "accent_primary": "#0284c7",
        "accent_cyan": "#38bdf8",
        "accent_mint": "#10b981",
        "btn_close_hover": "#ef4444",
        "shadow_color": "#000000"
    },
    "oled_black": {
        "name": "OLED Midnight (True Black)",
        "desc": "Zero consumo per pannelli OLED e Steam Deck OLED con contrasto perfetto",
        "bg_base": "#000000",
        "bg_panel": "#050608",
        "bg_surface": "#0a0c10",
        "bg_card": "#101318",
        "bg_card_hover": "#1a1f28",
        "titlebar_active": "#0f1218",
        "titlebar_inactive": "#040507",
        "border_active": "#0ea5e9",
        "border_inactive": "#181d26",
        "border_subtle": "#10141b",
        "text_primary": "#ffffff",
        "text_muted": "#8593a6",
        "accent_primary": "#0284c7",
        "accent_cyan": "#38bdf8",
        "accent_mint": "#10b981",
        "btn_close_hover": "#ef4444",
        "shadow_color": "#000000"
    },
    "nordic_frost": {
        "name": "Nordic Frost (Ice Slate)",
        "desc": "Armonia scandinava in toni ardesia polare e ciano glaciale",
        "bg_base": "#0d131f",
        "bg_panel": "#141c2c",
        "bg_surface": "#1c273c",
        "bg_card": "#24324d",
        "bg_card_hover": "#2e3f60",
        "titlebar_active": "#223048",
        "titlebar_inactive": "#121a28",
        "border_active": "#67e8f9",
        "border_inactive": "#2d3d58",
        "border_subtle": "#1e293b",
        "text_primary": "#f1f5f9",
        "text_muted": "#94a3b8",
        "accent_primary": "#0891b2",
        "accent_cyan": "#67e8f9",
        "accent_mint": "#2dd4bf",
        "btn_close_hover": "#f43f5e",
        "shadow_color": "#030712"
    },
    "cyber_neon": {
        "name": "Cyber Neon (Alchemic Violet)",
        "desc": "Viola profondo sintetico con linee neon e personalità audace",
        "bg_base": "#0a0614",
        "bg_panel": "#120c22",
        "bg_surface": "#1a1232",
        "bg_card": "#251a46",
        "bg_card_hover": "#332460",
        "titlebar_active": "#241844",
        "titlebar_inactive": "#100920",
        "border_active": "#c084fc",
        "border_inactive": "#3b2268",
        "border_subtle": "#22133e",
        "text_primary": "#faf5ff",
        "text_muted": "#c084fc",
        "accent_primary": "#9333ea",
        "accent_cyan": "#38bdf8",
        "accent_mint": "#34d399",
        "btn_close_hover": "#f43f5e",
        "shadow_color": "#050010"
    },
    "studio_light": {
        "name": "Studio Light (Pro High-Contrast)",
        "desc": "Modalità chiara pulita, ideale per ambienti luminosi e produttività da ufficio",
        "bg_base": "#f1f5f9",
        "bg_panel": "#e2e8f0",
        "bg_surface": "#ffffff",
        "bg_card": "#f8fafc",
        "bg_card_hover": "#e2e8f0",
        "titlebar_active": "#e2e8f0",
        "titlebar_inactive": "#f1f5f9",
        "border_active": "#0284c7",
        "border_inactive": "#cbd5e1",
        "border_subtle": "#e2e8f0",
        "text_primary": "#0f172a",
        "text_muted": "#64748b",
        "accent_primary": "#0284c7",
        "accent_cyan": "#0284c7",
        "accent_mint": "#059669",
        "btn_close_hover": "#dc2626",
        "shadow_color": "#94a3b8"
    }
}

DEFAULT_CONFIG = {
    "theme_id": "obsidian_dark",
    "window_buttons_style": "macos_traffic_lights",  # macos_traffic_lights, fluent_linear, breeze_circular
    "corner_radius": 10,                            # 0, 8, 10, 14
    "cursor_size": 28,                              # 24, 28, 36, 48
    "cursor_theme": "cyan_glow",                    # cyan_glow, obsidian_black, crystal_white
    "ui_scale": 1.0,                                # 1.0, 1.25, 1.5
    "window_snapping": True,
    "animations_enabled": True,
    "animation_speed_ms": 180,
    "touch_mode": False                             # True allarga i pulsanti a 44px
}

class OSifyThemeEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OSifyThemeEngine, cls).__new__(cls)
            cls._instance.button_cache = {}
            cls._instance.config = cls._instance.load_config()
            cls._instance.current_theme = THEMES.get(cls._instance.config["theme_id"], THEMES["obsidian_dark"])
        return cls._instance

    def load_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return cfg
            except Exception:
                pass
        self.save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    def save_config(self, cfg=None):
        if cfg is None:
            cfg = self.config
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        self.config = cfg
        self.current_theme = THEMES.get(cfg.get("theme_id", "obsidian_dark"), THEMES["obsidian_dark"])
        self.button_cache.clear()

    @property
    def theme_id(self):
        return self.config.get("theme_id", "obsidian_dark")

    @property
    def button_style(self):
        return self.config.get("window_buttons_style", "macos_traffic_lights")

    @button_style.setter
    def button_style(self, val):
        self.set_window_buttons_style(val)

    @property
    def corner_radius(self):
        return self.config.get("corner_radius", 10)

    @corner_radius.setter
    def corner_radius(self, val):
        self.set_corner_radius(val)

    @property
    def cursor_size(self):
        return self.config.get("cursor_size", 28)

    @cursor_size.setter
    def cursor_size(self, val):
        self.set_cursor_size(val)

    def get_color(self, token_name):
        return self.current_theme.get(token_name, "#ffffff")

    def set_theme(self, theme_id):
        if theme_id in THEMES:
            self.config["theme_id"] = theme_id
            self.save_config()
            return True
        return False

    def set_window_buttons_style(self, style_name):
        if style_name in ("macos_traffic_lights", "fluent_linear", "breeze_circular"):
            self.config["window_buttons_style"] = style_name
            self.save_config()
            return True
        return False

    def set_corner_radius(self, radius):
        self.config["corner_radius"] = int(radius)
        self.save_config()

    def set_cursor_size(self, size):
        self.config["cursor_size"] = int(size)
        self.save_config()

    def set_touch_mode(self, enabled):
        self.config["touch_mode"] = bool(enabled)
        self.save_config()

    # =========================================================================
    # GENERATORE VETTORIALE PULSANTI TITOLO FINESTRA (Zero Slop Unicode)
    # =========================================================================
    def render_titlebar_button(self, btn_type, state="normal", size=14, scale=3):
        """
        Renderizza il pulsante del titolo finestra ad altissima definizione.
        btn_type: 'close', 'minimize', 'maximize', 'restore'
        state: 'normal', 'hover', 'active'
        """
        cache_key = (self.config["window_buttons_style"], btn_type, state, size, self.config["theme_id"])
        if cache_key in self.button_cache:
            return self.button_cache[cache_key]

        style = self.config.get("window_buttons_style", "macos_traffic_lights")
        hi = size * scale
        im = Image.new("RGBA", (hi, hi), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        if style == "macos_traffic_lights":
            # Perline cerchiate levigate stile macOS
            radius = hi // 2 - scale
            cx, cy = hi // 2, hi // 2

            if btn_type == "close":
                fill_color = (255, 95, 86) if state == "normal" else (235, 75, 66)
                border_color = (224, 68, 62)
            elif btn_type == "minimize":
                fill_color = (255, 189, 46) if state == "normal" else (235, 169, 26)
                border_color = (222, 161, 35)
            else: # maximize / restore
                fill_color = (39, 201, 63) if state == "normal" else (19, 181, 43)
                border_color = (26, 171, 41)

            # Sfera principale con anti-aliasing
            d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=fill_color, outline=border_color, width=max(1, scale))

            # Al passaggio del mouse disegna micro-glifo scuro elegante all'interno
            if state in ("hover", "active"):
                glyph_c = (70, 20, 20, 200) if btn_type == "close" else (90, 60, 10, 200) if btn_type == "minimize" else (10, 70, 20, 200)
                gw = radius // 2
                lw = max(2, int(scale * 1.2))
                if btn_type == "close":
                    d.line([(cx - gw, cy - gw), (cx + gw, cy + gw)], fill=glyph_c, width=lw)
                    d.line([(cx + gw, cy - gw), (cx - gw, cy + gw)], fill=glyph_c, width=lw)
                elif btn_type == "minimize":
                    d.line([(cx - gw, cy), (cx + gw, cy)], fill=glyph_c, width=lw)
                else:
                    # Due triangolini o un +
                    d.line([(cx - gw, cy), (cx + gw, cy)], fill=glyph_c, width=lw)
                    d.line([(cx, cy - gw), (cx, cy + gw)], fill=glyph_c, width=lw)

        elif style == "breeze_circular":
            # Cerchietti incassati minimali KDE Plasma 6
            radius = hi // 2 - scale
            cx, cy = hi // 2, hi // 2
            bg_c = (35, 45, 65, 180) if state == "normal" else (50, 70, 100, 230)
            stroke_c = (239, 68, 68) if btn_type == "close" and state != "normal" else (180, 200, 230)
            d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=bg_c, outline=(60, 80, 110), width=1)
            gw = radius // 2
            lw = max(1, scale)
            if btn_type == "close":
                d.line([(cx - gw, cy - gw), (cx + gw, cy + gw)], fill=stroke_c, width=lw)
                d.line([(cx + gw, cy - gw), (cx - gw, cy + gw)], fill=stroke_c, width=lw)
            elif btn_type == "minimize":
                d.line([(cx - gw, cy + gw // 2), (cx + gw, cy + gw // 2)], fill=stroke_c, width=lw)
            else:
                d.rectangle([cx - gw, cy - gw, cx + gw, cy + gw], outline=stroke_c, width=lw)

        else: # fluent_linear (Windows 11)
            # Rettangolo discreto con glifi geometrici lineari
            cx, cy = hi // 2, hi // 2
            gw = int(hi * 0.35)
            lw = max(1, scale)
            stroke_c = (240, 245, 255)
            if btn_type == "close":
                if state in ("hover", "active"):
                    d.rectangle([0, 0, hi, hi], fill=(232, 17, 35))
                d.line([(cx - gw, cy - gw), (cx + gw, cy + gw)], fill=stroke_c, width=lw)
                d.line([(cx + gw, cy - gw), (cx - gw, cy + gw)], fill=stroke_c, width=lw)
            elif btn_type == "minimize":
                if state in ("hover", "active"):
                    d.rectangle([0, 0, hi, hi], fill=(40, 50, 75))
                d.line([(cx - gw, cy), (cx + gw, cy)], fill=stroke_c, width=lw)
            else:
                if state in ("hover", "active"):
                    d.rectangle([0, 0, hi, hi], fill=(40, 50, 75))
                d.rectangle([cx - gw, cy - gw, cx + gw, cy + gw], outline=stroke_c, width=lw)

        # Ridimensiona con Lanczos per un'antialiasing perfetto
        res = im.resize((size, size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(res)
        self.button_cache[cache_key] = photo
        return photo

# CLI Entrypoint
if __name__ == "__main__":
    engine = OSifyThemeEngine()
    args = sys.argv[1:]
    if not args:
        print("Tema attivo:", engine.config["theme_id"])
        print("Temi disponibili:", ", ".join(THEMES.keys()))
        sys.exit(0)

    cmd = args[0]
    if cmd == "list":
        for k, v in THEMES.items():
            print(f"• {k:<16} : {v['name']} — {v['desc']}")
    elif cmd in ("set", "apply") and len(args) > 1:
        tid = args[1]
        if engine.set_theme(tid):
            print(f"[✓] Tema impostato a: {tid}")
        else:
            print(f"[!] Tema '{tid}' non valido. Usa: {', '.join(THEMES.keys())}")
    elif cmd == "style" and len(args) > 1:
        st = args[1]
        if engine.set_window_buttons_style(st):
            print(f"[✓] Stile pulsanti impostato a: {st}")
        else:
            print(f"[!] Stile non valido. Usa: macos_traffic_lights, fluent_linear, breeze_circular")
    elif cmd == "status":
        print(json.dumps(engine.config, indent=2))
    else:
        print("Uso: osify_theme_engine.py {list|set <theme_id>|style <style_name>|status}")
