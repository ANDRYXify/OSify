#!/usr/bin/env bash
# ==============================================================================
# OSify Smart Calculator — Calcolatrice di Sistema Grafica
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta operazioni aritmetiche, percentuali, potenze, radici e conversioni.
# ==============================================================================

set -euo pipefail

calculate_expr() {
    local expr="$1"
    # Sostituisci x o X con * e virgole con punti
    expr="$(echo "$expr" | tr 'xX' '**' | tr ',' '.')"
    python3 -c "
import math
try:
    res = eval('$expr', {'__builtins__': None}, {'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'pi': math.pi, 'pow': pow})
    print(res)
except Exception as e:
    print('Errore Sintassi')
" 2>/dev/null || (echo "$expr" | bc -l 2>/dev/null || echo "Errore")
}

launch_gui() {
    local last_res="0"
    local expr=""

    while true; do
        if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
            local input
            input="$(yad --form --title="Calcolatrice OSify" \
                --text="<b>Calcolatrice Rapida di Sistema</b>\nUltimo Risultato: <b><big>${last_res}</big></b>" \
                --window-icon="/usr/share/pixmaps/osify-hub.png" \
                --width=380 --center \
                --field="Espressione da Calcolare:":ENTRY "$expr" \
                --button="Calcola:0" --button="Azzera:2" --button="Chiudi:1" 2>/dev/null || echo "")"
            local ret=$?

            if [ "$ret" -eq 1 ] || [ "$ret" -eq 252 ]; then
                break
            elif [ "$ret" -eq 2 ]; then
                last_res="0"
                expr=""
                continue
            fi

            expr="$(echo "$input" | cut -d'|' -f1)"
            if [ -n "$expr" ]; then
                last_res="$(calculate_expr "$expr")"
            fi
        else
            echo "=== Calcolatrice OSify ==="
            read -r -p "Inserisci espressione (es. 25 * 4 + 10): " expr
            if [ -n "$expr" ]; then
                calculate_expr "$expr"
            fi
            break
        fi
    done
}

if [ $# -gt 0 ]; then
    calculate_expr "$*"
else
    launch_gui
fi
