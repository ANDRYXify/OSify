#!/usr/bin/env bash
# ==============================================================================
# OSify Wi-Fi Hotspot & Tethering Station — Condivisione Connessione
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Trasforma il computer in un Access Point Wi-Fi per condividere la connessione
# cablata Ethernet verso smartphone, tablet e altri computer portatili.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-wifi.png"
STATE_FILE="/tmp/.osify_hotspot_active"

detect_wifi_card() {
    local iface=""
    for i in /sys/class/net/*; do
        local b
        b="$(basename "$i")"
        if [ -d "$i/wireless" ] || [ -d "$i/phy80211" ]; then
            iface="$b"
            break
        fi
    done
    echo "$iface"
}

start_hotspot() {
    local ssid="${1:-OSify-Hotspot}"
    local psk="${2:-osify1234}"
    local wlan
    wlan="$(detect_wifi_card)"

    if [ -z "$wlan" ]; then
        echo "[!] Nessuna scheda di rete wireless rilevata."
        return 1
    fi

    echo "==> Avvio Hotspot Wi-Fi su $wlan (SSID: $ssid)..."

    # Se NetworkManager / nmcli e disponibile
    if command -v nmcli >/dev/null 2>&1; then
        nmcli device wifi hotspot ifname "$wlan" ssid "$ssid" password "$psk" 2>/dev/null || true
    else
        # Modalita SoftAP minimale / routing con iptables
        ip link set "$wlan" up 2>/dev/null || true
        ip addr add 192.168.12.1/24 dev "$wlan" 2>/dev/null || true
        echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null || true
        iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
        iptables -A FORWARD -i "$wlan" -j ACCEPT 2>/dev/null || true
    fi

    echo "$ssid|$psk|$wlan" > "$STATE_FILE"
    echo "[OK] Hotspot Wi-Fi attivo: SSID='$ssid' (Password='$psk')"
}

stop_hotspot() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "[*] Nessun hotspot Wi-Fi attivo."
        return 0
    fi

    local wlan
    wlan="$(awk -F'|' '{print $3}' "$STATE_FILE" 2>/dev/null || detect_wifi_card)"

    if command -v nmcli >/dev/null 2>&1 && [ -n "$wlan" ]; then
        nmcli device disconnect "$wlan" 2>/dev/null || true
    fi

    rm -f "$STATE_FILE"
    echo "[OK] Hotspot Wi-Fi disattivato con successo."
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {start [ssid] [password]|stop|status}"
        return 1
    fi

    local wlan
    wlan="$(detect_wifi_card)"

    if [ -z "$wlan" ]; then
        yad --info --title="Nessun Wi-Fi" \
            --text="Nessuna scheda Wi-Fi trovata per generare l'Hotspot." \
            --center 2>/dev/null || true
        return 0
    fi

    local is_active=0
    [ -f "$STATE_FILE" ] && is_active=1

    if [ "$is_active" -eq 1 ]; then
        local cur_info
        cur_info="$(cat "$STATE_FILE")"
        local cur_ssid cur_psk
        cur_ssid="$(echo "$cur_info" | awk -F'|' '{print $1}')"
        cur_psk="$(echo "$cur_info" | awk -F'|' '{print $2}')"

        yad --question \
            --title="OSify — Hotspot Wi-Fi Attivo" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>L'Hotspot Wi-Fi e attualmente ATTIVO!</b></big>\n\nNome Rete (SSID): <b>$cur_ssid</b>\nPassword WPA2: <b>$cur_psk</b>\n\nVuoi disattivare l'hotspot e ripristinare il client Wi-Fi?" \
            --button="Spegni Hotspot:0" \
            --button="Mantieni Attivo:1" \
            --center 2>/dev/null && stop_hotspot || true
    else
        local choice
        choice="$(yad --form \
            --title="OSify — Hotspot Wi-Fi & Tethering" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Condividi Connessione Wi-Fi</b></big>\nConfigura i parametri dell'Hotspot per smartphone e altri dispositivi:" \
            --field="Nome Rete (SSID):" "OSify-Hotspot" \
            --field="Password di Sicurezza WPA2:" "osify1234" \
            --button="Attiva Hotspot:0" \
            --button="Annulla:1" \
            --width=450 --center 2>/dev/null || echo "")"

        if [ -n "$choice" ]; then
            local n_ssid n_psk
            n_ssid="$(echo "$choice" | awk -F'|' '{print $1}')"
            n_psk="$(echo "$choice" | awk -F'|' '{print $2}')"
            [ -z "$n_ssid" ] && n_ssid="OSify-Hotspot"
            [ -z "$n_psk" ] && n_psk="osify1234"

            start_hotspot "$n_ssid" "$n_psk"
            yad --info --title="Hotspot Attivo" \
                --text="<big><b>Hotspot Wi-Fi Avviato!</b></big>\n\nPuoi ora connettere i tuoi dispositivi a:\nSSID: <b>$n_ssid</b>\nPassword: <b>$n_psk</b>" \
                --center 2>/dev/null || true
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
    start)
        start_hotspot "${2:-OSify-Hotspot}" "${3:-osify1234}"
        ;;
    stop)
        stop_hotspot
        ;;
    status)
        if [ -f "$STATE_FILE" ]; then
            echo "Hotspot: Attivo ($(cat "$STATE_FILE"))"
        else
            echo "Hotspot: Inattivo"
        fi
        ;;
    *)
        echo "Uso: $0 {gui|start [ssid] [psk]|stop|status}"
        exit 1
        ;;
esac
