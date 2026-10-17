#!/usr/bin/env bash
# ==============================================================================
# OSify Keyboard Layout Switcher — Selettore Rapido Mappatura Tastiera
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

set_layout() {
    local layout="$1"
    if command -v setxkbmap >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        setxkbmap "$layout"
        echo "[[OK]] Mappatura tastiera impostata su: $layout"
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Tastiera OSify" "Layout tastiera impostato su: ${layout^^}" -i /usr/share/pixmaps/osify-settings.png || true
        fi
    else
        echo "[!] Server grafico X11 o setxkbmap non attivo."
    fi
}

get_current_layout() {
    if command -v setxkbmap >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        setxkbmap -query 2>/dev/null | awk '/layout/ {print $2}' || echo "it"
    else
        echo "it"
    fi
}

launch_gui() {
    local cur
    cur="$(get_current_layout)"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local choice
        choice="$(yad --list --title="Mappatura Tastiera OSify" \
            --text="<b>Layout Corrente:</b> ${cur^^}\nSeleziona la mappatura per la tua tastiera:" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=380 --height=260 --center \
            --column="Codice" --column="Nazione / Layout" \
            "it" "Italiana (Standard QWERTY)" \
            "us" "Inglese USA (QWERTY)" \
            "gb" "Inglese UK (QWERTY)" \
            "de" "Tedesca (QWERTZ)" \
            "fr" "Francese (AZERTY)" \
            "es" "Spagnola (QWERTY)" \
            --button="Applica:0" --button="Annulla:1" 2>/dev/null || echo "")"
        
        local selected
        selected="$(echo "$choice" | cut -d'|' -f1)"
        if [ -n "$selected" ]; then
            set_layout "$selected"
        fi
    else
        echo "Layout corrente: $cur"
        echo "Uso: $0 {it|us|gb|de|fr|es}"
    fi
}

case "${1:-gui}" in
    gui|--gui)
        launch_gui ;;
    get)
        get_current_layout ;;
    it|us|gb|de|fr|es)
        set_layout "$1" ;;
    *)
        echo "Uso: $0 {gui|get|it|us|gb|de|fr|es}"
        exit 1 ;;
esac
