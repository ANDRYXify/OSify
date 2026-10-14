#!/usr/bin/env bash
# ==============================================================================
# OSify Accessibility & Visual Aid — Accessibilita & Aiuti Visivi
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Centro di controllo accessibilita: ingranditore schermo, scaling DPI testo,
# modalita ad alto contrasto e avvisi visivi per ipovedenti e schermi netbook compatti.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-appearance.png"
STATE_DIR="${HOME:-/root}/.config/osify"
mkdir -p "$STATE_DIR"

get_primary_output() {
    xrandr --current 2>/dev/null | grep " connected primary" | awk '{print $1}' || \
    xrandr --current 2>/dev/null | grep " connected" | awk '{print $1}' | head -n1
}

set_dpi_scale() {
    local dpi="${1:-96}"
    if command -v xrandr >/dev/null 2>&1; then
        xrandr --dpi "$dpi" 2>/dev/null || true
    fi
    if command -v xrdb >/dev/null 2>&1; then
        echo "Xft.dpi: $dpi" | xrdb -merge 2>/dev/null || true
    fi
    echo "$dpi" > "$STATE_DIR/dpi_scale"
    echo "[OK] DPI schermo impostato a $dpi"
}

set_magnification() {
    local level="${1:-1.0}"
    local out
    out="$(get_primary_output)"

    if [ -z "$out" ]; then
        echo "[!] Nessun output video rilevato."
        return 1
    fi

    if [ "$level" = "1.0" ] || [ "$level" = "off" ]; then
        xrandr --output "$out" --scale 1x1 --panning 0x0 2>/dev/null || true
        echo "off" > "$STATE_DIR/magnifier_state"
        echo "[OK] Ingranditore disattivato (Scala 1:1)."
    elif [ "$level" = "1.25" ]; then
        # Scala 0.8x0.8 equivale a zoom 1.25x
        xrandr --output "$out" --scale 0.8x0.8 2>/dev/null || true
        echo "1.25" > "$STATE_DIR/magnifier_state"
        echo "[OK] Ingranditore attivato: Zoom 1.25x"
    elif [ "$level" = "1.5" ]; then
        # Scala 0.67x0.67 equivale a zoom 1.5x
        xrandr --output "$out" --scale 0.67x0.67 2>/dev/null || true
        echo "1.5" > "$STATE_DIR/magnifier_state"
        echo "[OK] Ingranditore attivato: Zoom 1.5x"
    fi
}

toggle_high_contrast() {
    local state_file="$STATE_DIR/high_contrast"
    local cur="off"
    [ -f "$state_file" ] && cur="$(cat "$state_file")"

    if [ "$cur" = "off" ]; then
        if command -v xcalib >/dev/null 2>&1; then
            xcalib -invert -alter 2>/dev/null || true
        fi
        echo "on" > "$state_file"
        echo "[OK] Modalita Alto Contrasto Attivata"
    else
        if command -v xcalib >/dev/null 2>&1; then
            xcalib -clear 2>/dev/null || true
        fi
        echo "off" > "$state_file"
        echo "[OK] Modalita Alto Contrasto Disattivata"
    fi
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {dpi <96|120|144>|zoom <1.0|1.25|1.5>|contrast|status}"
        return 1
    fi

    local cur_dpi="96"
    [ -f "$STATE_DIR/dpi_scale" ] && cur_dpi="$(cat "$STATE_DIR/dpi_scale")"

    local choice
    choice="$(yad --form \
        --title="OSify — Accessibilita & Aiuti Visivi" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Centro Accessibilita & Comfort Visivo</b></big>\nConfigura la dimensione del testo e gli ingranditori per facilitare la lettura:" \
        --field="Dimensione Testo & Interfaccia:CB" "Normale (DPI 96 - Default)!Grande +25% (DPI 120)!Molto Grande +50% (DPI 144 - Consigliato Ipovedenti)" \
        --field="Ingranditore Schermo (Zoom):CB" "Disattivato (Normale 100%)!Zoom Moderato (125%)!Zoom Elevato (150%)" \
        --field="Inverti Colori / Alto Contrasto:CHK" FALSE \
        --button="Applica Modifiche:0" \
        --button="gtk-cancel:1" \
        --width=480 --center 2>/dev/null || echo "")"

    if [ -n "$choice" ]; then
        local dpi_raw zoom_raw contrast_raw
        dpi_raw="$(echo "$choice" | awk -F'|' '{print $1}')"
        zoom_raw="$(echo "$choice" | awk -F'|' '{print $2}')"
        contrast_raw="$(echo "$choice" | awk -F'|' '{print $3}')"

        # 1. Applicazione DPI
        case "$dpi_raw" in
            *Molto*) set_dpi_scale 144 ;;
            *Grande*) set_dpi_scale 120 ;;
            *)        set_dpi_scale 96 ;;
        esac

        # 2. Applicazione Zoom
        case "$zoom_raw" in
            *150%*) set_magnification "1.5" ;;
            *125%*) set_magnification "1.25" ;;
            *)      set_magnification "1.0" ;;
        esac

        # 3. Contrasto
        if [ "$contrast_raw" = "TRUE" ]; then
            toggle_high_contrast
        fi
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
    dpi)
        set_dpi_scale "${2:-96}"
        ;;
    zoom|magnifier)
        set_magnification "${2:-1.0}"
        ;;
    contrast)
        toggle_high_contrast
        ;;
    status)
        echo "DPI: $(cat "$STATE_DIR/dpi_scale" 2>/dev/null || echo 96)"
        echo "Zoom: $(cat "$STATE_DIR/magnifier_state" 2>/dev/null || echo 1.0)"
        echo "Contrasto: $(cat "$STATE_DIR/high_contrast" 2>/dev/null || echo off)"
        ;;
    *)
        echo "Uso: $0 {gui|dpi <96|120|144>|zoom <1.0|1.25|1.5>|contrast|status}"
        exit 1
        ;;
esac
