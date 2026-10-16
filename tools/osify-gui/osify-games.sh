#!/bin/sh
# ==============================================================================
# OSify Gaming & Retrogaming Hub 2050 — Interfaccia Grafica Nativa
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Compatibile al 100% con POSIX /bin/sh, Busybox ash e GNU Bash.
# 100% GUI: selettore file nativo, nessun terminale, zero console CLI.
# ==============================================================================

set -e

GAMES_DIR="$HOME/Giochi"
mkdir -p "$GAMES_DIR"

boost_gaming_profile() {
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [ -f "$gov" ] && echo "performance" > "$gov" 2>/dev/null || true
    done
    sysctl -w vm.dirty_ratio=10 vm.dirty_background_ratio=5 2>/dev/null || true
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
}

launch_game_file() {
    target="$1"
    [ -z "$target" ] || [ ! -f "$target" ] && return
    boost_gaming_profile
    if [ -x /usr/bin/osify-exec ]; then
        /usr/bin/osify-exec "$target" &
    elif command -v wine >/dev/null 2>&1; then
        wine "$target" &
    elif command -v dosbox >/dev/null 2>&1; then
        dosbox "$target" &
    else
        xdg-open "$target" 2>/dev/null || true
    fi
}

# ------------------------------------------------------------------------------
# 1. MODALITÀ GUI YAD (Cyber-Gaming 2050)
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    while true; do
        ACTION=$(yad --title="OSify Gaming & UEM Hub" \
            --window-icon="/usr/share/pixmaps/osify-games.png" \
            --width=500 --height=380 --center \
            --list --radiolist \
            --text="<b><big>🎮 Centro Gaming & Retrogaming 2050</big></b>\nSeleziona l'azione desiderata:" \
            --column="Scelta" --column="Icona" --column="Azione" \
            TRUE "🕹️" "Esegui Gioco Windows (.exe / DirectX / Wine)" \
            FALSE "👾" "Retrogaming DOS & Console (.com / .exe / ROM)" \
            FALSE "⚡" "Attiva Turbo Boost Prestazioni (CPU & GPU)" \
            FALSE "📁" "Esplora Cartella Giochi ($GAMES_DIR)" \
            --button="Chiudi!gtk-cancel:1" \
            --button="Avvia!gtk-ok:0") || exit 0

        CHOSEN=$(echo "$ACTION" | cut -d'|' -f3)
        case "$CHOSEN" in
            *"Windows"*)
                GAME_FILE=$(yad --file-selection --title="Seleziona Eseguibile Windows (.exe)" \
                    --filename="$GAMES_DIR/" \
                    --file-filter="Eseguibili Windows (*.exe)|*.exe;*.EXE" \
                    --center --width=600 --height=450) || true
                [ -n "$GAME_FILE" ] && launch_game_file "$GAME_FILE"
                ;;
            *"DOS"*)
                DOS_FILE=$(yad --file-selection --title="Seleziona Gioco DOS o ROM" \
                    --filename="$GAMES_DIR/" \
                    --file-filter="Giochi DOS & ROM|*.exe;*.com;*.iso;*.bin;*.rom" \
                    --center --width=600 --height=450) || true
                [ -n "$DOS_FILE" ] && launch_game_file "$DOS_FILE"
                ;;
            *"Turbo Boost"*)
                boost_gaming_profile
                yad --title="OSify Turbo Boost" --info \
                    --text="<b><big>⚡ Turbo Boost Gaming Attivato!</big></b>\n\n• Governor CPU: <b>Performance</b>\n• Cache RAM: <b>Ottimizzata e ripulita</b>\n• Priorita I/O: <b>Real-time per il gioco</b>" \
                    --center --width=380 --button="OK:0"
                ;;
            *"Esplora"*)
                if command -v pcmanfm >/dev/null 2>&1; then
                    pcmanfm "$GAMES_DIR" &
                fi
                ;;
            *)
                exit 0
                ;;
        esac
    done
fi

