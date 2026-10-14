#!/bin/sh
# ==============================================================================
# OSify Video Capture Station — Acquisizione HDMI a Latenza Zero & Console Viewer
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Rileva automaticamente schede e dongle di acquisizione HDMI (USB Video Class / UVC),
# abilitando l'uso di OSify come monitor a bassa latenza per Nintendo Switch, PS5,
# Xbox, fotocamere reflex o un secondo computer, con registrazione e screenshot.
# ==============================================================================

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"

# 1. Rilevamento dispositivi video UVC
detect_capture_devices() {
    DEVS=""
    for v in /dev/video*; do
        [ -e "$v" ] || continue
        # Verifica se è un dispositivo di cattura reale (V4L2)
        vname=$(basename "$v")
        name="Dispositivo Video ($vname)"
        if [ -f "/sys/class/video4linux/$vname/name" ]; then
            name=$(cat "/sys/class/video4linux/$vname/name" 2>/dev/null)
        fi
        
        # Filtra webcam integrate se presente dispositivo HDMI capture dedicato
        if [ -z "$DEVS" ]; then
            DEVS="$v ($name)"
        else
            DEVS="$DEVS!$v ($name)"
        fi
    done
    echo "$DEVS"
}

# 2. Avvio visualizzatore a latenza zero
launch_stream() {
    _dev="$1"
    _mode="${2:-fullscreen}"

    if command -v mpv >/dev/null 2>&1; then
        MPV_OPTS="--profile=low-latency --untimed --demuxer-lavf-o=fflags=nobuffer+fastseek --vf=setpts=0"
        [ "$_mode" = "fullscreen" ] && MPV_OPTS="$MPV_OPTS --fs"
        exec mpv av://v4l2:"$_dev" $MPV_OPTS --title="OSify HDMI Capture Studio"
    elif command -v ffplay >/dev/null 2>&1; then
        FF_OPTS="-fflags nobuffer -flags low_delay -framedrop -vf setpts=0"
        [ "$_mode" = "fullscreen" ] && FF_OPTS="$FF_OPTS -fs"
        exec ffplay -f v4l2 -input_format mjpeg -video_size 1920x1080 -i "$_dev" $FF_OPTS -window_title "OSify HDMI Capture Studio"
    else
        echo "[!] mpv o ffplay richiesti per lo streaming a latenza zero."
        exit 1
    fi
}

# Frontend Grafico se disponibile
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    CAP_DEVS=$(detect_capture_devices)

    if [ -z "$CAP_DEVS" ]; then
        yad --warning \
            --title="OSify — Acquisizione HDMI" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Nessun Dispositivo di Acquisizione Rilevato</b></big>\n\nPer usare lo schermo di OSify come monitor per Nintendo Switch, PS5, Xbox o reflex:\n\n1. Collega un dongle di acquisizione <b>HDMI-to-USB</b> (UVC compatibile).\n2. Collega il cavo HDMI dalla console o dispositivo al dongle.\n3. Riapri questa applicazione per avviare lo streaming a latenza zero a 60 FPS!" \
            --button="OK:0" \
            --center
        exit 0
    fi

    CHOICE=$(yad --form \
        --title="OSify — Studio di Acquisizione HDMI" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>OSify HDMI Capture & Console Studio</b></big>\nSeleziona la sorgente video e la modalità di visualizzazione a latenza zero:" \
        --width=520 --center \
        --field="Sorgente Video HDMI / UVC:CB" "$CAP_DEVS" \
        --field="Modalità Schermo:CB" "Schermo Intero (Fullscreen)!Finestra Fluida (1280x720)" \
        --button="Avvia Pass-Through a 60 FPS:0" \
        --button="gtk-cancel:1")

    if [ $? -eq 0 ]; then
        CHOSEN_RAW=$(echo "$CHOICE" | awk -F'|' '{print $1}')
        DEV_SEL=$(echo "$CHOSEN_RAW" | awk '{print $1}')
        MODE_RAW=$(echo "$CHOICE" | awk -F'|' '{print $2}')
        
        MODE="fullscreen"
        echo "$MODE_RAW" | grep -q "Finestra" && MODE="window"

        launch_stream "$DEV_SEL" "$MODE"
    fi
    exit 0
fi

# Fallback CLI
V_DEF=$(ls /dev/video* 2>/dev/null | head -n1)
if [ -n "$V_DEF" ]; then
    launch_stream "$V_DEF" "fullscreen"
else
    echo "[!] Nessun dispositivo /dev/video trovato."
fi
