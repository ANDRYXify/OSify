#!/usr/bin/env bash
# ==============================================================================
# OSify Camera & Webcam Station — Fotocamera & Visualizzatore Webcam Integrata
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Visualizzazione stream webcam a bassa latenza, scatto istantaneo foto
# e registrazione video per netbook e portatili con webcam USB/UVC.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"
SAVE_DIR="${HOME:-/home/osify}/Immagini/Webcam"
mkdir -p "$SAVE_DIR"

detect_webcam() {
    local dev=""
    for v in /dev/video*; do
        if [ -c "$v" ]; then
            dev="$v"
            break
        fi
    done
    echo "$dev"
}

take_photo() {
    local dev="${1:-$(detect_webcam)}"
    if [ -z "$dev" ]; then
        echo "[!] Nessuna webcam trovata in /dev/video*."
        return 1
    fi

    local ts
    ts="$(date +%Y%m%d_%H%M%S)"
    local target="$SAVE_DIR/Foto_${ts}.jpg"

    echo "==> Scatto foto da $dev..."
    if command -v ffmpeg >/dev/null 2>&1; then
        ffmpeg -y -f v4l2 -i "$dev" -vframes 1 -q:v 2 "$target" >/dev/null 2>&1
    elif command -v fswebcam >/dev/null 2>&1; then
        fswebcam -d "$dev" -r 1280x720 --jpeg 90 -D 1 "$target" >/dev/null 2>&1
    else
        echo "[!] Nessun tool per scattare foto (ffmpeg o fswebcam) installato."
        return 1
    fi

    echo "[OK] Foto salvata con successo: $target"
    echo "$target"
}

view_webcam() {
    local dev="${1:-$(detect_webcam)}"
    if [ -z "$dev" ]; then
        echo "[!] Nessuna webcam trovata."
        return 1
    fi

    echo "==> Avvio streaming live webcam: $dev..."
    if command -v mpv >/dev/null 2>&1; then
        exec mpv av://v4l2:"$dev" --profile=low-latency --untimed --title="OSify Fotocamera Live" --geometry=800x600+100+100
    elif command -v ffplay >/dev/null 2>&1; then
        exec ffplay -f v4l2 -i "$dev" -vf "hflip" -window_title "OSify Fotocamera Live"
    elif command -v mplayer >/dev/null 2>&1; then
        exec mplayer tv:// -tv device="$dev"
    fi
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {view|photo}"
        return 1
    fi

    local dev
    dev="$(detect_webcam)"

    if [ -z "$dev" ]; then
        yad --info \
            --title="Nessuna Fotocamera" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Nessuna Webcam Rilevata</b></big>\n\nNon e stata rilevata alcuna webcam integrata o USB collegata.\nCollega una fotocamera USB o abilita il modulo UVC nel BIOS del computer." \
            --center 2>/dev/null || true
        return 0
    fi

    local choice
    choice="$(yad --form \
        --title="OSify — Fotocamera & Webcam" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Fotocamera e Webcam Integrata</b></big>\nDispositivo rilevato: <b>$dev</b>" \
        --field="Azione:CB" "Visualizza Fotocamera a Schermo!Scatta una Foto Istantanea" \
        --button="Avvia:0" \
        --button="Chiudi:1" \
        --width=460 --center 2>/dev/null || echo "")"

    if [ -n "$choice" ]; then
        local act
        act="$(echo "$choice" | awk -F'|' '{print $1}')"
        case "$act" in
            *Visualizza*)
                view_webcam "$dev"
                ;;
            *Scatta*)
                local pic
                pic="$(take_photo "$dev" | tail -n1)"
                yad --info --title="Foto Scattata" \
                    --text="<big><b>Foto Salvata con Successo!</b></big>\n\nSalvata in:\n<b>$pic</b>" \
                    --center 2>/dev/null || true
                ;;
        esac
    fi
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui
        else
            echo "Display X11 non rilevato."
        fi
        ;;
    view)
        view_webcam "${2:-}"
        ;;
    photo)
        take_photo "${2:-}"
        ;;
    status)
        local d
        d="$(detect_webcam)"
        if [ -n "$d" ]; then
            echo "Webcam: $d"
        else
            echo "Webcam: Non rilevata"
        fi
        ;;
    *)
        echo "Uso: $0 {gui|view|photo|status}"
        exit 1
        ;;
esac
