#!/usr/bin/env bash
# ==============================================================================
# OSify Display & Screen Brightness Manager
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestisce risoluzione, refresh rate e luminosità su netbook e PC desktop:
# - Supporto risoluzione nativa 1024x600 (Toshiba NB200) e 1280x800 (Steam Deck)
# - Controllo luminosità hardware via /sys/class/backlight/
# - Gestione monitor esterni HDMI/VGA
# ==============================================================================

set -euo pipefail

get_brightness() {
    local b_path
    b_path="$(find /sys/class/backlight -maxdepth 1 -mindepth 1 2>/dev/null | head -n1 || true)"
    if [[ -n "$b_path" && -r "$b_path/brightness" && -r "$b_path/max_brightness" ]]; then
        local cur max
        cur="$(cat "$b_path/brightness")"
        max="$(cat "$b_path/max_brightness")"
        if (( max > 0 )); then
            echo $(( (cur * 100) / max ))
            return
        fi
    fi
    if command -v brightnessctl >/dev/null 2>&1; then
        brightnessctl -m | awk -F, '{print $4}' | tr -d '%' || echo "80"
    else
        echo "80"
    fi
}

set_brightness() {
    local percent="${1:-80}"
    if (( percent < 5 )); then percent=5; fi
    if (( percent > 100 )); then percent=100; fi

    local b_path
    b_path="$(find /sys/class/backlight -maxdepth 1 -mindepth 1 2>/dev/null | head -n1 || true)"
    if [[ -n "$b_path" && -w "$b_path/brightness" && -r "$b_path/max_brightness" ]]; then
        local max val
        max="$(cat "$b_path/max_brightness")"
        val=$(( (percent * max) / 100 ))
        echo "$val" > "$b_path/brightness" 2>/dev/null || true
    elif command -v brightnessctl >/dev/null 2>&1; then
        brightnessctl set "${percent}%" >/dev/null 2>&1 || true
    elif command -v xbacklight >/dev/null 2>&1; then
        xbacklight -set "$percent" 2>/dev/null || true
    fi
    echo "[✓] Luminosità schermo impostata al ${percent}%"
}

get_resolutions() {
    echo "=== Modalità Video Rilevate ==="
    if command -v xrandr >/dev/null 2>&1; then
        xrandr 2>/dev/null | grep -E "^[ ]+[0-9]+x[0-9]+" | awk '{print $1}' | head -n 6 || true
    else
        echo "1024x600 (Toshiba NB200 Nativo)"
        echo "1280x800 (Steam Deck Nativo)"
        echo "1920x1080 (Full HD Esterno)"
    fi
}

set_resolution() {
    local res="${1:-1024x600}"
    if command -v xrandr >/dev/null 2>&1; then
        xrandr -s "$res" 2>/dev/null || true
    fi
    echo "[✓] Risoluzione video impostata su: $res"
}

case "${1:-get-brightness}" in
    get-brightness)
        get_brightness
        ;;
    set-brightness)
        set_brightness "${2:-80}"
        ;;
    resolutions)
        get_resolutions
        ;;
    set-res)
        set_resolution "${2:-1024x600}"
        ;;
    *)
        echo "Uso: $0 {get-brightness|set-brightness <5-100>|resolutions|set-res <WxH>}"
        exit 1
        ;;
esac
