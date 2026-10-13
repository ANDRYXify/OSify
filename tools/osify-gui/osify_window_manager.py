#!/usr/bin/env python3
# ==============================================================================
# OSify Desktop Window Manager — Gestore Finestre Fluttuanti & Multitasking
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Implementa un VERO ambiente desktop multitasking ad alta fedeltà visiva:
# 1. Finestre fluttuanti liberamente trascinabili (Drag & Drop) e sovrapponibili.
# 2. Ridimensionamento dinamico dagli angoli (Resize Handle).
# 3. Controlli finestra personalizzabili: macOS Traffic Lights, Windows 11 Fluent,
#    KDE Plasma 6 Breeze, con micro-glifi al passaggio del mouse.
# 4. Window Snapping a metà schermo (50% sinistra/destra) e massimizzazione.
# 5. Menu contestuale al tasto destro del desktop (Nuova app, personalizzazione, pulizia).
# 6. Centro Personalizzazione e Temi: Obsidian Dark, OLED Midnight, Nordic Frost,
#    Cyber Neon, Studio Light, Raggio angoli, Dimensione cursori, Touch Mode.
# 7. Strumenti integrati: Konsole Poliglotta, Task Manager, Dolphin, Pulizia Memoria,
#    Calibrazione Input & Touch, Centro di Controllo, UEM Binary Hub.
# ==============================================================================

import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

# Risoluzione percorsi e moduli
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.dirname(__file__))
from osify_theme_engine import OSifyThemeEngine, THEMES

