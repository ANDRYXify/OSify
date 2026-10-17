#!/usr/bin/env bash
# ==============================================================================
# OSify Thermal Governor & Fan Telemetry — Protezione Termica Hardware
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

CRITICAL_TEMP=80
WARNING_TEMP=72

get_cpu_temp() {
    local temp=0
    # 1. Prova thermal_zone
    for tz in /sys/class/thermal/thermal_zone*/temp; do
        if [ -f "$tz" ]; then
            local raw
            raw="$(cat "$tz" 2>/dev/null || echo 0)"
            if [ "$raw" -gt 1000 ]; then raw=$(( raw / 1000 )); fi
            if [ "$raw" -gt "$temp" ]; then temp="$raw"; fi
        fi
    done

    # 2. Prova hwmon coretemp
    if [ "$temp" -eq 0 ]; then
        for hw in /sys/class/hwmon/hwmon*/temp*_input; do
            if [ -f "$hw" ]; then
                local raw
                raw="$(cat "$hw" 2>/dev/null || echo 0)"
                if [ "$raw" -gt 1000 ]; then raw=$(( raw / 1000 )); fi
                if [ "$raw" -gt "$temp" ]; then temp="$raw"; fi
            fi
        done
    fi

    # Fallback sicuro
    if [ "$temp" -eq 0 ]; then temp=45; fi
    echo "$temp"
}

check_thermal() {
    local cur
    cur="$(get_cpu_temp)"
    echo "Temperatura CPU Attuale: ${cur}°C"

    if [ "$cur" -ge "$CRITICAL_TEMP" ]; then
        echo "[!] ALLERTA CRITICA: Temperatura ${cur}°C supera la soglia sicura (${CRITICAL_TEMP}°C)!"
        echo "[+] Applicazione governor powersave di emergenza per raffreddare la CPU..."
        echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
        if command -v notify-send >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
            notify-send "ALLERTA TEMPERATURA" "CPU a ${cur}°C! Protezione termica attivata." -u critical || true
        fi
    elif [ "$cur" -ge "$WARNING_TEMP" ]; then
        echo "[*] Avviso: Temperatura elevata (${cur}°C). Monitoraggio in corso."
    else
        echo "[[OK]] Temperatura nei limiti ottimali di esercizio."
    fi
}

launch_gui() {
    local cur
    cur="$(get_cpu_temp)"
    local status="Normale (Raffreddamento Ottimale)"
    if [ "$cur" -ge "$CRITICAL_TEMP" ]; then status="Critica (Troppo Caldo)"; elif [ "$cur" -ge "$WARNING_TEMP" ]; then status="Elevata"; fi

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        yad --info --title="Monitor Termico OSify" \
            --text="<b>Telemetria Termica Hardware CPU</b>\n\nTemperatura Attuale: <b><big>${cur}°C</big></b>\nStato Termico: <b>${status}</b>\n\nSoglia Attenzione: ${WARNING_TEMP}°C | Soglia Critica: ${CRITICAL_TEMP}°C" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=420 --center \
            --button="Aggiorna:2" --button="Chiudi:0" >/dev/null 2>&1 || true
        local ret=$?
        if [ "$ret" -eq 2 ]; then launch_gui; fi
    else
        check_thermal
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    get) get_cpu_temp ;;
    check) check_thermal ;;
    *) echo "Uso: $0 {gui|get|check}" ;;
esac
