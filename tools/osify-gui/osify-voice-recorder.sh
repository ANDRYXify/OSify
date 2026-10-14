#!/usr/bin/env bash
# ==============================================================================
# OSify Voice Recorder & Mic Tester — Registratore Vocale & Collaudo Microfono
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Registrazione memo vocali, appunti audio e diagnostica ingresso microfono/cuffie
# basata su ALSA nativo a bassissima latenza, con riproduzione e verifica immediata.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-audio.png"
SAVE_DIR="${HOME:-/home/osify}/Musica/Registrazioni"
mkdir -p "$SAVE_DIR"
LAST_RECORDING="/tmp/.osify_last_voice_test.wav"

record_clip() {
    local duration="${1:-5}"
    local outfile="${2:-$LAST_RECORDING}"

    echo "==> Avvio registrazione per $duration secondi su ALSA (default input)..."
    if command -v arecord >/dev/null 2>&1; then
        arecord -f cd -t wav -d "$duration" -q "$outfile" 2>/dev/null || \
        arecord -f dat -t wav -d "$duration" -q "$outfile" 2>/dev/null || \
        arecord -d "$duration" -q "$outfile" 2>/dev/null
    elif command -v ffmpeg >/dev/null 2>&1; then
        ffmpeg -y -f alsa -i default -t "$duration" "$outfile" >/dev/null 2>&1
    else
        echo "[!] Nessun registratore audio ALSA (arecord o ffmpeg) disponibile."
        return 1
    fi
    echo "[OK] Registrazione salvata: $outfile"
}

play_clip() {
    local clip="${1:-$LAST_RECORDING}"
    if [ ! -f "$clip" ]; then
        echo "[!] Nessun file audio trovato da riprodurre: $clip"
        return 1
    fi

    echo "==> Riproduzione in corso: $clip"
    if command -v aplay >/dev/null 2>&1; then
        aplay -q "$clip" 2>/dev/null
    elif command -v mpv >/dev/null 2>&1; then
        mpv --no-video "$clip" >/dev/null 2>&1
    elif command -v ffplay >/dev/null 2>&1; then
        ffplay -nodisp -autoexit "$clip" >/dev/null 2>&1
    fi
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {record [sec] [file.wav]|play [file.wav]}"
        return 1
    fi

    while true; do
        local choice
        choice="$(yad --form \
            --title="OSify — Registratore Vocale & Test Microfono" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Registratore Vocale & Collaudo Audio</b></big>\nVerifica il microfono integrato o registra un promemoria audio:" \
            --field="Durata Registrazione:CB" "Test Rapido (5 secondi)!Memo Vocale (15 secondi)!Registrazione Estesa (60 secondi)" \
            --button="Avvia Registrazione:0" \
            --button="Ascolta Ultima:2" \
            --button="Chiudi:1" \
            --width=480 --center 2>/dev/null || echo "1")"
        local ret=$?

        if [ $ret -eq 2 ]; then
            if [ -f "$LAST_RECORDING" ]; then
                play_clip "$LAST_RECORDING"
            else
                yad --info --title="Nessun Audio" --text="Nessuna registrazione recente presente. Registra prima un test!" --center 2>/dev/null || true
            fi
            continue
        elif [ $ret -ne 0 ]; then
            break
        fi

        local sel_dur
        sel_dur="$(echo "$choice" | awk -F'|' '{print $1}')"
        local dur=5
        case "$sel_dur" in
            *60*) dur=60 ;;
            *15*) dur=15 ;;
            *)    dur=5 ;;
        esac

        local ts
        ts="$(date +%Y%m%d_%H%M%S)"
        local perm_file="$SAVE_DIR/Nota_Vocale_${ts}.wav"

        # Notifica visiva registrazione in corso
        (
            record_clip "$dur" "$LAST_RECORDING"
            cp "$LAST_RECORDING" "$perm_file" 2>/dev/null || true
        ) | yad --progress --pulsate --title="Registrazione in Corso" \
            --text="Parla vicino al microfono... ($dur secondi)" \
            --auto-close --center 2>/dev/null || true

        # Chiede se ascoltare subito
        yad --question --title="Registrazione Completata" \
            --text="<big><b>Registrazione Vocale Conclusa!</b></big>\n\nIl file e stato archiviato in:\n<b>$perm_file</b>\n\nVuoi ascoltare subito la traccia registrata per verificare il microfono?" \
            --button="Ascolta:0" --button="OK:1" --center 2>/dev/null && play_clip "$LAST_RECORDING" || true
    done
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui
        else
            echo "Display X11 non rilevato."
        fi
        ;;
    record)
        record_clip "${2:-5}" "${3:-$LAST_RECORDING}"
        ;;
    play)
        play_clip "${2:-$LAST_RECORDING}"
        ;;
    *)
        echo "Uso: $0 {gui|record [sec] [file]|play [file]}"
        exit 1
        ;;
esac
