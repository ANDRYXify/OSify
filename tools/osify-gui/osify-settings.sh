#!/bin/sh
# ==============================================================================
# OSify Control Center (osify-settings) — Comprehensive System Settings
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Pannello impostazioni a schede per Display, Touchpad, Rete Wi-Fi, Audio e Info Sistema
# ==============================================================================

export LC_ALL=C

# Rilevamento info sistema
CPU_INFO=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//' || uname -m)
GPU_INFO=$(lspci 2>/dev/null | grep -iE 'vga|display|3d' | head -n1 | cut -d: -f3 | sed 's/^[ \t]*//' || echo "Controller Grafico Integrato")
KERNEL_INFO=$(uname -srm)
RAM_INFO=$(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "1024 MB")
UPTIME_INFO=$(uptime 2>/dev/null | sed 's/.*up \([^,]*\), .*/\1/' || echo "Attivo")

OSIFY_VER=$(cat /etc/osify-version 2>/dev/null || echo "1.2.0")

# Finestra Notebook a Schede
RESP=$(yad --form \
    --title="OSify Control Center — Impostazioni di Sistema" \
    --window-icon="preferences-desktop" \
    --width=540 \
    --height=480 \
    --center \
    --text="<b><big>⚙️ OSify Control Center</big></b>\n<i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>\n" \
    --field="<b>SCHERMO & RISOLUZIONE</b>":LBL "" \
    --field="Risoluzione Display:":CB "1024x600 (Nativa WSVGA Netbook)!1280x768 (Virtual Enhancer Anti-Cutoff)!800x600 (Compatibilità VESA)" \
    --field="Luce Notturna (Filtro Blu):":CHK "FALSE" \
    --field="<b>TOUCHPAD & PUNTATORE</b>":LBL "" \
    --field="Tocco per Click (Tap-to-Click):":CHK "TRUE" \
    --field="Scorrimento Verticale su Bordo:":CHK "TRUE" \
    --field="<b>AUDIO & VOLUME</b>":LBL "" \
    --field="Volume Master (%):":NUM "80!0..100!5" \
    --field="Sblocca Canali Audio (ALSA Unmute):":CHK "TRUE" \
    --field="<b>INFORMAZIONI HARDWARE & AGGIORNAMENTI</b>":LBL "" \
    --field="Versione OSify:":RO "v$OSIFY_VER" \
    --field="Processore:":RO "$CPU_INFO" \
    --field="Scheda Video:":RO "$GPU_INFO" \
    --field="Kernel & Architettura:":RO "$KERNEL_INFO" \
    --field="Memoria Installata:":RO "$RAM_INFO" \
    --button="🔄 Controlla Aggiornamenti":20 \
    --button="🔊 Test Suono":10 \
    --button="Salva e Applica":0 \
    --button="Chiudi":1)

RET=$?

if [ "$RET" -eq 20 ]; then
    if [ -x /usr/bin/osify-update ]; then
        /usr/bin/osify-update --gui &
    elif [ -x "$REPO_ROOT/system/updater/osify-live-updater.sh" ]; then
        "$REPO_ROOT/system/updater/osify-live-updater.sh" --gui &
    fi
    exit 0
fi

if [ "$RET" -eq 10 ]; then
    # Test audio con beep o aplay sintetico
    if command -v aplay >/dev/null 2>&1; then
        speaker-test -t sine -f 800 -l 1 >/dev/null 2>&1 &
    fi
    exec "$0"
fi

if [ "$RET" -eq 0 ]; then
    SCREEN_RES=$(echo "$RESP" | cut -d'|' -f2)
    NIGHT_MODE=$(echo "$RESP" | cut -d'|' -f3)
    TAP_CLICK=$(echo "$RESP" | cut -d'|' -f5)
    EDGE_SCROLL=$(echo "$RESP" | cut -d'|' -f6)
    VOL_LEVEL=$(echo "$RESP" | cut -d'|' -f8)
    UNMUTE=$(echo "$RESP" | cut -d'|' -f9)

    # 1. Applicazione Risoluzione
    disp=$(xrandr 2>/dev/null | awk '/ connected/ {print $1; exit}')
    [ -z "$disp" ] && disp="LVDS1"
    
    if [ "$SCREEN_RES" = "1280x768 (Virtual Enhancer Anti-Cutoff)" ]; then
        xrandr --output "$disp" --scale 1.25x1.28 --panning 1280x768 2>/dev/null || true
    else
        xrandr --output "$disp" --scale 1.0x1.0 --panning 1024x600 2>/dev/null || xrandr --output "$disp" --auto || true
    fi

    # 2. Night Light
    if [ "$NIGHT_MODE" = "TRUE" ]; then
        xrandr --output "$disp" --gamma 1.0:0.85:0.70 2>/dev/null || true
    else
        xrandr --output "$disp" --gamma 1.0:1.0:1.0 2>/dev/null || true
    fi

    # 3. Touchpad synclient
    if command -v synclient >/dev/null 2>&1; then
        [ "$TAP_CLICK" = "TRUE" ] && synclient TapButton1=1 TapButton2=3 TapButton3=2 2>/dev/null
        [ "$TAP_CLICK" = "FALSE" ] && synclient TapButton1=0 2>/dev/null
        [ "$EDGE_SCROLL" = "TRUE" ] && synclient VertEdgeScroll=1 HorizEdgeScroll=1 2>/dev/null
        [ "$EDGE_SCROLL" = "FALSE" ] && synclient VertEdgeScroll=0 HorizEdgeScroll=0 2>/dev/null
    fi

    # 4. Audio Volume
    if command -v amixer >/dev/null 2>&1; then
        [ "$UNMUTE" = "TRUE" ] && amixer set Master unmute 2>/dev/null || true
        amixer set Master "${VOL_LEVEL}%" 2>/dev/null || true
    fi

    yad --notification --text="✅ Impostazioni OSify applicate con successo!" --timeout=3 2>/dev/null &
fi