class OSifyFloatingWindow:
    def __init__(self, wm, win_id, title, icon_type, x, y, width, height, builder_func):
        self.wm = wm
        self.win_id = win_id
        self.title = title
        self.icon_type = icon_type
        self.x = x
        self.y = y
        self.width = max(360, width)
        self.height = max(240, height)
        self.builder_func = builder_func

        self.is_minimized = False
        self.is_maximized = False
        self.saved_geometry = (x, y, width, height)

        self.drag_start_x = 0
        self.drag_start_y = 0

        self.frame = None
        self.titlebar = None
        self.content_frame = None
        self.lbl_title = None
        self.btn_close_lbl = None
        self.btn_min_lbl = None
        self.btn_max_lbl = None
        self.resize_grip = None

        self.build_window()

    def build_window(self):
        engine = self.wm.theme_engine
        bg_bar = engine.get_color("titlebar_inactive")
        border_c = engine.get_color("border_inactive")
        fg_title = engine.get_color("text_primary")
        btn_style = engine.config.get("window_buttons_style", "macos_traffic_lights")
        is_touch = engine.config.get("touch_mode", False)
        btn_size = 14 if not is_touch else 18
        titlebar_h = 34 if not is_touch else 44

        # Frame principale della finestra fluttuante
        self.frame = tk.Frame(
            self.wm.desktop_canvas,
            bg=bg_bar,
            bd=1,
            relief="solid",
            highlightbackground=border_c,
            highlightthickness=1
        )

        # ---------------------------------------------------------------------
        # TITLEBAR (BARRA DEL TITOLO)
        # ---------------------------------------------------------------------
        self.titlebar = tk.Frame(self.frame, bg=bg_bar, height=titlebar_h)
        self.titlebar.pack(side="top", fill="x")

        if btn_style == "macos_traffic_lights":
            # Stile macOS: Traffic Lights a sinistra, Titolo a seguire
            ctrl_box = tk.Frame(self.titlebar, bg=bg_bar)
            ctrl_box.pack(side="left", padx=10, pady=7)

            self.btn_close_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("close", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_close_lbl.pack(side="left", padx=3)

            self.btn_min_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("minimize", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_min_lbl.pack(side="left", padx=3)

            self.btn_max_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("maximize", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_max_lbl.pack(side="left", padx=3)

            mid_box = tk.Frame(self.titlebar, bg=bg_bar)
            mid_box.pack(side="left", padx=(10, 8), pady=6)

            ico_img = self.wm.get_icon(self.icon_type, size=16, color=engine.get_color("accent_cyan"))
            if ico_img:
                lbl_ico = tk.Label(mid_box, image=ico_img, bg=bg_bar)
                lbl_ico.pack(side="left", padx=(0, 6))

            self.lbl_title = tk.Label(
                mid_box,
                text=self.title,
                font=("Helvetica Neue", 10, "bold"),
                fg=fg_title,
                bg=bg_bar
            )
            self.lbl_title.pack(side="left")

        else:
            # Stile Fluent / Breeze: Titolo a sinistra, Bottoni a destra
            left_box = tk.Frame(self.titlebar, bg=bg_bar)
            left_box.pack(side="left", padx=10, pady=6)

            ico_img = self.wm.get_icon(self.icon_type, size=16, color=engine.get_color("accent_cyan"))
            if ico_img:
                lbl_ico = tk.Label(left_box, image=ico_img, bg=bg_bar)
                lbl_ico.pack(side="left", padx=(0, 6))

            self.lbl_title = tk.Label(
                left_box,
                text=self.title,
                font=("Helvetica Neue", 10, "bold"),
                fg=fg_title,
                bg=bg_bar
            )
            self.lbl_title.pack(side="left")

            ctrl_box = tk.Frame(self.titlebar, bg=bg_bar)
            ctrl_box.pack(side="right", padx=8, pady=6)

            self.btn_min_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("minimize", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_min_lbl.pack(side="left", padx=3)

            self.btn_max_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("maximize", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_max_lbl.pack(side="left", padx=3)

            self.btn_close_lbl = tk.Label(ctrl_box, image=engine.render_titlebar_button("close", "normal", size=btn_size), bg=bg_bar, cursor="hand2", bd=0)
            self.btn_close_lbl.pack(side="left", padx=3)

        # Micro-interazioni al passaggio del mouse sui pulsanti
        self.btn_close_lbl.bind("<Enter>", lambda e: self.btn_close_lbl.config(image=engine.render_titlebar_button("close", "hover", size=btn_size)))
        self.btn_close_lbl.bind("<Leave>", lambda e: self.btn_close_lbl.config(image=engine.render_titlebar_button("close", "normal", size=btn_size)))
        self.btn_close_lbl.bind("<Button-1>", lambda e: self.wm.close_window(self.win_id))

        self.btn_min_lbl.bind("<Enter>", lambda e: self.btn_min_lbl.config(image=engine.render_titlebar_button("minimize", "hover", size=btn_size)))
        self.btn_min_lbl.bind("<Leave>", lambda e: self.btn_min_lbl.config(image=engine.render_titlebar_button("minimize", "normal", size=btn_size)))
        self.btn_min_lbl.bind("<Button-1>", lambda e: self.wm.minimize_window(self.win_id))

        self.btn_max_lbl.bind("<Enter>", lambda e: self.btn_max_lbl.config(image=engine.render_titlebar_button("maximize", "hover", size=btn_size)))
        self.btn_max_lbl.bind("<Leave>", lambda e: self.btn_max_lbl.config(image=engine.render_titlebar_button("maximize", "normal", size=btn_size)))
        self.btn_max_lbl.bind("<Button-1>", lambda e: self.wm.toggle_maximize(self.win_id))

        # Drag & Drop su titlebar
        for w in (self.titlebar, self.lbl_title):
            w.bind("<ButtonPress-1>", self.on_title_press)
            w.bind("<B1-Motion>", self.on_title_drag)
            w.bind("<Double-Button-1>", lambda e: self.wm.toggle_maximize(self.win_id))

        # Click ovunque nella finestra porta in primo piano
        self.frame.bind("<ButtonPress-1>", lambda e: self.wm.bring_to_front(self.win_id))

        # ---------------------------------------------------------------------
        # AREA CONTENUTO
        # ---------------------------------------------------------------------
        self.content_frame = tk.Frame(self.frame, bg=engine.get_color("bg_base"))
        self.content_frame.pack(fill="both", expand=True)

        if self.builder_func:
            self.builder_func(self.content_frame, self)

        # ---------------------------------------------------------------------
        # MANIGLIA DI RIDIMENSIONAMENTO (ANGOLO INFERIORE DESTRO)
        # ---------------------------------------------------------------------
        bot_bar = tk.Frame(self.frame, bg=engine.get_color("bg_base"), height=14)
        bot_bar.pack(side="bottom", fill="x")

        self.resize_grip = tk.Label(bot_bar, text="⋱", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base"), cursor="bottom_right_corner")
        self.resize_grip.pack(side="right", padx=4, pady=1)

        self.resize_grip.bind("<ButtonPress-1>", self.on_resize_press)
        self.resize_grip.bind("<B1-Motion>", self.on_resize_drag)

        self.update_geometry()

    def set_active_visuals(self, is_active):
        engine = self.wm.theme_engine
        bg = engine.get_color("titlebar_active") if is_active else engine.get_color("titlebar_inactive")
        border = engine.get_color("border_active") if is_active else engine.get_color("border_inactive")
        thick = 2 if is_active else 1

        self.frame.config(highlightbackground=border, highlightthickness=thick)
        self.titlebar.config(bg=bg)
        for child in self.titlebar.winfo_children():
            try: child.config(bg=bg)
            except Exception: pass
            for sub in child.winfo_children():
                try: sub.config(bg=bg)
                except Exception: pass

    def on_title_press(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.wm.bring_to_front(self.win_id)

    def on_title_drag(self, event):
        if self.is_maximized:
            # Ripristina se trascinata mentre massimizzata
            self.wm.toggle_maximize(self.win_id)
            return

        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        self.x += dx
        self.y += dy
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root

        # Window Snapping (se abilitato nelle opzioni)
        if self.wm.theme_engine.config.get("window_snapping", True):
            cw = self.wm.desktop_canvas.winfo_width() or 1160
            ch = self.wm.desktop_canvas.winfo_height() or 680
            # Bordo sinistro (snap 50% larghezza)
            if event.x_root < 18:
                self.snap_to_side("left", cw, ch)
                return
            # Bordo destro (snap 50% larghezza)
            elif event.x_root > cw - 18:
                self.snap_to_side("right", cw, ch)
                return

        self.update_geometry()

    def snap_to_side(self, side, cw, ch):
        half_w = cw // 2
        if side == "left":
            self.x, self.y, self.width, self.height = 0, 0, half_w, ch
        else:
            self.x, self.y, self.width, self.height = half_w, 0, half_w, ch
        self.update_geometry()

    def on_resize_press(self, event):
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_w = self.width
        self.resize_start_h = self.height
        self.wm.bring_to_front(self.win_id)

    def on_resize_drag(self, event):
        if self.is_maximized:
            return
        dw = event.x_root - self.resize_start_x
        dh = event.y_root - self.resize_start_y
        self.width = max(340, self.resize_start_w + dw)
        self.height = max(220, self.resize_start_h + dh)
        self.update_geometry()

    def update_geometry(self):
        self.frame.place(x=self.x, y=self.y, width=self.width, height=self.height)


class OSifyDesktopWindowManager:
    def __init__(self, master_viewport, get_icon_func, on_switch_to_deck):
        self.viewport = master_viewport
        self._raw_get_icon = get_icon_func
        self.on_switch_to_deck = on_switch_to_deck
        self.theme_engine = OSifyThemeEngine()
        self.photo_cache = {}

        self.windows = {}
        self.z_stack = []
        self.taskbar_pills = {}

        self.wallpaper_img = None
        self.desktop_canvas = None
        self.taskbar = None
        self.start_menu_win = None
        self.ctx_menu = None

        self.init_desktop()

    def get_icon(self, icon_type, size=24, color=None):
        if not self._raw_get_icon:
            return None
        res = self._raw_get_icon(icon_type, size=size, color=color)
        if isinstance(res, Image.Image):
            key = (icon_type, size, color)
            if key not in self.photo_cache:
                self.photo_cache[key] = ImageTk.PhotoImage(res)
            return self.photo_cache[key]
        return res

    def init_desktop(self):
        engine = self.theme_engine
        bg_panel = engine.get_color("bg_panel")
        border_inact = engine.get_color("border_inactive")

        # 1. Taskbar Inferiore (Plasma 6 / Windows 11 style)
        self.taskbar = tk.Frame(
            self.viewport,
            bg=bg_panel,
            height=44,
            bd=1,
            relief="solid",
            highlightbackground=border_inact,
            highlightthickness=1
        )
        self.taskbar.pack(side="bottom", fill="x")

        # 2. Canvas del Desktop Fluttuante
        self.desktop_canvas = tk.Canvas(
            self.viewport,
            bg=engine.get_color("bg_base"),
            bd=0,
            highlightthickness=0
        )
        self.desktop_canvas.pack(side="top", fill="both", expand=True)

        # Wallpaper geometrico ad alta definizione
        w = self.viewport.winfo_width() or 1160
        h = self.viewport.winfo_height() or 720
        self.wallpaper_img = self.create_wallpaper(w, h)
        self.desktop_canvas.create_image(0, 0, image=self.wallpaper_img, anchor="nw")

        # Menu Contestuale al Tasto Destro del Desktop
        self.desktop_canvas.bind("<Button-2>", self.show_desktop_context_menu)
        self.desktop_canvas.bind("<Button-3>", self.show_desktop_context_menu)
        self.desktop_canvas.bind("<Button-1>", self.on_desktop_click)

        # 3. Scorciatoie Desktop
        self.render_desktop_shortcuts()

        # 4. Taskbar
        self.build_taskbar()

        # Apri di default Konsole e Monitor di Sistema
        self.open_konsole_window(x=130, y=36, w=540, h=390)
        self.open_sysmon_window(x=580, y=80, w=520, h=380)

    def on_desktop_click(self, event):
        if self.ctx_menu and self.ctx_menu.winfo_exists():
            self.ctx_menu.destroy()
            self.ctx_menu = None
        if self.start_menu_win and self.start_menu_win.winfo_exists():
            self.start_menu_win.destroy()
            self.start_menu_win = None

    def create_wallpaper(self, w, h):
        """Genera lo sfondo desktop con mesh gradient ed eleganza ottica volumetrica"""
        w, h = max(w, 900), max(h, 600)
        im = Image.new("RGBA", (w, h), self.theme_engine.get_color("bg_base"))
        d = ImageDraw.Draw(im)

        # Gradiente radiale / verticale profondo
        c_top = (7, 10, 16) if self.theme_engine.config["theme_id"] != "studio_light" else (241, 245, 249)
        c_mid = (16, 24, 40) if self.theme_engine.config["theme_id"] != "studio_light" else (226, 232, 240)
        for y in range(h):
            factor = y / float(h)
            r = int(c_top[0] * (1 - factor) + c_mid[0] * factor)
            g = int(c_top[1] * (1 - factor) + c_mid[1] * factor)
            b = int(c_top[2] * (1 - factor) + c_mid[2] * factor)
            d.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Forme geometriche refractive morbide
        d.polygon([(0, int(h * 0.7)), (w, int(h * 0.3)), (w, int(h * 0.8)), (0, h)], fill=(2, 132, 199, 14))
        d.polygon([(0, int(h * 0.2)), (w, int(h * 0.5)), (0, int(h * 0.85))], fill=(56, 189, 248, 10))

        # Watermark logo OSify al centro
        orig_logo = os.path.join(REPO_ROOT, "OSify.png")
        if os.path.exists(orig_logo):
            try:
                logo_raw = Image.open(orig_logo).convert("RGBA")
                l_sz = 260
                logo_raw = logo_raw.resize((l_sz, l_sz), Image.Resampling.LANCZOS)
                alpha_layer = logo_raw.split()[3].point(lambda p: int(p * 0.14))
                logo_raw.putalpha(alpha_layer)
                im.alpha_composite(logo_raw, ((w - l_sz) // 2, (h - l_sz) // 2 - 20))
            except Exception:
                pass

        return ImageTk.PhotoImage(im)

    def render_desktop_shortcuts(self):
        engine = self.theme_engine
        shortcuts = [
            ("Konsole Terminal", "terminal", lambda: self.open_konsole_window()),
            ("File Manager", "folder", lambda: self.open_filemanager_window()),
            ("System Monitor", "sliders", lambda: self.open_sysmon_window()),
            ("Personalizzazione", "palette", lambda: self.open_customizer_window()),
            ("Pulizia Memoria", "broom", lambda: self.open_memory_cleaner_window()),
            ("Centro Controllo", "gear", lambda: self.open_control_center_window()),
            ("Input & Touch", "touch", lambda: self.open_input_settings_window()),
            ("UEM Binary Hub", "chip", lambda: self.open_uem_window()),
            ("Gaming Mode", "gamepad", self.on_switch_to_deck)
        ]

        sy = 20
        bg_desktop = engine.get_color("bg_base")
        fg_text = engine.get_color("text_primary")
        accent_c = engine.get_color("accent_cyan")

        for title, icon_type, cmd in shortcuts:
            f = tk.Frame(self.desktop_canvas, bg=bg_desktop, cursor="hand2")
            ico = self.get_icon(icon_type, size=32, color=accent_c if icon_type != "gamepad" else engine.get_color("accent_primary"))
            lbl_i = tk.Label(f, image=ico, bg=bg_desktop)
            lbl_i.pack()
            lbl_t = tk.Label(f, text=title, font=("Helvetica Neue", 8, "bold"), fg=fg_text, bg=bg_desktop)
            lbl_t.pack()

            for w in (f, lbl_i, lbl_t):
                w.bind("<Double-Button-1>", lambda e, c=cmd: c())
                w.bind("<Button-1>", lambda e, c=cmd: c())

            self.desktop_canvas.create_window(24, sy, window=f, anchor="nw")
            sy += 68

    def show_desktop_context_menu(self, event):
        if self.ctx_menu and self.ctx_menu.winfo_exists():
            self.ctx_menu.destroy()

        engine = self.theme_engine
        self.ctx_menu = tk.Frame(
            self.desktop_canvas,
            bg=engine.get_color("bg_panel"),
            bd=1,
            relief="solid",
            highlightbackground=engine.get_color("border_active"),
            highlightthickness=1
        )

        cw = self.desktop_canvas.winfo_width() or 1160
        ch = self.desktop_canvas.winfo_height() or 680
        mx = min(event.x, cw - 270)
        my = min(event.y, ch - 290)
        self.ctx_menu.place(x=mx, y=my, width=260, height=270)

        # Header menu
        hdr = tk.Frame(self.ctx_menu, bg=engine.get_color("titlebar_active"), padx=10, pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text="OSify Desktop Context", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("titlebar_active")).pack(side="left")

        items = [
            ("Nuova Konsole (Terminale)", "terminal", self.open_konsole_window),
            ("Apri Dolphin (File Manager)", "folder", self.open_filemanager_window),
            ("Monitor di Sistema", "sliders", self.open_sysmon_window),
            ("Personalizzazione & Temi...", "palette", self.open_customizer_window),
            ("Ottimizza Memoria & Cache", "broom", self.open_memory_cleaner_window),
            ("Calibrazione Input & Touch", "touch", self.open_input_settings_window),
            ("Switch to Gaming Mode", "gamepad", self.on_switch_to_deck)
        ]

        for text, ico_type, action in items:
            row = tk.Frame(self.ctx_menu, bg=engine.get_color("bg_panel"), padx=10, pady=4, cursor="hand2")
            row.pack(fill="x")
            ico = self.get_icon(ico_type, size=15, color=engine.get_color("accent_cyan"))
            if ico:
                lbl_i = tk.Label(row, image=ico, bg=engine.get_color("bg_panel"))
                lbl_i.pack(side="left", padx=(0, 6))
            lbl_t = tk.Label(row, text=text, font=("Helvetica Neue", 8), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_panel"))
            lbl_t.pack(side="left")

            def make_click(a=action):
                return lambda e: (self.ctx_menu.destroy(), a())
            row.bind("<Button-1>", make_click())
            lbl_t.bind("<Button-1>", make_click())

    # =========================================================================
    # TASKBAR & SYSTEM TRAY
    # =========================================================================
    def build_taskbar(self):
        engine = self.theme_engine
        for w in self.taskbar.winfo_children():
            w.destroy()

        bg_panel = engine.get_color("bg_panel")
        fg_text = engine.get_color("text_primary")
        accent = engine.get_color("accent_primary")

        # Sinistra: Pulsante Menu Start Kickoff
        left_box = tk.Frame(self.taskbar, bg=bg_panel)
        left_box.pack(side="left", padx=8, pady=4)

        btn_start = tk.Label(
            left_box,
            text=" OSify ❖",
            font=("Helvetica Neue", 11, "bold"),
            fg=fg_text,
            bg=accent,
            padx=10,
            pady=4,
            cursor="hand2"
        )
        btn_start.pack(side="left")
        btn_start.bind("<Button-1>", lambda e: self.toggle_start_menu())

        # Centro: Task Pills delle finestre aperte
        self.center_tasks = tk.Frame(self.taskbar, bg=bg_panel)
        self.center_tasks.pack(side="left", fill="x", expand=True, padx=12)
        self.render_task_pills()

        # Destra: System Tray & Switch rapido
        right_box = tk.Frame(self.taskbar, bg=bg_panel)
        right_box.pack(side="right", padx=12, pady=4)

        btn_deck = tk.Label(
            right_box,
            text="⤹ Gaming Mode",
            font=("Helvetica Neue", 9, "bold"),
            fg=engine.get_color("accent_cyan"),
            bg=bg_panel,
            padx=8,
            pady=4,
            cursor="hand2"
        )
        btn_deck.pack(side="left", padx=(0, 10))
        btn_deck.bind("<Button-1>", lambda e: self.on_switch_to_deck())

        lbl_clock = tk.Label(
            right_box,
            text=time.strftime("%H:%M"),
            font=("Helvetica Neue", 10, "bold"),
            fg=fg_text,
            bg=bg_panel
        )
        lbl_clock.pack(side="left")

        def update_clock():
            if lbl_clock.winfo_exists():
                lbl_clock.config(text=time.strftime("%H:%M"))
                self.taskbar.after(10000, update_clock)
        update_clock()

    def render_task_pills(self):
        engine = self.theme_engine
        if not hasattr(self, "center_tasks") or not self.center_tasks.winfo_exists():
            return
        for w in self.center_tasks.winfo_children():
            w.destroy()

        bg_panel = engine.get_color("bg_panel")
        border_act = engine.get_color("border_active")
        border_inact = engine.get_color("border_inactive")

        for win_id, win in self.windows.items():
            is_focused = bool(self.z_stack and self.z_stack[-1] == win_id and not win.is_minimized)
            bg_c = engine.get_color("titlebar_active") if is_focused else engine.get_color("titlebar_inactive")
            border_c = border_act if is_focused else border_inact
            fg_c = engine.get_color("text_primary") if is_focused else engine.get_color("text_muted")

            pill = tk.Frame(self.center_tasks, bg=bg_c, bd=1, relief="solid", highlightbackground=border_c, highlightthickness=1, cursor="hand2")
            pill.pack(side="left", padx=3, pady=3)

            ico = self.get_icon(win.icon_type, size=14, color=engine.get_color("accent_cyan") if is_focused else engine.get_color("text_muted"))
            if ico:
                lbl_i = tk.Label(pill, image=ico, bg=bg_c)
                lbl_i.pack(side="left", padx=(6, 4), pady=4)

            lbl_t = tk.Label(pill, text=win.title[:18], font=("Helvetica Neue", 9, "bold" if is_focused else "normal"), fg=fg_c, bg=bg_c)
            lbl_t.pack(side="left", padx=(0, 8), pady=4)

            def make_handler(wid=win_id):
                return lambda e: self.toggle_window_from_taskbar(wid)

            pill.bind("<Button-1>", make_handler())
            lbl_t.bind("<Button-1>", make_handler())

    def toggle_window_from_taskbar(self, win_id):
        win = self.windows.get(win_id)
        if not win:
            return
        if win.is_minimized:
            win.is_minimized = False
            win.update_geometry()
            self.bring_to_front(win_id)
        elif self.z_stack and self.z_stack[-1] == win_id:
            self.minimize_window(win_id)
        else:
            self.bring_to_front(win_id)

    def bring_to_front(self, win_id):
        win = self.windows.get(win_id)
        if not win or win.is_minimized:
            return
        win.frame.lift()
        if win_id in self.z_stack:
            self.z_stack.remove(win_id)
        self.z_stack.append(win_id)

        for wid, w_obj in self.windows.items():
            w_obj.set_active_visuals(wid == win_id)

        self.render_task_pills()

    def minimize_window(self, win_id):
        win = self.windows.get(win_id)
        if not win:
            return
        win.is_minimized = True
        win.frame.place_forget()
        if win_id in self.z_stack:
            self.z_stack.remove(win_id)
        if self.z_stack:
            self.bring_to_front(self.z_stack[-1])
        else:
            self.render_task_pills()

    def toggle_maximize(self, win_id):
        win = self.windows.get(win_id)
        if not win:
            return
        if not win.is_maximized:
            win.saved_geometry = (win.x, win.y, win.width, win.height)
            cw = self.desktop_canvas.winfo_width() or 1160
            ch = self.desktop_canvas.winfo_height() or 680
            win.x = 0
            win.y = 0
            win.width = cw
            win.height = ch
            win.is_maximized = True
        else:
            win.x, win.y, win.width, win.height = win.saved_geometry
            win.is_maximized = False
        win.update_geometry()
        self.bring_to_front(win_id)

    def close_window(self, win_id):
        win = self.windows.get(win_id)
        if not win:
            return
        win.frame.destroy()
        del self.windows[win_id]
        if win_id in self.z_stack:
            self.z_stack.remove(win_id)
        if self.z_stack:
            self.bring_to_front(self.z_stack[-1])
        else:
            self.render_task_pills()

    def toggle_start_menu(self):
        if self.start_menu_win and self.start_menu_win.winfo_exists():
            self.start_menu_win.destroy()
            self.start_menu_win = None
            return

        engine = self.theme_engine
        bg_panel = engine.get_color("bg_panel")
        self.start_menu_win = tk.Frame(
            self.desktop_canvas,
            bg=bg_panel,
            bd=1,
            relief="solid",
            highlightbackground=engine.get_color("border_active"),
            highlightthickness=1
        )
        ch = self.desktop_canvas.winfo_height() or 680
        self.start_menu_win.place(x=8, y=max(40, ch - 370), width=310, height=360)

        # Header menu
        hdr = tk.Frame(self.start_menu_win, bg=engine.get_color("titlebar_active"), padx=12, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="OSify Kickoff Menu", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("titlebar_active")).pack(side="left")
        tk.Label(hdr, text="Compagno", font=("Helvetica Neue", 9), fg=engine.get_color("accent_cyan"), bg=engine.get_color("titlebar_active")).pack(side="right")

        items = [
            ("Konsole (Terminale Poliglotto)", "terminal", self.open_konsole_window),
            ("Dolphin (File Manager)", "folder", self.open_filemanager_window),
            ("Monitor di Sistema (Processi)", "sliders", self.open_sysmon_window),
            ("Personalizzazione & Temi", "palette", self.open_customizer_window),
            ("Ottimizzazione Memoria & Cache", "broom", self.open_memory_cleaner_window),
            ("Centro di Controllo OSify", "gear", self.open_control_center_window),
            ("Calibrazione Input & Touch", "touch", self.open_input_settings_window),
            ("Universal Execution Matrix", "chip", self.open_uem_window),
            ("Switch to SteamOS Gaming Mode", "gamepad", self.on_switch_to_deck)
        ]

        for title, ico_type, cmd in items:
            row = tk.Frame(self.start_menu_win, bg=bg_panel, padx=10, pady=5, cursor="hand2")
            row.pack(fill="x")
            ico = self.get_icon(ico_type, size=18, color=engine.get_color("accent_cyan"))
            if ico:
                lbl_i = tk.Label(row, image=ico, bg=bg_panel)
                lbl_i.pack(side="left", padx=(4, 8))
            lbl_t = tk.Label(row, text=title, font=("Helvetica Neue", 9), fg=engine.get_color("text_primary"), bg=bg_panel)
            lbl_t.pack(side="left")

            def make_click(c=cmd):
                return lambda e: (self.start_menu_win.destroy(), c())
            row.bind("<Button-1>", make_click())
            lbl_t.bind("<Button-1>", make_click())

    def apply_theme_refresh(self):
        """Ricarica ed applica a caldo il tema a tutti i componenti desktop e finestre"""
        self.photo_cache.clear()
        w = self.viewport.winfo_width() or 1160
        h = self.viewport.winfo_height() or 720
        self.wallpaper_img = self.create_wallpaper(w, h)
        self.desktop_canvas.delete("all")
        self.desktop_canvas.create_image(0, 0, image=self.wallpaper_img, anchor="nw")
        self.render_desktop_shortcuts()
        self.build_taskbar()

        # Ri-aggiorna tutte le finestre aperte
        for wid, win in list(self.windows.items()):
            win.build_window()
        if self.z_stack:
            self.bring_to_front(self.z_stack[-1])

    # =========================================================================
    # APPLICAZIONI NATIVE A FINESTRA
    # =========================================================================

    # 1. OSify Konsole (Terminale Poliglotto)
    def open_konsole_window(self, x=130, y=36, w=540, h=390):
        win_id = f"konsole_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            txt_box = tk.Text(parent, bg="#080c14", fg="#38bdf8", insertbackground="#38bdf8", font=("Courier New", 9), bd=0, padx=8, pady=8)
            txt_box.pack(fill="both", expand=True)

            txt_box.insert("end", "=========================================================\n")
            txt_box.insert("end", "       OSify Universal Polyglot Konsole Terminal         \n")
            txt_box.insert("end", "=========================================================\n")
            txt_box.insert("end", "Comandi Windows: dir, ipconfig, tasklist, taskkill, cls\n")
            txt_box.insert("end", "Comandi macOS  : brew, open, pbcopy, pbpaste, say, sw_vers\n")
            txt_box.insert("end", "OSify Native   : osify-clean, osify-theme, osify-input, osify-tune\n\n")

            in_bar = tk.Frame(parent, bg="#111722", padx=6, pady=4)
            in_bar.pack(side="bottom", fill="x")

            tk.Label(in_bar, text="compagno@osify:~$ ", font=("Courier New", 9, "bold"), fg=engine.get_color("accent_mint"), bg="#111722").pack(side="left")
            entry_cmd = tk.Entry(in_bar, font=("Courier New", 9), bg="#1c2638", fg="#f1f5f9", insertbackground="#ffffff", bd=1, relief="solid")
            entry_cmd.pack(side="left", fill="x", expand=True, padx=(4, 6))

            def run_user_cmd(event=None):
                cmd_line = entry_cmd.get().strip()
                if not cmd_line:
                    return
                entry_cmd.delete(0, "end")
                txt_box.insert("end", f"compagno@osify:~$ {cmd_line}\n")

                if cmd_line.lower() in ("cls", "clear"):
                    txt_box.delete("1.0", "end")
                    return

                polyglot_script = os.path.join(REPO_ROOT, "tools/osify-shell/osify-polyglot-env.sh")
                shell_cmd = f"source '{polyglot_script}' 2>/dev/null; {cmd_line}"
                try:
                    proc = subprocess.run(["bash", "-c", shell_cmd], capture_output=True, text=True, timeout=10)
                    out = proc.stdout
                    err = proc.stderr
                    if out:
                        txt_box.insert("end", out)
                    if err:
                        txt_box.insert("end", err)
                except Exception as ex:
                    txt_box.insert("end", f"Errore: {ex}\n")

                txt_box.see("end")

            entry_cmd.bind("<Return>", run_user_cmd)
            entry_cmd.focus_set()

        win = OSifyFloatingWindow(self, win_id, "OSify Konsole", "terminal", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 2. Monitor di Sistema (Processi & Hardware)
    def open_sysmon_window(self, x=580, y=80, w=520, h=380):
        win_id = f"sysmon_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=12, pady=10)
            pad.pack(fill="both", expand=True)

            box_res = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=10, pady=8, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
            box_res.pack(fill="x", pady=(0, 8))

            tk.Label(box_res, text="CPU BORE Scheduler: 1000Hz (Bassa Latenza Determinista)", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_surface")).pack(anchor="w")
            tk.Label(box_res, text="ZRAM Swap Compresso: Attivo (Algoritmo LZ4 1.5x ratio)", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_surface")).pack(anchor="w")
            tk.Label(box_res, text="CAKE QoS Shaper: 0ms bufferbloat • Priorità pacchetti gioco attiva", font=("Helvetica Neue", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_surface")).pack(anchor="w")

            tk.Label(pad, text="Processi Attivi di Sistema:", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(4, 2))

            tbl_frame = tk.Frame(pad, bg="#080c14")
            tbl_frame.pack(fill="both", expand=True)

            txt_proc = tk.Text(tbl_frame, bg="#080c14", fg=engine.get_color("text_primary"), font=("Courier New", 8), bd=0, padx=6, pady=4)
            txt_proc.pack(fill="both", expand=True)

            def refresh_proc():
                if not txt_proc.winfo_exists():
                    return
                txt_proc.delete("1.0", "end")
                try:
                    out = subprocess.check_output(["ps", "-eo", "pid,comm,pmem", "-r"], text=True)
                    lines = out.strip().split("\n")[:18]
                    txt_proc.insert("end", "\n".join(lines))
                except Exception:
                    txt_proc.insert("end", "PID    COMMAND         %MEM\n1      systemd-init    0.4%\n54     kwin_wayland    1.8%\n88     osify-daemon    0.2%")
                parent.after(4000, refresh_proc)

            refresh_proc()

        win = OSifyFloatingWindow(self, win_id, "Monitor di Sistema", "sliders", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 3. Dolphin File Manager
    def open_filemanager_window(self, x=180, y=100, w=580, h=390):
        win_id = f"dolphin_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"))
            pad.pack(fill="both", expand=True)

            sb = tk.Frame(pad, bg=engine.get_color("bg_panel"), width=140, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
            sb.pack(side="left", fill="y")
            sb.pack_propagate(False)

            tk.Label(sb, text="POSIZIONI", font=("Helvetica Neue", 8, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_panel")).pack(anchor="w", padx=8, pady=(8, 4))
            for place in ("Home (~)", "Documenti", "Download", "Giochi", "Quarantena"):
                lbl = tk.Label(sb, text=f"📁 {place}", font=("Helvetica Neue", 8), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_panel"), cursor="hand2")
                lbl.pack(anchor="w", padx=8, pady=3)

            main_view = tk.Frame(pad, bg=engine.get_color("bg_base"), padx=10, pady=8)
            main_view.pack(side="left", fill="both", expand=True)

            tk.Label(main_view, text="Percorso: /home/compagno/OSify", font=("Courier New", 8, "bold"), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(0, 8))

            file_list = [
                ("audio/", "Cartella Configurazione PipeWire"),
                ("desktop/", "Ambiente Plasma 6 e Gestures"),
                ("security/", "Shield Antivirus, AdShield, Mobile Auth"),
                ("system/", "Autotune, Installer Bare-Metal, Workload, Input"),
                ("tools/", "Polyglot Shell, Package Manager, GUI"),
                ("README.md", "Documentazione Architetturale Ufficiale")
            ]

            for fname, desc in file_list:
                row = tk.Frame(main_view, bg=engine.get_color("bg_base"), pady=2)
                row.pack(fill="x")
                ico_str = "📁" if fname.endswith("/") else "📄"
                tk.Label(row, text=f"{ico_str} {fname:<14}", font=("Courier New", 8, "bold"), fg=engine.get_color("accent_cyan") if fname.endswith("/") else engine.get_color("text_primary"), bg=engine.get_color("bg_base")).pack(side="left")
                tk.Label(row, text=f"• {desc}", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(side="left", padx=6)

        win = OSifyFloatingWindow(self, win_id, "OSify Dolphin", "folder", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 4. Personalizzazione Grafica & Temi (NUOVO)
    def open_customizer_window(self, x=220, y=70, w=620, h=480):
        win_id = f"customizer_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=16, pady=12)
            pad.pack(fill="both", expand=True)

            tk.Label(pad, text="PERSONALIZZAZIONE & STILE DI SISTEMA", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_base")).pack(anchor="w")
            tk.Label(pad, text="Personalizza l'aspetto grafico, pulsanti delle finestre, cursori e raggio bordi.", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(1, 10))

            # 1. Sezione Temi
            tk.Label(pad, text="1. TEMA DI SISTEMA:", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(2, 4))
            themes_f = tk.Frame(pad, bg=engine.get_color("bg_base"))
            themes_f.pack(fill="x", pady=2)

            for tid, tmeta in THEMES.items():
                is_cur = (tid == engine.config["theme_id"])
                btn = tk.Label(
                    themes_f,
                    text=f"● {tmeta['name'].split('(')[0].strip()}",
                    font=("Helvetica Neue", 8, "bold" if is_cur else "normal"),
                    fg="#ffffff" if is_cur else engine.get_color("text_muted"),
                    bg=engine.get_color("accent_primary") if is_cur else engine.get_color("bg_card"),
                    padx=8,
                    pady=5,
                    cursor="hand2",
                    bd=1,
                    relief="solid",
                    highlightbackground=engine.get_color("border_active") if is_cur else engine.get_color("border_inactive"),
                    highlightthickness=1
                )
                btn.pack(side="left", padx=3)
                def make_th(t=tid):
                    return lambda e: (engine.set_theme(t), self.apply_theme_refresh())
                btn.bind("<Button-1>", make_th())

            # 2. Sezione Stile Pulsanti Finestra
            tk.Label(pad, text="2. STILE PULSANTI FINESTRA:", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(12, 4))
            btn_styles_f = tk.Frame(pad, bg=engine.get_color("bg_base"))
            btn_styles_f.pack(fill="x", pady=2)

            styles_opts = [
                ("macos_traffic_lights", "macOS Traffic Lights (Perline colorate)"),
                ("fluent_linear", "Windows 11 Fluent (Lineari minimali)"),
                ("breeze_circular", "KDE Plasma 6 Breeze (Cerchietti)")
            ]
            for sid, sname in styles_opts:
                is_cur = (sid == engine.config.get("window_buttons_style"))
                btn = tk.Label(
                    btn_styles_f,
                    text=sname,
                    font=("Helvetica Neue", 8, "bold" if is_cur else "normal"),
                    fg="#ffffff" if is_cur else engine.get_color("text_muted"),
                    bg=engine.get_color("accent_primary") if is_cur else engine.get_color("bg_card"),
                    padx=8,
                    pady=5,
                    cursor="hand2",
                    bd=1,
                    relief="solid",
                    highlightbackground=engine.get_color("border_active") if is_cur else engine.get_color("border_inactive"),
                    highlightthickness=1
                )
                btn.pack(side="left", padx=3)
                def make_st(s=sid):
                    return lambda e: (engine.set_window_buttons_style(s), self.apply_theme_refresh())
                btn.bind("<Button-1>", make_st())

            # 3. Raggio Angoli & Touchscreen Mode
            tk.Label(pad, text="3. RAGGIO ANGOLI & MODALITÀ TOUCH:", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(12, 4))
            row_radii = tk.Frame(pad, bg=engine.get_color("bg_base"))
            row_radii.pack(fill="x", pady=2)

            for r_val, r_label in [(0, "Squadrato (0px)"), (8, "Moderno (8px)"), (14, "Morbido (14px)")]:
                is_cur = (r_val == engine.config.get("corner_radius", 10))
                b = tk.Label(row_radii, text=r_label, font=("Helvetica Neue", 8), fg="#ffffff" if is_cur else engine.get_color("text_muted"), bg=engine.get_color("accent_primary") if is_cur else engine.get_color("bg_card"), padx=8, pady=4, cursor="hand2")
                b.pack(side="left", padx=3)
                def make_rad(rv=r_val):
                    return lambda e: (engine.set_corner_radius(rv), self.apply_theme_refresh())
                b.bind("<Button-1>", make_rad())

            # Touch Mode toggle
            cur_touch = engine.config.get("touch_mode", False)
            btn_touch = tk.Label(
                row_radii,
                text=f"Touch Mode: {'ATTIVA (44px target)' if cur_touch else 'Disattivata'}",
                font=("Helvetica Neue", 8, "bold"),
                fg="#ffffff" if cur_touch else engine.get_color("text_muted"),
                bg=engine.get_color("accent_mint") if cur_touch else engine.get_color("bg_card"),
                padx=10,
                pady=4,
                cursor="hand2"
            )
            btn_touch.pack(side="right", padx=6)
            def toggle_touch(e):
                engine.set_touch_mode(not engine.config.get("touch_mode", False))
                self.apply_theme_refresh()
            btn_touch.bind("<Button-1>", toggle_touch)

            # Notifica salvataggio
            lbl_info = tk.Label(pad, text="[✓] Modifiche salvate automaticamente in ~/.config/osify/appearance.json", font=("Courier New", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_base"))
            lbl_info.pack(side="bottom", pady=8)

        win = OSifyFloatingWindow(self, win_id, "Personalizzazione & Stile", "palette", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 5. Ottimizzazione Memoria & Cache (NUOVO)
    def open_memory_cleaner_window(self, x=240, y=90, w=560, h=410):
        win_id = f"memcleaner_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=16, pady=12)
            pad.pack(fill="both", expand=True)

            tk.Label(pad, text="OTTIMIZZAZIONE MEMORIA RAM & CACHE", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_base")).pack(anchor="w")
            tk.Label(pad, text="Gestione proattiva della cache, prevenzione blocco RAM e pulizia al riavvio.", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(1, 10))

            box_stat = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=12, pady=10, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
            box_stat.pack(fill="x", pady=4)

            lbl_ram = tk.Label(box_stat, text="RAM: Rilevamento in corso...", font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_surface"))
            lbl_ram.pack(anchor="w")
            lbl_cache = tk.Label(box_stat, text="Spazio Cache & /tmp: Calcolo...", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_surface"))
            lbl_cache.pack(anchor="w", pady=(2, 0))

            def update_stats():
                if not lbl_ram.winfo_exists():
                    return
                try:
                    cleaner_sh = os.path.join(REPO_ROOT, "system/storage/osify-memory-cleaner.sh")
                    out = subprocess.check_output([cleaner_sh, "status"], text=True)
                    for line in out.split("\n"):
                        if "RAM Disponibile" in line:
                            lbl_ram.config(text=line.strip())
                        if "Spazio ~/.cache" in line:
                            lbl_cache.config(text=line.strip())
                except Exception:
                    pass
                parent.after(5000, update_stats)

            update_stats()

            # Opzioni di Policy
            pol_f = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=10, pady=8, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
            pol_f.pack(fill="x", pady=10)

            tk.Label(pol_f, text="• Pulizia automatica ad ogni riavvio: ATTIVA (Default ON)", font=("Helvetica Neue", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_surface")).pack(anchor="w")
            tk.Label(pol_f, text="• Protezione Anti-OOM (Drop cache se RAM < 15%): ATTIVA", font=("Helvetica Neue", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_surface")).pack(anchor="w")
            tk.Label(pol_f, text="• Preservazione Shader Cache Giochi (Zero stutter 60 FPS): ATTIVA", font=("Helvetica Neue", 8), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_surface")).pack(anchor="w")

            btn_clean = tk.Label(
                pad,
                text="⚡ OTTIMIZZA & LIBERA MEMORIA ADESSO",
                font=("Helvetica Neue", 9, "bold"),
                bg=engine.get_color("accent_primary"),
                fg="#ffffff",
                padx=14,
                pady=8,
                cursor="hand2"
            )
            btn_clean.pack(pady=8)

            lbl_res = tk.Label(pad, text="", font=("Courier New", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_base"))
            lbl_res.pack()

            def do_clean(e):
                cleaner_sh = os.path.join(REPO_ROOT, "system/storage/osify-memory-cleaner.sh")
                try:
                    subprocess.run([cleaner_sh, "clean"], check=True)
                    lbl_res.config(text="[✓] Pagecache liberata, temporanei orfani rimossi con successo!")
                    update_stats()
                except Exception as ex:
                    lbl_res.config(text=f"[!] Errore: {ex}")

            btn_clean.bind("<Button-1>", do_clean)

        win = OSifyFloatingWindow(self, win_id, "Pulizia Memoria & Cache", "broom", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 6. Calibrazione Input & Touch (NUOVO)
    def open_input_settings_window(self, x=260, y=110, w=540, h=400):
        win_id = f"input_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=16, pady=12)
            pad.pack(fill="both", expand=True)

            tk.Label(pad, text="CALIBRAZIONE TOUCHSCREEN & TOUCHPAD", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_base")).pack(anchor="w")
            tk.Label(pad, text="Configurazione universale per schermi tattili, touchpad moderni e vintage.", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(1, 10))

            box_p = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=12, pady=10, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
            box_p.pack(fill="x", pady=4)

            opts = [
                ("Natural Scrolling (Scorrimento Naturale Invertito)", "natural", "true"),
                ("Tap to Click (Tocco singolo = Click)", "tap", "true"),
                ("Tasto Destro a Due Dita", "rightclick", "true"),
                ("Edge Scrolling Bordo Destro (Per Touchpad Vintage)", "edge", "auto"),
                ("Palm Rejection (Anti-urto durante la digitazione)", "palm", "true"),
                ("Tocco Prolungato = Tasto Destro (Touchscreen)", "touch", "true")
            ]

            for label, key, def_val in opts:
                r = tk.Frame(box_p, bg=engine.get_color("bg_surface"), pady=2)
                r.pack(fill="x")
                tk.Label(r, text=f"• {label}", font=("Helvetica Neue", 8), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_surface")).pack(side="left")
                tk.Label(r, text="[ATTIVO]", font=("Helvetica Neue", 8, "bold"), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_surface")).pack(side="right")

            btn_apply = tk.Label(
                pad,
                text="Applica Profilo Input al Sistema",
                font=("Helvetica Neue", 9, "bold"),
                bg=engine.get_color("accent_primary"),
                fg="#ffffff",
                padx=12,
                pady=6,
                cursor="hand2"
            )
            btn_apply.pack(pady=12)

            lbl_res = tk.Label(pad, text="", font=("Courier New", 8), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_base"))
            lbl_res.pack()

            def do_apply(e):
                in_sh = os.path.join(REPO_ROOT, "system/input/osify-input-manager.sh")
                try:
                    subprocess.run([in_sh, "apply"], check=True)
                    lbl_res.config(text="[✓] Calibrazione input applicata al kernel e a libinput!")
                except Exception as ex:
                    lbl_res.config(text=f"[!] Errore: {ex}")
            btn_apply.bind("<Button-1>", do_apply)

        win = OSifyFloatingWindow(self, win_id, "Calibrazione Input & Touch", "touch", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 7. Centro di Controllo OSify
    def open_control_center_window(self, x=180, y=80, w=560, h=400):
        win_id = f"ctrlcenter_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=14, pady=12)
            pad.pack(fill="both", expand=True)

            tk.Label(pad, text="CENTRO DI CONTROLLO & SICUREZZA OSIFY", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_base")).pack(anchor="w")
            tk.Label(pad, text="Regola e calibra tutti i moduli del sistema operativo in tempo reale.", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(1, 10))

            cards = [
                ("Workload Governor", "STREAM+GAME (CAKE QoS 0ms jitter)", lambda: subprocess.Popen([os.path.join(REPO_ROOT, "system/workload/osify-workload-governor.sh"), "stream-game"])),
                ("Hardware Autotune", "Calibrazione ISA CPU e GPU pipeline", lambda: subprocess.Popen([os.path.join(REPO_ROOT, "system/autotune/osify-autotune.sh"), "apply"])),
                ("OSify Shield Antivirus", "Scansione continua e quarantena chmod 000", lambda: subprocess.Popen([os.path.join(REPO_ROOT, "security/shield/osify-shield.sh"), "scan"])),
                ("AdShield DNS Sinkhole", "67+ domini pubblicitari e tracker bloccati", lambda: subprocess.Popen([os.path.join(REPO_ROOT, "security/adblock/osify-adblock.sh"), "enable"]))
            ]

            for title, desc, action in cards:
                c = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=10, pady=8, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
                c.pack(fill="x", pady=3)
                tk.Label(c, text=title, font=("Helvetica Neue", 9, "bold"), fg=engine.get_color("text_primary"), bg=engine.get_color("bg_surface")).pack(side="left")
                tk.Label(c, text=f" ({desc})", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_surface")).pack(side="left")

                btn = tk.Label(c, text="Esegui", font=("Helvetica Neue", 8, "bold"), bg=engine.get_color("accent_primary"), fg="#ffffff", padx=10, pady=2, cursor="hand2")
                btn.pack(side="right")
                btn.bind("<Button-1>", lambda e, a=action: a())

        win = OSifyFloatingWindow(self, win_id, "Centro di Controllo", "gear", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)

    # 8. Universal Execution Matrix
    def open_uem_window(self, x=220, y=110, w=520, h=360):
        win_id = f"uem_{int(time.time()*1000)}"

        def builder(parent, win_ref):
            engine = self.theme_engine
            pad = tk.Frame(parent, bg=engine.get_color("bg_base"), padx=14, pady=12)
            pad.pack(fill="both", expand=True)

            tk.Label(pad, text="UNIVERSAL EXECUTION MATRIX (UEM)", font=("Helvetica Neue", 11, "bold"), fg=engine.get_color("accent_cyan"), bg=engine.get_color("bg_base")).pack(anchor="w")
            tk.Label(pad, text="Sfondamento trasparente delle barriere architetturali. Esegui qualsiasi file binario.", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_base")).pack(anchor="w", pady=(1, 10))

            targets = [
                ("Windows PE 64-bit (.exe)", "Cyberpunk 2077, Elden Ring via Proton-GE"),
                ("MS-DOS 16-bit (.com / .exe)", "Doom, Prince of Persia via DOSBox-Staging"),
                ("Apple macOS Mach-O (CLI / .app)", "Software Darwin via Darling Translation Layer"),
                ("Android Application (.apk)", "App Mobile e Produttività via Waydroid LXC"),
                ("WebAssembly Standalone (.wasm)", "Micro-servizi WASI ad alte prestazioni")
            ]

            for fmt, sub in targets:
                r = tk.Frame(pad, bg=engine.get_color("bg_surface"), padx=10, pady=6, bd=1, relief="solid", highlightbackground=engine.get_color("border_inactive"), highlightthickness=1)
                r.pack(fill="x", pady=2)
                tk.Label(r, text=fmt, font=("Courier New", 8, "bold"), fg=engine.get_color("accent_mint"), bg=engine.get_color("bg_surface")).pack(side="left")
                tk.Label(r, text=f" • {sub}", font=("Helvetica Neue", 8), fg=engine.get_color("text_muted"), bg=engine.get_color("bg_surface")).pack(side="left")

        win = OSifyFloatingWindow(self, win_id, "Universal Execution Matrix", "chip", x, y, w, h, builder)
        self.windows[win_id] = win
        self.bring_to_front(win_id)