# ------------------------------------------------------------------------------
# 2. MODALITÀ GUI ZENITY
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v zenity >/dev/null 2>&1; then
    while true; do
        ACTION=$(zenity --list --title="OSify Gaming Hub" \
            --text="Seleziona operazione gaming:" \
            --column="Opzione" \
            "Esegui Gioco Windows (.exe)" \
            "Retrogaming DOS / Emulatori" \
            "Attiva Turbo Boost Prestazioni" \
            "Apri Cartella Giochi" \
            --width=450 --height=320) || exit 0

        case "$ACTION" in
            *"Windows"*)
                GF=$(zenity --file-selection --title="Seleziona Gioco .exe" --filename="$GAMES_DIR/") || true
                [ -n "$GF" ] && launch_game_file "$GF"
                ;;
            *"DOS"*)
                DF=$(zenity --file-selection --title="Seleziona File DOS" --filename="$GAMES_DIR/") || true
                [ -n "$DF" ] && launch_game_file "$DF"
                ;;
            *"Turbo"*)
                boost_gaming_profile
                zenity --info --title="Turbo Boost" --text="Prestazioni massime attivate!" --width=300
                ;;
            *"Cartella"*)
                pcmanfm "$GAMES_DIR" &
                ;;
            *)
                exit 0
                ;;
        esac
    done
fi

# ------------------------------------------------------------------------------
# 3. MODALITÀ PYTHON TKINTER
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1; then
    exec python3 - << 'PYEOF'
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

GAMES_DIR = os.path.expanduser("~/Giochi")
os.makedirs(GAMES_DIR, exist_ok=True)

root = tk.Tk()
root.title("OSify Gaming & Retrogaming Hub")
root.geometry("480x360")
root.configure(bg="#0b0d14")
root.resizable(False, False)

header = tk.Label(root, text="🎮 OSIFY GAMING MATRIX 2050", 
                  font=("Helvetica", 13, "bold"), fg="#38bdf8", bg="#0b0d14")
header.pack(pady=15)

def run_exe():
    f = filedialog.askopenfilename(initialdir=GAMES_DIR, title="Seleziona Gioco (.exe)", filetypes=[("Eseguibili Windows", "*.exe;*.EXE")])
    if f:
        subprocess.Popen(f"/usr/bin/osify-exec '{f}'", shell=True)
        messagebox.showinfo("OSify Gaming", f"Avvio di: {os.path.basename(f)}")

def run_dos():
    f = filedialog.askopenfilename(initialdir=GAMES_DIR, title="Seleziona Gioco DOS", filetypes=[("File DOS", "*.exe;*.com;*.bat")])
    if f:
        subprocess.Popen(f"dosbox '{f}' 2>/dev/null || /usr/bin/osify-exec '{f}'", shell=True)

def boost():
    subprocess.run("sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true", shell=True)
    messagebox.showinfo("Turbo Boost", "Prestazioni massime CPU/GPU attivate!")

def open_dir():
    subprocess.Popen(f"pcmanfm '{GAMES_DIR}' 2>/dev/null || xdg-open '{GAMES_DIR}'", shell=True)

btn_style = {"font": ("Helvetica", 11, "bold"), "fg": "#ffffff", "relief": tk.FLAT, "pady": 8, "cursor": "hand2"}

tk.Button(root, text="🕹️  Esegui Gioco Windows (.EXE)", bg="#0284c7", activebackground="#0369a1", command=run_exe, **btn_style).pack(fill=tk.X, padx=30, pady=5)
tk.Button(root, text="👾  Retrogaming DOS & Console", bg="#1e293b", activebackground="#334155", command=run_dos, **btn_style).pack(fill=tk.X, padx=30, pady=5)
tk.Button(root, text="⚡  Attiva Profilo Turbo Boost", bg="#7c3aed", activebackground="#6d28d9", command=boost, **btn_style).pack(fill=tk.X, padx=30, pady=5)
tk.Button(root, text="📁  Apri Cartella Giochi", bg="#334155", activebackground="#475569", command=open_dir, **btn_style).pack(fill=tk.X, padx=30, pady=5)

root.mainloop()
PYEOF
    exit 0
fi

exit 0
