#!/usr/bin/env bash
# ==============================================================================
# OSify Screen Brightness Governor — Regolazione Intelligente Luminosita
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta sia hardware sysfs (/sys/class/backlight/*) per netbook e portatili,
# sia fallback universale xrandr software gamma per display esterni e VM.
# ==============================================================================

set -euo pipefail

SYSFS_BACKLIGHT=""
for b in /sys/class/backlight/*; do
    if [ -d "$b" ] && [ -w "$b/brightness" ]; then
        SYSFS_BACKLIGHT="$b"
        break
    fi
done

get_brightness() {
    if [ -n "$SYSFS_BACKLIGHT" ] && [ -f "$SYSFS_BACKLIGHT/max_brightness" ]; then
        local cur max
        cur="$(cat "$SYSFS_BACKLIGHT/brightness" 2>/dev/null || echo 100)"
        max="$(cat "$SYSFS_BACKLIGHT/max_brightness" 2>/dev/null || echo 100)"
        if [ "$max" -gt 0 ]; then
            echo $(( (cur * 100) / max ))
            return 0
        fi
    fi

    # Fallback xrandr
    if command -v xrandr >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local bright
        bright="$(xrandr --verbose 2>/dev/null | grep -m1 -i "Brightness" | awk '{print $2}' || echo "1.0")"
        python3 -c "print(int(float('${bright:-1.0}') * 100))" 2>/dev/null || echo "100"
        return 0
    fi

    echo "100"
}

set_brightness() {
    local pct="${1:-100}"
    if [ "$pct" -lt 10 ]; then pct=10; fi
    if [ "$pct" -gt 100 ]; then pct=100; fi

    local applied=0

    # 1. Prova sysfs backlight
    if [ -n "$SYSFS_BACKLIGHT" ] && [ -f "$SYSFS_BACKLIGHT/max_brightness" ]; then
        local max val
        max="$(cat "$SYSFS_BACKLIGHT/max_brightness" 2>/dev/null || echo 100)"
        val=$(( (pct * max) / 100 ))
        if echo "$val" | sudo tee "$SYSFS_BACKLIGHT/brightness" >/dev/null 2>&1; then
            applied=1
        elif echo "$val" > "$SYSFS_BACKLIGHT/brightness" 2>/dev/null; then
            applied=1
        fi
    fi

    # 2. Fallback xrandr se sysfs non disponibile o fallito
    if [ "$applied" -eq 0 ] && command -v xrandr >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local output
        output="$(xrandr --current 2>/dev/null | grep " connected" | awk '{print $1}' | head -n1 || echo "")"
        if [ -n "$output" ]; then
            local ratio
            ratio="$(python3 -c "print(round($pct / 100.0, 2))" 2>/dev/null || echo "1.0")"
            xrandr --output "$output" --brightness "$ratio" 2>/dev/null || true
            applied=1
        fi
    fi

    echo "[OK] Luminosita schermo impostata al ${pct}%"
}

step_brightness() {
    local delta="$1"
    local cur
    cur="$(get_brightness)"
    local nxt=$(( cur + delta ))
    set_brightness "$nxt"
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "[!] YAD non disponibile. Uso terminale interattivo."
        return 1
    fi

    local cur
    cur="$(get_brightness)"
    local new_val
    new_val="$(yad --scale --title="Luminosita Schermo OSify" \
        --text="Regola la luminosita del display:" \
        --value="$cur" --min-value=10 --max-value=100 --step=5 \
        --window-icon="/usr/share/pixmaps/osify-appearance.png" \
        --width=360 --center 2>/dev/null || echo "")"

    if [ -n "$new_val" ]; then
        set_brightness "$new_val"
    fi
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui || get_brightness
        else
            get_brightness
        fi
        ;;
    get)
        get_brightness
        ;;
    set)
        set_brightness "${2:-100}"
        ;;
    up|+*)
        step_brightness 10
        ;;
    down|-*)
        step_brightness -10
        ;;
    *)
        echo "Uso: $0 {get|set <10-100>|up|down|gui}"
        exit 1
        ;;
esac
