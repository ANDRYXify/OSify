#!/usr/bin/env bash
# ==============================================================================
# OSify Laptop Lid & Sleep Governor — Gestore Coperchio e Sospensione
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Configura il comportamento del laptop alla chiusura dello schermo:
# - Sospensione profonda in RAM (Sleep)
# - Spegnimento solo schermo (ideale per ascolto musica o download a coperchio chiuso)
# - Ignora chiusura schermo
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-power.png"
CONF_FILE="/etc/osify/lid_action.conf"
mkdir -p "$(dirname "$CONF_FILE")"

get_current_action() {
    if [ -f "$CONF_FILE" ]; then
        cat "$CONF_FILE"
    else
        echo "suspend"
    fi
}

set_action() {
    local action="${1:-suspend}"
    echo "$action" > "$CONF_FILE"

    # Aggiornamento systemd logind se presente
    if [ -f /etc/systemd/logind.conf ]; then
        local sys_act="suspend"
        case "$action" in
            ignore) sys_act="ignore" ;;
            blank)  sys_act="lock" ;;
            *)      sys_act="suspend" ;;
        esac
        sudo sed -i "s/^#\?HandleLidSwitch=.*/HandleLidSwitch=$sys_act/" /etc/systemd/logind.conf 2>/dev/null || true
    fi

    # Script ACPI SliTaz
    local acpi_lid="/etc/acpi/lid.sh"
    if [ -d /etc/acpi ]; then
        cat <<EOF | sudo tee "$acpi_lid" >/dev/null
#!/bin/sh
ACTION="\$(cat $CONF_FILE 2>/dev/null || echo suspend)"
case "\$ACTION" in
    suspend)
        echo mem > /sys/power/state 2>/dev/null || pm-suspend
        ;;
    blank)
        xset dpms force off 2>/dev/null || true
        ;;
    ignore)
        exit 0
        ;;
esac
EOF
        sudo chmod +x "$acpi_lid" 2>/dev/null || true
    fi

    echo "[OK] Azione chiusura coperchio impostata su: $action"
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {suspend|blank|ignore|status}"
        return 1
    fi

    local cur
    cur="$(get_current_action)"
    local cur_desc="Sospendi Laptop in RAM (Consigliato per batteria)"
    case "$cur" in
        blank)  cur_desc="Spegni solo lo Schermo (Musica e download continuano)" ;;
        ignore) cur_desc="Non fare Nulla (Schermo e sistema restano accesi)" ;;
    esac

    local choice
    choice="$(yad --form \
        --title="OSify — Gestore Coperchio Laptop" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Azione alla Chiusura dello Schermo</b></big>\nImposta cosa deve fare il portatile quando abbassi il coperchio:\n(Stato attuale: <b>$cur_desc</b>)" \
        --field="Azione Chiusura Schermo:CB" "Sospendi Laptop in RAM (Standby)!Spegni solo lo Schermo (PC resta attivo per musica/download)!Non fare Nulla" \
        --button="Salva:0" \
        --button="gtk-cancel:1" \
        --width=480 --center 2>/dev/null || echo "")"

    if [ -n "$choice" ]; then
        local sel
        sel="$(echo "$choice" | awk -F'|' '{print $1}')"
        case "$sel" in
            *Spegni*) set_action "blank" ;;
            *Nulla*)  set_action "ignore" ;;
            *)        set_action "suspend" ;;
        esac
        yad --info --title="Impostazione Salvata" \
            --text="Comportamento coperchio laptop aggiornato con successo!" --center 2>/dev/null || true
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
    suspend|sleep)
        set_action "suspend"
        ;;
    blank|screenoff)
        set_action "blank"
        ;;
    ignore|nothing)
        set_action "ignore"
        ;;
    status)
        echo "Lid Action: $(get_current_action)"
        ;;
    *)
        echo "Uso: $0 {gui|suspend|blank|ignore|status}"
        exit 1
        ;;
esac
