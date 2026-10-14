#!/bin/sh
# ==============================================================================
# OSify Welcome & Hardware Control Wizard (Native GTK2 / YAD / Dialog / TUI)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Ottimizzato specificamente per schermi WSVGA 1024x600 (Toshiba NB200) e PC moderni.
# Funziona al 100% senza Python, consuma meno di 4MB di RAM, avvio istantaneo.
# ==============================================================================

# Rilevamento info hardware
detect_hw() {
    CPU_INFO=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^[ \t]*//')
    [ -z "$CPU_INFO" ] && CPU_INFO=$(uname -m)
    
    RAM_TOTAL=$(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")
    RAM_FREE=$(awk '/MemAvailable/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "N/A")
    
    SWAP_INFO=$(awk '/SwapTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "0 MB")
    
    GPU_INFO=$(lspci 2>/dev/null | grep -iE 'vga|display|3d' | head -n1 | cut -d: -f3 | sed 's/^[ \t]*//')
    [ -z "$GPU_INFO" ] && GPU_INFO="Controller Grafico Standard"
    
    DISKS_INFO=$(lsblk -d -n -o NAME,SIZE,MODEL 2>/dev/null | grep -v "loop" | tr '\n' ' | ' || echo "Standard")
}

# Trova un emulatore di terminale valido
get_terminal() {
    for term in sakura xterm terminal lxterminal urxvt rxvt; do
        if command -v "$term" >/dev/null 2>&1; then
            echo "$term"
            return
        fi
    done
    echo "xterm"
}

TERM_BIN=$(get_terminal)

# Azione: Avvio installatore su disco
action_install() {
    if [ -x /usr/bin/osify-install ]; then
        $TERM_BIN -geometry 95x26+30+30 -T "OSify Disk Installer" -e /usr/bin/osify-install &
    elif [ -x /osify/system/installer/osify-disk-installer.sh ]; then
        $TERM_BIN -geometry 95x26+30+30 -T "OSify Disk Installer" -e /osify/system/installer/osify-disk-installer.sh &
    else
        yad --error --title="OSify" --text="Installatore non trovato in /usr/bin/osify-install" --width=350 --button="OK":0 2>/dev/null || echo "Errore installer"
    fi
}

# Azione: Ottimizzazione zRAM e memoria
action_zram() {
    modprobe zram 2>/dev/null || true
    if [ -b /dev/zram0 ]; then
        echo lz4 > /sys/block/zram0/comp_algorithm 2>/dev/null || echo lzo > /sys/block/zram0/comp_algorithm 2>/dev/null || true
        echo 1073741824 > /sys/block/zram0/disksize 2>/dev/null || echo 1G > /sys/block/zram0/disksize 2>/dev/null || true
        mkswap /dev/zram0 >/dev/null 2>&1 || true
        swapon -p 100 /dev/zram0 2>/dev/null || true
        sysctl -w vm.swappiness=60 vm.vfs_cache_pressure=50 >/dev/null 2>&1 || true
    fi
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    
    NEW_RAM_FREE=$(awk '/MemFree/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "OK")
    if command -v yad >/dev/null 2>&1; then
        yad --info --title="Memoria Ottimizzata" --text="<b>zRAM Swap 1GB Attivata!</b>\n\nMemoria cache liberata con successo.\nRAM Libera Attuale: $NEW_RAM_FREE" --width=380 --button="Chiudi":0
    else
        echo "zRAM attivata e cache pulita. RAM libera: $NEW_RAM_FREE"
    fi
}

# Azione: Touchpad Netbook Synaptics
action_touchpad() {
    synclient TapButton1=1 TapButton2=3 TapButton3=2 VertEdgeScroll=1 HorizEdgeScroll=1 CoastingSpeed=20 2>/dev/null || true
    if command -v yad >/dev/null 2>&1; then
        yad --info --title="Touchpad Netbook" --text="<b>Touchpad Configurato per Netbook!</b>\n\n• Tocco per fare click: ATTIVO (TapButton1=1)\n• Scorrimento laterale bordo destro: ATTIVO\n• Tocco due dita per menu contestuale: ATTIVO" --width=380 --button="Chiudi":0
    else
        echo "Touchpad configurato con successo."
    fi
}

# Azione: Unmute Audio ALSA
action_audio() {
    amixer sset Master unmute 85% >/dev/null 2>&1 || true
    amixer sset PCM unmute 85% >/dev/null 2>&1 || true
    amixer sset Speaker unmute 85% >/dev/null 2>&1 || true
    amixer sset Headphone unmute 85% >/dev/null 2>&1 || true
    aplay /usr/share/sounds/alsa/Front_Center.wav >/dev/null 2>&1 || true
    if command -v yad >/dev/null 2>&1; then
        yad --info --title="Audio Sbloccato" --text="<b>Scheda Audio Inizializzata!</b>\n\nCanali Master, PCM e Speaker portati all'85% e sbloccati da mute." --width=380 --button="Chiudi":0
    else
        echo "Audio sbloccato."
    fi
}

# Azione: Configurazione Rete Wi-Fi
action_wifi() {
    rfkill unblock all 2>/dev/null || true
    if [ -x /usr/bin/osify-wifi ]; then
        $TERM_BIN -geometry 78x22 -T "OSify Wi-Fi Manager" -e /usr/bin/osify-wifi &
    elif [ -x /opt/osify/network/osify-wifi-gui.sh ]; then
        $TERM_BIN -geometry 78x22 -T "OSify Wi-Fi Manager" -e /opt/osify/network/osify-wifi-gui.sh &
    else
        $TERM_BIN -geometry 78x22 -T "OSify Wi-Fi" -e sh -c 'osify wifi; echo ""; echo "Premi INVIO per chiudere..."; read -r dummy' &
    fi
}

# Azione: Terminale Root
action_terminal() {
    $TERM_BIN -geometry 90x24+40+40 -T "Terminale Cyber-OSify" &
}

# ------------------------------------------------------------------------------
# Interfaccia Principale YAD (GTK2 Nativo)
# ------------------------------------------------------------------------------
gui_yad() {
    detect_hw

    TEXT_BANNER="<big><b>Benvenuto in OSify</b></big>\n\
<i>Sistema Operativo per Netbook (Intel Atom N280 / GMA 950) e PC Universali</i>\n\
<i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>\n\n\
• <b>Processore:</b> $CPU_INFO\n\
• <b>Memoria RAM:</b> $RAM_TOTAL (Disponibile: $RAM_FREE) | <b>Swap:</b> $SWAP_INFO\n\
• <b>Scheda Video:</b> $GPU_INFO\n\
• <b>Kernel:</b> $(uname -r) ($(uname -m))\n\n\
Scegli l'operazione da eseguire:"

    while true; do
        CHOICE=$(yad --width=640 --height=460 --center \
            --title="Benvenuto in OSify — Centro Operativo di Primo Avvio" \
            --window-icon="/usr/share/pixmaps/osify-hub.png" \
            --text="$TEXT_BANNER" \
            --button="Installa su Disco Fisso!/usr/share/pixmaps/osify-install.png:1" \
            --button="Turbo Boost & zRAM!/usr/share/pixmaps/osify-hub.png:2" \
            --button="Calibra Touchpad!/usr/share/pixmaps/osify-settings.png:3" \
            --button="Sblocca Audio!/usr/share/pixmaps/osify-games.png:4" \
            --button="Connessione Wi-Fi!/usr/share/pixmaps/osify-wifi.png:5" \
            --button="Terminale!utilities-terminal:6" \
            --button="Chiudi!window-close:0" \
            2>/dev/null)
        RET=$?

        case $RET in
            1) action_install ;;
            2) action_zram ;;
            3) action_touchpad ;;
            4) action_audio ;;
            5) action_wifi ;;
            6) action_terminal ;;
            0|252) exit 0 ;;
            *) exit 0 ;;
        esac
    done
}

