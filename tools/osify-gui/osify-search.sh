#!/usr/bin/env bash
# ==============================================================================
# OSify Instant File Search — Ricerca File Globale a Latenza Zero
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

search_files() {
    local query="$1"
    local search_path="${2:-$HOME}"

    find "$search_path" -iname "*${query}*" 2>/dev/null | head -n 50
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local q
        q="$(yad --entry --title="Cerca File — OSify" \
            --text="Inserisci il nome del file da cercare (es. appunti, .png, fattura):" \
            --window-icon="/usr/share/pixmaps/osify-files.png" \
            --width=420 --center 2>/dev/null || echo "")"

        if [ -n "$q" ]; then
            local results
            results="$(search_files "$q" "$HOME")"

            if [ -z "$results" ]; then
                yad --info --title="Cerca File" --text="Nessun file trovato corrispondente a: <b>$q</b>" --center || true
                return 0
            fi

            local chosen
            chosen="$(yad --list --title="Risultati Ricerca: $q" \
                --text="File trovati nella cartella personale:" \
                --window-icon="/usr/share/pixmaps/osify-files.png" \
                --width=680 --height=380 --center \
                --column="Percorso File" $results \
                --button="Apri File:0" --button="Mostra nella Cartella:2" --button="Chiudi:1" 2>/dev/null || echo "")"
            local ret=$?

            local sel_f
            sel_f="$(echo "$chosen" | cut -d'|' -f1)"

            if [ -n "$sel_f" ] && [ -e "$sel_f" ]; then
                if [ "$ret" -eq 0 ]; then
                    if command -v xdg-open >/dev/null 2>&1; then
                        xdg-open "$sel_f" &
                    else
                        pcmanfm "$sel_f" &
                    fi
                elif [ "$ret" -eq 2 ]; then
                    pcmanfm "$(dirname "$sel_f")" &
                fi
            fi
        fi
    else
        echo "Uso: $0 <nome_file>"
    fi
}

if [ $# -gt 0 ]; then
    search_files "$1" "${2:-$HOME}"
else
    launch_gui
fi
