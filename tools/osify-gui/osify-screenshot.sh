#!/usr/bin/env bash
# ==============================================================================
# OSify Instant Screenshot Engine — Cattura Schermo a Latenza Zero
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

TARGET_DIR="${HOME}/Immagini"
mkdir -p "$TARGET_DIR"
TIMESTAMP="$(date +'%Y-%m-%d_%H-%M-%S')"
OUT_FILE="${TARGET_DIR}/Schermata_${TIMESTAMP}.png"

capture_fullscreen() {
    local delay="${1:-0}"
    if [ "$delay" -gt 0 ]; then
        sleep "$delay"
    fi

    if command -v scrot >/dev/null 2>&1; then
        scrot "$OUT_FILE"
    elif command -v import >/dev/null 2>&1; then
        import -window root "$OUT_FILE"
    elif command -v xwd >/dev/null 2>&1; then
        xwd -root -silent | (convert xwd:- "$OUT_FILE" 2>/dev/null || cat > "${TARGET_DIR}/Schermata_${TIMESTAMP}.xwd")
    else
        echo "[!] Nessun tool di cattura X11 disponibile (scrot/import/xwd)."
        return 1
    fi

    if [ -f "$OUT_FILE" ]; then
        echo "[✓] Schermata salvata con successo in: $OUT_FILE"
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "OSify Screenshot" "Schermata salvata in: $(basename "$OUT_FILE")" -i /usr/share/pixmaps/osify-appearance.png || true
        fi
    fi
}

capture_window() {
    if command -v scrot >/dev/null 2>&1; then
        scrot -u "$OUT_FILE"
    elif command -v import >/dev/null 2>&1; then
        import "$OUT_FILE"
    else
        capture_fullscreen
    fi

    if [ -f "$OUT_FILE" ]; then
        echo "[✓] Finestra catturata con successo in: $OUT_FILE"
    fi
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local choice
        choice="$(yad --list --title="Cattura Schermo OSify" \
            --text="<b>Scegli la modalita di cattura:</b>" \
            --window-icon="/usr/share/pixmaps/osify-appearance.png" \
            --width=380 --height=220 --center \
            --column="Modalita" --column="Descrizione" \
            "Schermo Intero" "Cattura istantaneamente l'intero desktop" \
            "Ritardo 5s" "Attendi 5 secondi prima di catturare" \
            "Finestra Attiva" "Fai click sulla finestra da catturare" \
            --button="Cattura:0" --button="Annulla:1" 2>/dev/null || echo "")"
        
        local mode
        mode="$(echo "$choice" | cut -d'|' -f1)"
        case "$mode" in
            "Schermo Intero") capture_fullscreen 0 ;;
            "Ritardo 5s") capture_fullscreen 5 ;;
            "Finestra Attiva") capture_window ;;
        esac
    else
        capture_fullscreen 0
    fi
}

case "${1:-instant}" in
    instant|--now)
        capture_fullscreen 0
        ;;
    gui|--gui)
        launch_gui
        ;;
    window)
        capture_window
        ;;
    delay)
        capture_fullscreen "${2:-5}"
        ;;
    *)
        echo "Uso: $0 {instant|gui|window|delay <sec>}"
        exit 1
        ;;
esac