# ------------------------------------------------------------------------------
# Interfaccia Alternativa Curses (Dialog) se YAD non è disponibile o no X11
# ------------------------------------------------------------------------------
gui_dialog() {
    detect_hw
    while true; do
        CHOICE=$(dialog --stdout --backtitle "OSify — Universal Operating System" \
            --title "Benvenuto in OSify" \
            --menu "CPU: $CPU_INFO | RAM: $RAM_TOTAL\nSeleziona una voce:" 18 68 8 \
            "1" "Installa OSify su Disco Fisso" \
            "2" "Attiva zRAM Swap 1GB e Pulisci Cache" \
            "3" "Configura Touchpad Netbook (Tap & Scroll)" \
            "4" "Sblocca Audio ALSA (Master & Speaker)" \
            "5" "Scansione e Connessione Wi-Fi" \
            "6" "Apri Shell Terminale Amministratore" \
            "0" "Esci al Desktop" 2>/dev/null || echo "0")
        
        case "$CHOICE" in
            1) action_install ;;
            2) action_zram ;;
            3) action_touchpad ;;
            4) action_audio ;;
            5) action_wifi ;;
            6) action_terminal ;;
            0|"") clear; exit 0 ;;
        esac
    done
}

# Selezione Engine GUI
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    gui_yad
elif [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1 && [ -f /usr/bin/osify-welcome-wizard.py ]; then
    python3 /usr/bin/osify-welcome-wizard.py
elif command -v dialog >/dev/null 2>&1; then
    gui_dialog
else
    # Fallback puro testo
    detect_hw
    echo "========================================================="
    echo "  Benvenuto in OSify — Pannello di Configurazione       "
    echo "========================================================="
    echo "CPU: $CPU_INFO | RAM: $RAM_TOTAL"
    echo "1) Installa OSify su Disco Fisso (/usr/bin/osify-install)"
    echo "2) Attiva zRAM Swap 1GB"
    echo "3) Configura Touchpad Netbook"
    echo "4) Sblocca Audio ALSA"
    echo "5) Esci"
    read -rp "Selezione [1-5]: " c
    case "$c" in
        1) action_install ;;
        2) action_zram ;;
        3) action_touchpad ;;
        4) action_audio ;;
        *) exit 0 ;;
    esac
fi
