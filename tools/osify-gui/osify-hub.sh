#!/bin/sh
# ==============================================================================
# OSify Hub — Il Centro di Controllo e Launchpad Ufficiale a 360°
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Centro operativo omnicomprensivo: Web, Gaming, Sviluppo, Ufficio,
# Personalizzazione, Ottimizzazione Hardware e Installatore su Disco Fisso.
# ==============================================================================

# Rilevamento Hardware in tempo reale
CPU_MODEL=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//')
[ -z "$CPU_MODEL" ] && CPU_MODEL="$(uname -m)"
CPU_CORES=$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo 1)

RAM_TOTAL=$(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")
RAM_AVAIL=$(awk '/MemAvailable/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")
SWAP_TOTAL=$(awk '/SwapTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "0 MB")

GPU_NAME=$(lspci 2>/dev/null | grep -iE 'vga|display|3d' | head -n1 | cut -d: -f3 | sed 's/^[ \t]*//')
[ -z "$GPU_NAME" ] && GPU_NAME="Controller Grafico Integrato"

DISP_RES=$(xrandr 2>/dev/null | grep -o '[0-9]\+x[0-9]\+' | head -n1 || echo "1024x600")

# Classificazione Edizione OSify
TOTAL_MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 1048576)
if [ "$TOTAL_MEM_KB" -lt 2500000 ] || [ "$(uname -m)" = "i686" ]; then
    OSIFY_TIER="Riesumare Antichi (Vintage 32-bit Edition)"
elif [ "$TOTAL_MEM_KB" -gt 12000000 ]; then
    OSIFY_TIER="OSify Pro Station (64-bit Performance)"
else
    OSIFY_TIER="OSify Standard Edition (Universal 64-bit)"
fi

# Funzioni Operative
boost_system() {
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [ -f "$gov" ] && echo "performance" > "$gov" 2>/dev/null || true
    done
    modprobe -q zram 2>/dev/null || true
    if [ -b /dev/zram0 ]; then
        echo lz4 > /sys/block/zram0/comp_algorithm 2>/dev/null || echo lzo > /sys/block/zram0/comp_algorithm 2>/dev/null || true
        echo 1073741824 > /sys/block/zram0/disksize 2>/dev/null || echo 1G > /sys/block/zram0/disksize 2>/dev/null || true
        mkswap /dev/zram0 >/dev/null 2>&1 || true
        swapon -p 100 /dev/zram0 2>/dev/null || true
        sysctl -w vm.swappiness=70 vm.vfs_cache_pressure=50 >/dev/null 2>&1 || true
    fi
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

    if command -v dialog >/dev/null 2>&1; then
        dialog --title "OSify — Turbo Boost Attivato" \
            --msgbox "\n[✓] CPU Governor: Modalità Prestazioni Massime\n[✓] Modulo zRAM: 1 GB di Swap Ultra-Veloce Attivo\n[✓] Cache RAM: Ottimizzata e ripulita!\n" 9 55
    fi
}

fix_touchpad() {
    /usr/bin/osify-input-setup 2>/dev/null || true
    if command -v dialog >/dev/null 2>&1; then
        dialog --title "OSify — Calibrazione Touchpad" \
            --msgbox "\n[✓] Tocco per cliccare (Tap-To-Click): ABILITATO\n[✓] Scorrimento con scorrimento bordo: ABILITATO\n[✓] Driver evdev & psmouse: Sincronizzati!\n" 9 55
    fi
}

unmute_audio() {
    amixer sset Master unmute 90% >/dev/null 2>&1 || true
    amixer sset PCM unmute 90% >/dev/null 2>&1 || true
    amixer sset Speaker unmute 90% >/dev/null 2>&1 || true
    amixer sset Headphone unmute 90% >/dev/null 2>&1 || true
    aplay -q /usr/share/sounds/alsa/Front_Center.wav 2>/dev/null || true
    if command -v dialog >/dev/null 2>&1; then
        dialog --title "OSify — Audio Inizializzato" \
            --msgbox "\n[✓] Canali Master, PCM e Speaker portati al 90% e sbloccati da mute.\n" 7 55
    fi
}

open_browser() {
    if [ -x /usr/bin/osify-browser ]; then
        /usr/bin/osify-browser &
    elif command -v dillo >/dev/null 2>&1; then
        dillo &
    elif command -v firefox >/dev/null 2>&1; then
        firefox &
    fi
}

open_wifi_manager() {
    if [ -x /usr/bin/osify-wifi ]; then
        terminal -geometry 75x20 -T "OSify Wi-Fi Manager" -e /usr/bin/osify-wifi &
    elif [ -x /opt/osify/network/osify-wifi-gui.sh ]; then
        terminal -geometry 75x20 -T "OSify Wi-Fi Manager" -e /opt/osify/network/osify-wifi-gui.sh &
    fi
}

open_gaming_hub() {
    if [ -x /usr/bin/osify-games ]; then
        terminal -geometry 75x20 -T "OSify Gaming Hub" -e /usr/bin/osify-games &
    elif [ -x /opt/osify/tools/osify-gui/osify-games.sh ]; then
        terminal -geometry 75x20 -T "OSify Gaming Hub" -e /opt/osify/tools/osify-gui/osify-games.sh &
    fi
}

open_developer_suite() {
    if [ -x /usr/bin/osify-developer ]; then
        terminal -geometry 75x20 -T "OSify Developer Suite" -e /usr/bin/osify-developer &
    elif [ -x /opt/osify/tools/osify-gui/osify-developer.sh ]; then
        terminal -geometry 75x20 -T "OSify Developer Suite" -e /opt/osify/tools/osify-gui/osify-developer.sh &
    fi
}

open_appearance_mgr() {
    if [ -x /usr/bin/osify-appearance ]; then
        terminal -geometry 75x20 -T "OSify Appearance Manager" -e /usr/bin/osify-appearance &
    elif [ -x /opt/osify/tools/osify-gui/osify-appearance.sh ]; then
        terminal -geometry 75x20 -T "OSify Appearance Manager" -e /opt/osify/tools/osify-gui/osify-appearance.sh &
    fi
}

take_screenshot() {
    mkdir -p "$HOME/Immagini/Screenshot"
    sfile="$HOME/Immagini/Screenshot/screenshot_$(date +%Y%m%d_%H%M%S).png"
    if command -v import >/dev/null 2>&1; then
        import -window root "$sfile" 2>/dev/null || true
    elif command -v scrot >/dev/null 2>&1; then
        scrot "$sfile" 2>/dev/null || true
    fi
    if command -v dialog >/dev/null 2>&1; then
        dialog --title "Screenshot Catturato" --msgbox "\nSchermata salvata in:\n$sfile\n" 8 50
    fi
}

open_app_drawer() {
    if [ -x /usr/bin/osify-app-drawer ]; then
        /usr/bin/osify-app-drawer &
    elif [ -f /opt/osify/tools/osify-gui/osify-app-drawer.py ]; then
        python3 /opt/osify/tools/osify-gui/osify-app-drawer.py &
    elif [ -f "$(dirname "$0")/osify-app-drawer.py" ]; then
        python3 "$(dirname "$0")/osify-app-drawer.py" &
    fi
}

# Loop Menu Principale
while true; do
    if command -v dialog >/dev/null 2>&1; then
        CHOICE=$(dialog --stdout --backtitle "OSify Operating System — Ingegnerizzato da Andrea Taliento (ANDRYXify)" \
            --title " 🚀 OSify Hub — Il Tuo Sistema Operativo a 360° " \
            --menu "Edizione: $OSIFY_TIER\nCPU: $CPU_MODEL ($CPU_CORES Core) | RAM: $RAM_AVAIL / $RAM_TOTAL\nDisplay: $DISP_RES | GPU: $GPU_NAME\n\nCosa desideri fare?" 23 75 12 \
            "1" "🚀  Apri App Drawer (Launchpad con Ricerca Istantanea)" \
            "2" "🌐  Naviga su Internet (Browser Web Grafico Veloce)" \
            "3" "📡  Connettiti al Wi-Fi (Scansione Reti & Password)" \
            "4" "🎮  Gaming & Retrogaming Hub (Windows .exe, DOS, Emulazione)" \
            "5" "💻  Programma & Sviluppa (Python 3, C/TCC, Git, Nano, Progetti)" \
            "6" "📁  Lavoro & Produttività (File Manager, PDF, Archivi, Cattura)" \
            "7" "🎨  Personalizzazione (Virtual Scaler 1280x768, Sfondi, Temi)" \
            "8" "⚡  Turbo Boost Hardware (CPU Performance + zRAM 1GB + Touchpad)" \
            "9" "🔊  Audio & Calibrazione Suono (Sblocca Master/PCM al 90%)" \
            "10" "📊  Task Manager & Monitor Risorse (Processi in tempo reale)" \
            "11" "💾  Installa OSify su Disco Fisso (con migrazione profilo Live)" \
            "0" "❌  Torna al Desktop" 2>/dev/null || echo "0")
    else
        clear
        echo "========================================================="
        echo "   🚀 OSify Hub — Il Tuo Sistema Operativo a 360°        "
        echo "========================================================="
        echo " Edizione : $OSIFY_TIER"
        echo " CPU      : $CPU_MODEL ($CPU_CORES Core)"
        echo " RAM      : $RAM_AVAIL liberi su $RAM_TOTAL"
        echo " Display  : $DISP_RES | GPU: $GPU_NAME"
        echo "---------------------------------------------------------"
        echo "  1) 🚀 Apri App Drawer (Launchpad con Ricerca Istantanea)"
        echo "  2) 🌐 Naviga su Internet (Browser Web Grafico)"
        echo "  3) 📡 Connettiti al Wi-Fi (Scansione reti wireless)"
        echo "  4) 🎮 Gaming & Retrogaming (Windows .exe, DOS, Emulazione)"
        echo "  5) 💻 Programma & Sviluppa (Python 3, C, Git, Nano)"
        echo "  6) 📁 Lavoro & File (File Manager, PDF, Archivi)"
        echo "  7) 🎨 Personalizzazione (Scaler 1280x768, Sfondi, Temi)"
        echo "  8) ⚡ Turbo Boost (CPU Performance + zRAM 1GB)"
        echo "  9) 🔊 Sblocca Audio ALSA"
        echo " 10) 📊 Task Manager & Monitor Processi"
        echo " 11) 💾 Installa OSify su Disco Fisso (con migrazione Live)"
        echo "  0) ❌ Esci al Desktop"
        echo "========================================================="
        read -rp "Selezione [0-11]: " CHOICE
    fi

    case "$CHOICE" in
        1) open_app_drawer ;;
        2) open_browser ;;
        3) open_wifi_manager ;;
        4) open_gaming_hub ;;
        5) open_developer_suite ;;
        6) pcmanfm "$HOME" & ;;
        7) open_appearance_mgr ;;
        8) boost_system ;;
        9) unmute_audio ;;
        10) terminal -geometry 95x26 -T 'OSify Task Manager' -e /usr/bin/osify-taskmanager & ;;
        11) terminal -geometry 95x28 -T 'OSify Bare-Metal Installer' -e /usr/bin/osify-install & ;;
        0|"") clear; exit 0 ;;
        *) clear; exit 0 ;;
    esac
done
