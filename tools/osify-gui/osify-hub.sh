#!/bin/sh
# ==============================================================================
# OSify Hub 2050 — Il Centro di Controllo e Launchpad Ufficiale
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Centro operativo omnicomprensivo 100% GUI: nessuna console di testo su desktop.
# ==============================================================================

set -e

CPU_MODEL=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//')
[ -z "$CPU_MODEL" ] && CPU_MODEL="$(uname -m)"
CPU_CORES=$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo 1)

RAM_TOTAL=$(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")
RAM_AVAIL=$(awk '/MemAvailable/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")

TOTAL_MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 1048576)
if [ "$TOTAL_MEM_KB" -lt 2500000 ] || [ "$(uname -m)" = "i686" ]; then
    OSIFY_TIER="Vintage Edition (Intel Atom / 32-bit)"
else
    OSIFY_TIER="Modern Pro Station (x86_64 v3)"
fi

boost_system() {
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [ -f "$gov" ] && echo "performance" > "$gov" 2>/dev/null || true
    done
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
}

# Se PyQt6 è disponibile, apri il Control Center avanzato
if [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1; then
    CC_PY="$(dirname "$0")/osify-control-center.py"
    [ ! -f "$CC_PY" ] && CC_PY="/opt/osify/tools/osify-gui/osify-control-center.py"
    if [ -f "$CC_PY" ] && python3 -c "import PyQt6" 2>/dev/null; then
        exec python3 "$CC_PY"
    fi
fi

# ------------------------------------------------------------------------------
# 1. MODALITÀ GUI YAD (Cyber-Hub 2050)
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    while true; do
        SEL=$(yad --title="OSify Hub — Master Dashboard 2050" \
            --window-icon="/usr/share/pixmaps/osify-hub.png" \
            --width=560 --height=440 --center \
            --list \
            --text="<b><big>OSify 2.0 Operating System</big></b>\n• Profilo: <b>$OSIFY_TIER</b>\n• CPU: <b>$CPU_MODEL ($CPU_CORES core)</b>\n• RAM: <b>$RAM_AVAIL liberi su $RAM_TOTAL</b>\n\nSeleziona un'area operativa:" \
            --column="Icona" --column="Modulo" --column="Descrizione" \
            "⚡" "Turbo Boost Prestazioni" "Ottimizza CPU governor e svuota cache RAM" \
            "🌐" "Connessione Wi-Fi" "Scansione e connessione alle reti wireless" \
            "🎮" "Gaming & Retrogaming Hub" "Giochi Windows, DOS, emulatori e ROM" \
            "🎨" "Personalizzazione & Display" "Sfondi, risoluzioni, scala e temi cyber" \
            "🛠️" "Strumenti per Sviluppatori" "Compilatori, UEM Inspector e debugger" \
            "📊" "Monitor Risorse e Attivita" "Uso CPU, processi e memoria in tempo reale" \
            "💿" "Installa OSify su Disco" "Installatore bare-metal autonomo su HDD/SSD" \
            "ℹ️" "Scheda Tecnica Completa" "Dettagli hardware, driver e sensori" \
            --button="Chiudi!gtk-cancel:1" \
            --button="Apri!gtk-ok:0") || exit 0

        ACT=$(echo "$SEL" | cut -d'|' -f2)
        case "$ACT" in
            *"Turbo Boost"*)
                boost_system
                yad --title="Turbo Boost" --info \
                    --text="<b>[✓] Ottimizzazione Completata!</b>\n\nPrestazioni massime abilitate." \
                    --center --width=320 --button="OK:0"
                ;;
            *"Wi-Fi"*)
                /usr/bin/osify-wifi &
                ;;
            *"Gaming"*)
                /usr/bin/osify-games &
                ;;
            *"Personalizzazione"*)
                /usr/bin/osify-appearance &
                ;;
            *"Sviluppatori"*)
                /usr/bin/osify-developer &
                ;;
            *"Monitor"*)
                /usr/bin/osify-taskmanager &
                ;;
            *"Installa"*)
                /usr/bin/osify-install &
                ;;
            *"Scheda"*)
                /usr/bin/osify-sysinfo &
                ;;
            *)
                exit 0
                ;;
        esac
    done
fi

# ------------------------------------------------------------------------------
# 2. MODALITÀ GUI PYTHON TKINTER
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1; then
    exec python3 - << 'PYEOF'
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

root = tk.Tk()
root.title("OSify Hub — Master Dashboard 2050")
root.geometry("520x460")
root.configure(bg="#0b0d14")
root.resizable(False, False)

header = tk.Label(root, text="⚡ OSIFY MASTER HUB 2050", 
                  font=("Helvetica", 14, "bold"), fg="#38bdf8", bg="#0b0d14")
header.pack(pady=12)

sub = tk.Label(root, text="Piattaforma Operativa Universale e Centro di Controllo", 
               font=("Helvetica", 9), fg="#94a3b8", bg="#0b0d14")
sub.pack()

btn_frame = tk.Frame(root, bg="#0b0d14")
btn_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=15)

def spawn(cmd):
    subprocess.Popen(cmd, shell=True)

def boost():
    subprocess.run("sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true", shell=True)
    messagebox.showinfo("Turbo Boost", "Prestazioni massime attivate con successo!")

buttons = [
    ("⚡ Attiva Turbo Boost Prestazioni", boost, "#7c3aed"),
    ("🌐 Connessione Wi-Fi & Reti", lambda: spawn("/usr/bin/osify-wifi"), "#0284c7"),
    ("🎮 Gaming & Retrogaming Hub", lambda: spawn("/usr/bin/osify-games"), "#059669"),
    ("🎨 Personalizzazione Schermo & Temi", lambda: spawn("/usr/bin/osify-appearance"), "#1e293b"),
    ("🛠️ Strumenti di Sviluppo UEM", lambda: spawn("/usr/bin/osify-developer"), "#1e293b"),
    ("📊 Gestione Attivita di Sistema", lambda: spawn("/usr/bin/osify-taskmanager"), "#1e293b"),
    ("💿 Installa OSify su Disco Fisso", lambda: spawn("/usr/bin/osify-install"), "#d97706"),
]

for text, cmd, col in buttons:
    b = tk.Button(btn_frame, text=text, font=("Helvetica", 10, "bold"), 
                  fg="#ffffff", bg=col, activebackground="#334155", 
                  relief=tk.FLAT, pady=6, cursor="hand2", command=cmd)
    b.pack(fill=tk.X, pady=4)

root.mainloop()
PYEOF
    exit 0
fi

exit 0
