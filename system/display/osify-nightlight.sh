#!/usr/bin/env bash
# ==============================================================================
# OSify Night Light — Filtro Luce Blu & Modalita Riposo Visivo Notturna
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Regola la temperatura colore dello schermo tramite correzione gamma hardware/software,
# riducendo l'affaticamento oculare nelle ore serali senza alcun impatto su CPU o RAM.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-appearance.png"
STATE_FILE="/tmp/.osify_nightlight_state"

get_active_outputs() {
    xrandr --current 2>/dev/null | grep " connected" | awk '{print $1}'
}

apply_profile() {
    local profile="${1:-normal}"
    local gamma="1.0:1.0:1.0"
    local desc="Normale (Nessun filtro)"

    case "$profile" in
        off|normal|day)
            gamma="1.0:1.0:1.0"
            desc="Luce Naturale (Giorno)"
            echo "off" > "$STATE_FILE"
            ;;
        soft|warm|evening)
            # ~4500K: riduzione lieve componente blu
            gamma="1.0:0.85:0.70"
            desc="Luce Calda Rilassante (Sera)"
            echo "warm" > "$STATE_FILE"
            ;;
        deep|candle|night)
            # ~3200K: forte attenuazione blu per ambienti bui
            gamma="1.0:0.70:0.50"
            desc="Modalita Notturna Profonda (Buio)"
            echo "night" > "$STATE_FILE"
            ;;
        amber|ultra)
            # ~2400K: filtro ambra ultra-riposante
            gamma="1.0:0.55:0.35"
            desc="Filtro Ambra Riposo Intenso"
            echo "amber" > "$STATE_FILE"
            ;;
        *)
            gamma="1.0:1.0:1.0"
            desc="Normale"
            echo "off" > "$STATE_FILE"
            ;;
    esac

    local applied=0
    for out in $(get_active_outputs); do
        if xrandr --output "$out" --gamma "$gamma" 2>/dev/null; then
            applied=1
        fi
    done

    if [ "$applied" -eq 1 ]; then
        echo "[OK] Profilo Luce Notturna applicato: $desc ($gamma)"
    else
        echo "[!] Impossibile applicare gamma xrandr."
    fi
}

toggle() {
    local cur="off"
    [ -f "$STATE_FILE" ] && cur="$(cat "$STATE_FILE")"
    if [ "$cur" = "off" ]; then
        apply_profile "warm"
    else
        apply_profile "off"
    fi
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {off|warm|night|amber|toggle}"
        return 1
    fi

    local cur="off"
    [ -f "$STATE_FILE" ] && cur="$(cat "$STATE_FILE")"

    local choice
    choice="$(yad --form \
        --title="OSify — Luce Notturna & Riposo Oculare" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Filtro Luce Blu & Protezione Visiva</b></big>\nRegola la temperatura dello schermo per prevenire l'affaticamento degli occhi:" \
        --field="Profilo Colore:CB" "Disattivato (Colori Naturali 6500K)!Sera Calda (Lieve attenuazione blu ~4500K)!Notte Profonda (Forte riduzione blu ~3200K)!Filtro Ambra (Massimo riposo al buio ~2400K)" \
        --button="Applica:0" \
        --button="gtk-cancel:1" \
        --width=450 --center 2>/dev/null || echo "")"

    if [ -n "$choice" ]; then
        local sel
        sel="$(echo "$choice" | awk -F'|' '{print $1}')"
        case "$sel" in
            *Disattivato*) apply_profile "off" ;;
            *Sera*)        apply_profile "warm" ;;
            *Notte*)       apply_profile "night" ;;
            *Ambra*)       apply_profile "amber" ;;
            *)             apply_profile "off" ;;
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
    off|normal|day)
        apply_profile "off"
        ;;
    warm|evening|soft)
        apply_profile "warm"
        ;;
    night|deep|candle)
        apply_profile "night"
        ;;
    amber|ultra)
        apply_profile "amber"
        ;;
    toggle)
        toggle
        ;;
    status)
        if [ -f "$STATE_FILE" ]; then
            echo "Stato: $(cat "$STATE_FILE")"
        else
            echo "Stato: off"
        fi
        ;;
    *)
        echo "Uso: $0 {gui|off|warm|night|amber|toggle|status}"
        exit 1
        ;;
esac
