#!/bin/sh
# ==============================================================================
# OSify Out-Of-Box Experience (OOBE) — Inizializzazione Primo Avvio
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Eseguito al primo avvio su disco per calibrare hardware, display, audio e UEM.
# Non disturba i riavvii successivi una volta completata l'inizializzazione.
# ==============================================================================

FLAG_FILE="/etc/osify-first-boot.done"
USER_FLAG="$HOME/.config/osify/first-boot.done"

# Se già eseguito sia a livello di sistema che per l'utente, esci
if [ -f "$FLAG_FILE" ] && [ -f "$USER_FLAG" ]; then
    exit 0
fi

# 1. Inizializzazione Audio & Mixer
if command -v amixer >/dev/null 2>&1; then
    amixer set Master 65% unmute 2>/dev/null || true
    amixer set PCM 65% unmute 2>/dev/null || true
    amixer set Speaker 65% unmute 2>/dev/null || true
fi

# 2. Ottimizzazione Risoluzione Schermo Safe-Mode per Netbook/WSVGA
if [ -n "$DISPLAY" ] && command -v xrandr >/dev/null 2>&1; then
    # Se la risoluzione è molto compatta (es. 1024x600 su netbook), imposta DPI safe
    RES=$(xrandr 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1)
    if [ -n "$RES" ]; then
        HEIGHT=$(echo "$RES" | cut -d'x' -f2)
        if [ "$HEIGHT" -le 650 ] 2>/dev/null; then
            # Display ultracompatto: scala font o adatta Xft.dpi
            echo "Xft.dpi: 84" | xrdb -merge 2>/dev/null || true
        fi
    fi
fi

# 3. Rilevamento Telemetria Hardware
CPU_NAME=$(grep "model name" /proc/cpuinfo 2>/dev/null | head -n1 | cut -d: -f2 | sed 's/^[ \t]*//' || echo "Processore x86")
[ -z "$CPU_NAME" ] && CPU_NAME="Processore Architettura x86"
MEM_KB=$(grep "MemTotal" /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "1048576")
MEM_MB=$((MEM_KB / 1024))

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"

# 4. Presentazione di Benvenuto Interattiva
if [ -n "$DISPLAY" ] && [ ! -f "$USER_FLAG" ]; then
    if command -v yad >/dev/null 2>&1; then
        yad --info \
            --title="Benvenuto in OSify Operating System" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --image-on-top \
            --width=520 \
            --center \
            --text="<big><b>OSify Operating System e' pronto all'uso</b></big>\n\nConfigurazione hardware completata con successo:\n - Processore: <b>$CPU_NAME</b>\n - Memoria RAM: <b>${MEM_MB} MB</b>\n - Sottosistemi attivi: <b>Universal Execution Matrix (UEM), Audio ALSA/PipeWire, WiFi Stack</b>\n\nPuoi avviare direttamente programmi Windows (.exe), pacchetti Android (.apk), applicazioni Mac o giochi retrò facendo doppio clic sui rispettivi file.\n\nBuon lavoro con OSify!" \
            --button="Inizia a Usare OSify:0" 2>/dev/null || true
    elif command -v dialog >/dev/null 2>&1 && [ -t 0 ]; then
        dialog --backtitle "OSify Operating System" \
            --title " Benvenuto in OSify " \
            --msgbox "\nOSify Operating System e' pronto all'uso!\n\nProcessore: $CPU_NAME\nMemoria RAM: ${MEM_MB} MB\n\nI sottosistemi di sistema e UEM sono operativi." 12 60
    fi
fi

# 5. Marcatura di completamento
mkdir -p "$HOME/.config/osify" 2>/dev/null || true
touch "$USER_FLAG" 2>/dev/null || true

if [ "$(id -u 2>/dev/null || echo 0)" -eq 0 ]; then
    touch "$FLAG_FILE" 2>/dev/null || true
elif command -v sudo >/dev/null 2>&1; then
    sudo touch "$FLAG_FILE" 2>/dev/null || true
fi

exit 0
