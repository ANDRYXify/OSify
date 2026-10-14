#!/usr/bin/env bash
# ==============================================================================
# OSify Power & Session Governor — Gestione Alimentazione e Spegnimento
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Centro decisionale per Spegnimento, Riavvio, Sospensione, Monitoraggio Batteria
# e Profilo Energetico (Risparmio Batteria vs Turbo Boost).
# ==============================================================================

set -euo pipefail

get_battery_status() {
    local b_path=""
    for b in /sys/class/power_supply/BAT* /sys/class/power_supply/battery; do
        if [ -d "$b" ]; then
            b_path="$b"
            break
        fi
    done

    if [ -n "$b_path" ] && [ -f "$b_path/capacity" ]; then
        local cap status
        cap="$(cat "$b_path/capacity" 2>/dev/null || echo "100")"
        status="$(cat "$b_path/status" 2>/dev/null || echo "Unknown")"
        echo "${cap}% (${status})"
    else
        echo "Alimentazione da Rete Elettrica (Nessuna Batteria)"
    fi
}

action_poweroff() {
    echo "[!] Spegnimento del sistema OSify..."
    sync
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl poweroff || sudo poweroff
    else
        sudo poweroff || sudo halt
    fi
}

action_reboot() {
    echo "[!] Riavvio del sistema OSify..."
    sync
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl reboot || sudo reboot
    else
        sudo reboot
    fi
}

action_suspend() {
    echo "[*] Sospensione RAM in corso..."
    sync
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl suspend
    elif command -v pm-suspend >/dev/null 2>&1; then
        sudo pm-suspend
    elif [ -w /sys/power/state ]; then
        echo mem | sudo tee /sys/power/state >/dev/null || true
    fi
}

action_logout() {
    echo "[*] Chiusura della sessione utente..."
    if command -v openbox >/dev/null 2>&1; then
        openbox --exit || pkill -u "$USER" openbox || true
    fi
    pkill -u "$USER" -f xinit || true
}

action_profile() {
    local prof="${1:-powersave}"
    if [ "$prof" = "turbo" ]; then
        echo "[+] Attivazione Profilo Turbo Prestazioni..."
        if [ -x /usr/bin/osify-autotune ]; then
            sudo /usr/bin/osify-autotune --turbo 2>/dev/null || true
        fi
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
        echo "[OK] Profilo Turbo Prestazioni Attivo."
    else
        echo "[+] Attivazione Profilo Risparmio Energetico..."
        echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
        if [ -x /usr/bin/osify-brightness ]; then
            /usr/bin/osify-brightness set 40 2>/dev/null || true
        fi
        echo "[OK] Profilo Risparmio Energetico Attivo."
    fi
}

launch_gui() {
    local bat
    bat="$(get_battery_status)"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local choice
        choice="$(yad --list --title="Gestione Alimentazione OSify" \
            --text="<b>Stato Batteria / Corrente:</b> ${bat}\nSeleziona l'azione desiderata:" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=440 --height=320 --center \
            --column="Opzione" --column="Descrizione" \
            "Spegni" "Arresta completamente il sistema in sicurezza" \
            "Riavvia" "Riavvia il computer" \
            "Sospendi" "Metti in standby a basso consumo energetico" \
            "Termina Sessione" "Esci dal desktop corrente" \
            "Risparmio Batteria" "Abilita CPU Powersave e ottimizza la durata" \
            "Turbo Prestazioni" "Massima velocita CPU e reattivita estrema" \
            --button="Conferma:0" --button="Annulla:1" 2>/dev/null || echo "")"
        
        local selected
        selected="$(echo "$choice" | cut -d'|' -f1)"

        case "$selected" in
            Spegni) action_poweroff ;;
            Riavvia) action_reboot ;;
            Sospendi) action_suspend ;;
            "Termina Sessione") action_logout ;;
            "Risparmio Batteria") action_profile powersave ;;
            "Turbo Prestazioni") action_profile turbo ;;
        esac
    else
        echo "=== Gestione Alimentazione OSify ==="
        echo "Stato: $bat"
        echo "1) Spegni"
        echo "2) Riavvia"
        echo "3) Sospendi"
        echo "4) Logout"
        echo "5) Risparmio Batteria"
        echo "6) Turbo Prestazioni"
        read -r -p "Scegli un'opzione [1-6]: " opt
        case "$opt" in
            1) action_poweroff ;;
            2) action_reboot ;;
            3) action_suspend ;;
            4) action_logout ;;
            5) action_profile powersave ;;
            6) action_profile turbo ;;
            *) echo "Annullato." ;;
        esac
    fi
}

case "${1:-gui}" in
    gui|--gui)
        launch_gui
        ;;
    poweroff|shutdown)
        action_poweroff
        ;;
    reboot)
        action_reboot
        ;;
    suspend)
        action_suspend
        ;;
    logout)
        action_logout
        ;;
    status)
        get_battery_status
        ;;
    powersave)
        action_profile powersave
        ;;
    turbo)
        action_profile turbo
        ;;
    *)
        echo "Uso: $0 {gui|poweroff|reboot|suspend|logout|status|powersave|turbo}"
        exit 1
        ;;
esac
