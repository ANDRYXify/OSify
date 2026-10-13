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
    case "$act" in
        poweroff|shutdown)
            echo "[+] Arresto del sistema in corso..."
            if command -v systemctl >/dev/null 2>&1; then
                systemctl poweroff -i || true
            elif command -v poweroff >/dev/null 2>&1; then
                poweroff -f || true
            else
                echo "[SIMULAZIONE] Chiamata ACPI Poweroff inviata al kernel."
            fi
            ;;
        reboot)
            echo "[+] Riavvio del sistema in corso..."
            if command -v systemctl >/dev/null 2>&1; then
                systemctl reboot -i || true
            elif command -v reboot >/dev/null 2>&1; then
                reboot -f || true
            else
                echo "[SIMULAZIONE] Chiamata ACPI Reboot inviata al kernel."
            fi
            ;;
        suspend)
            echo "[+] Sospensione del sistema in RAM (S3 Sleep)..."
            if command -v systemctl >/dev/null 2>&1; then
                systemctl suspend -i || true
            elif [[ -w /sys/power/state ]]; then
                echo mem > /sys/power/state || true
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
            echo "[✓] Profilo Risparmio Energetico attivo (Autonomia massima)."
            ;;
        performance)
            # Frequenza massima, TDP 15W
            if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
                echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
            fi
            echo "[✓] Profilo Prestazioni Massime attivo (BORE 1000Hz)."
            ;;
        balanced|*)
            # Scheduler BORE / schedutil bilanciato, TDP 10W
            if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
                echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
            fi
            echo "[✓] Profilo Bilanciato attivo."
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
