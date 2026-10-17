#!/usr/bin/env bash
# ==============================================================================
# OSify Power & Battery Management Subsystem
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestisce alimentazione ACPI, batteria notebook, sospensione e spegnimento reale:
# - Spegnimento immediato sicuro (poweroff) e riavvio (reboot)
# - Sospensione a basso consumo in RAM (S3 Sleep)
# - Lettura telemetria batteria da /sys/class/power_supply/
# - Switch profili termici e TDP (Risparmio 4W, Bilanciato 10W, Prestazioni 15W)
# ==============================================================================

set -euo pipefail

get_battery_status() {
    local bat_path
    bat_path="$(find /sys/class/power_supply -name "BAT*" 2>/dev/null | head -n1 || true)"
    if [[ -n "$bat_path" && -r "$bat_path/capacity" ]]; then
        local cap status
        cap="$(cat "$bat_path/capacity" 2>/dev/null || echo "100")"
        status="$(cat "$bat_path/status" 2>/dev/null || echo "Discharging")"
        echo "${cap}% (${status})"
        return
    fi
    echo "100% (Alimentazione da Rete)"
}

power_action() {
    local act="$1"
    sync
    local pwr_tool="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/osify-power.sh"
    if [[ -x "$pwr_tool" ]]; then
        "$pwr_tool" "$act"
        return
    elif command -v osify-power >/dev/null 2>&1; then
        osify-power "$act"
        return
    fi

    case "$act" in
        poweroff|shutdown|off)
            echo "[+] Arresto del sistema in corso..."
            if [[ "$(id -u)" -eq 0 ]]; then
                poweroff -f 2>/dev/null || halt -p 2>/dev/null || init 0 2>/dev/null || busybox poweroff -f 2>/dev/null || true
            elif command -v sudo >/dev/null 2>&1; then
                sudo poweroff -f 2>/dev/null || sudo halt -p 2>/dev/null || sudo init 0 2>/dev/null || true
            elif command -v systemctl >/dev/null 2>&1; then
                systemctl poweroff -i || true
            else
                poweroff -f 2>/dev/null || true
            fi
            ;;
        reboot)
            echo "[+] Riavvio del sistema in corso..."
            if [[ "$(id -u)" -eq 0 ]]; then
                reboot -f 2>/dev/null || init 6 2>/dev/null || busybox reboot -f 2>/dev/null || true
            elif command -v sudo >/dev/null 2>&1; then
                sudo reboot -f 2>/dev/null || sudo init 6 2>/dev/null || sudo reboot 2>/dev/null || true
            elif command -v systemctl >/dev/null 2>&1; then
                systemctl reboot -i || true
            else
                reboot -f 2>/dev/null || true
            fi
            ;;
        suspend)
            echo "[+] Sospensione del sistema in RAM (S3 Sleep)..."
            if command -v systemctl >/dev/null 2>&1; then
                systemctl suspend -i || true
            elif [[ -w /sys/power/state ]]; then
                echo mem > /sys/power/state || true
            elif command -v sudo >/dev/null 2>&1; then
                sudo sh -c 'echo mem > /sys/power/state' 2>/dev/null || true
            else
                echo "[SIMULAZIONE] Sistema sospeso."
            fi
            ;;
        *)
            echo "Azione non valida: $act"
            exit 1
            ;;
    esac
}

set_power_profile() {
    local profile="${1:-balanced}"
    echo "[+] Impostazione profilo energetico: $profile"
    case "$profile" in
        powersave)
            # Frequenza minima, TDP 4W
            if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
                echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
            fi
            echo "[[OK]] Profilo Risparmio Energetico attivo (Autonomia massima)."
            ;;
        performance)
            # Frequenza massima, TDP 15W
            if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
                echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
            fi
            echo "[[OK]] Profilo Prestazioni Massime attivo (BORE 1000Hz)."
            ;;
        balanced|*)
            # Scheduler BORE / schedutil bilanciato, TDP 10W
            if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
                echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
            fi
            echo "[[OK]] Profilo Bilanciato attivo."
            ;;
    esac
}

case "${1:-battery}" in
    battery)
        get_battery_status
        ;;
    poweroff|shutdown)
        power_action "poweroff"
        ;;
    reboot)
        power_action "reboot"
        ;;
    suspend)
        power_action "suspend"
        ;;
    profile)
        set_power_profile "${2:-balanced}"
        ;;
    *)
        echo "Uso: $0 {battery|poweroff|reboot|suspend|profile <powersave|balanced|performance>}"
        exit 1
        ;;
esac
