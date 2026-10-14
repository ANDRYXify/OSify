#!/usr/bin/env bash
# ==============================================================================
# OSify Touchpad & Precision Pointer Manager
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Calibrazione fine per touchpad Synaptics, ALPS, Elantech e mouse USB/Bluetooth.
# ==============================================================================

set -euo pipefail

apply_touchpad_settings() {
    local tap="${1:-1}"
    local speed="${2:-0}"
    local palm="${3:-1}"

    if command -v synclient >/dev/null 2>&1; then
        synclient TapButton1="$tap" 2>/dev/null || true
        synclient TapButton2=3 2>/dev/null || true
        synclient TapButton3=2 2>/dev/null || true
        synclient PalmDetect="$palm" 2>/dev/null || true
        synclient VertEdgeScroll=1 2>/dev/null || true
        synclient VertTwoFingerScroll=1 2>/dev/null || true
    fi

    # Fallback con xinput
    if command -v xinput >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        for dev in $(xinput list --name-only 2>/dev/null | grep -iE "touchpad|synaptics|alps|glidepoint"); do
            xinput set-prop "$dev" "libinput Tapping Enabled" "$tap" 2>/dev/null || true
            xinput set-prop "$dev" "libinput Natural Scrolling Enabled" 0 2>/dev/null || true
            xinput set-prop "$dev" "libinput Accel Speed" "$speed" 2>/dev/null || true
        done
    fi

    # Protezione digitazione con syndaemon
    if [ "$palm" -eq 1 ] && command -v syndaemon >/dev/null 2>&1; then
        pkill -f syndaemon 2>/dev/null || true
        syndaemon -i 0.8 -t -K -d 2>/dev/null || true
    fi

    echo "[✓] Configurazione Touchpad & Puntatore applicata."
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local res
        res="$(yad --form --title="Calibrazione Touchpad & Mouse OSify" \
            --text="<b>Impostazioni Touchpad e Puntatore</b>" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=440 --center \
            --field="Tocca per fare Click (Tap to Click):CHK" "TRUE" \
            --field="Protezione Palmo durante la Digitazione:CHK" "TRUE" \
            --field="Velocita Puntatore (-1.0 a 1.0):NUM" "0.0!-1.0..1.0!0.1" \
            --button="Applica:0" --button="Chiudi:1" 2>/dev/null || echo "")"
        
        if [ -n "$res" ]; then
            local tap palm spd
            tap="$(echo "$res" | cut -d'|' -f1)"
            palm="$(echo "$res" | cut -d'|' -f2)"
            spd="$(echo "$res" | cut -d'|' -f3)"

            local tap_v=0; local palm_v=0
            if [ "$tap" = "TRUE" ]; then tap_v=1; fi
            if [ "$palm" = "TRUE" ]; then palm_v=1; fi

            apply_touchpad_settings "$tap_v" "$spd" "$palm_v"
        fi
    else
        apply_touchpad_settings 1 0 1
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    auto|default) apply_touchpad_settings 1 0 1 ;;
    *) echo "Uso: $0 {gui|auto}" ;;
esac
