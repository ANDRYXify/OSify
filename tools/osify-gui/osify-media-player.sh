#!/usr/bin/env bash
# ==============================================================================
# OSify Media Player — Riproduttore Audio & Video Leggero a Bassa Latenza
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Ottimizzato sia per netbook a bassa potenza (Atom / i686) che per PC moderni.
# ==============================================================================

set -euo pipefail

TARGET_MEDIA="${1:-}"

play_file() {
    local f="$1"
    if [ ! -f "$f" ]; then
        echo "[!] File multimediale non trovato: $f"
        return 1
    fi

    # 1. Prova MPV con accelerazione e tuning per schermi vintage
    if command -v mpv >/dev/null 2>&1; then
        exec mpv --geometry=80%x80% --autofit=900x600 "$f"
    elif command -v ffplay >/dev/null 2>&1; then
        exec ffplay -autoexit -nodisp -volume 80 "$f"
    elif command -v vlc >/dev/null 2>&1; then
        exec vlc "$f"
    elif command -v mplayer >/dev/null 2>&1; then
        exec mplayer "$f"
    elif command -v aplay >/dev/null 2>&1 && [[ "$f" == *.wav ]]; then
        exec aplay "$f"
    else
        echo "[!] Nessun decoder audio/video disponibile. Installa mpv o ffmpeg."
    fi
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local file_chosen
        file_chosen="$(yad --file-selection --title="OSify Media Player — Scegli Traccia Audio o Video" \
            --window-icon="/usr/share/pixmaps/osify-audio.png" \
            --width=520 --height=340 --center 2>/dev/null || echo "")"
        
        if [ -n "$file_chosen" ] && [ -f "$file_chosen" ]; then
            play_file "$file_chosen"
        fi
    else
        echo "Uso: $0 <file_audio_o_video>"
    fi
}

if [ -n "$TARGET_MEDIA" ]; then
    play_file "$TARGET_MEDIA"
else
    launch_gui
fi
