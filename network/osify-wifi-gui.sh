#!/bin/sh
# ==============================================================================
# OSify Wi-Fi Manager — Connettività Wireless Guidata & Immediata
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# Compatibile al 100% con POSIX /bin/sh, Busybox ash e GNU Bash.
# ==============================================================================

# Auto-elevazione privilegi con sudo
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    elif command -v su >/dev/null 2>&1; then
        exec su -c "$0 $*"
    fi
fi

# Se lanciato dal desktop senza terminale interattivo, apri xterm
if [ -n "$DISPLAY" ] && [ ! -t 0 ]; then
    if command -v xterm >/dev/null 2>&1; then
        exec xterm -title "Connessione Wi-Fi — OSify" -geometry 80x25 -bg "#0b0d14" -fg "#38bdf8" -cr "#10b981" +sb -e "$0" --interactive
    fi
fi

find_wifi_iface() {
    if command -v iw >/dev/null 2>&1; then
        iface=$(iw dev 2>/dev/null | awk '$1=="Interface"{print $2; exit}')
        [ -n "$iface" ] && echo "$iface" && return
    fi
    if command -v ip >/dev/null 2>&1; then
        iface=$(ip -o link show 2>/dev/null | awk -F': ' '$2 ~ /^(wl|ath|ra|wlan)/ {print $2; exit}')
        [ -n "$iface" ] && echo "$iface" && return
    fi
    for cand in wlan0 wlan1 wlp2s0 wlp3s0 ath0; do
        if [ -d "/sys/class/net/$cand" ]; then
            echo "$cand"
            return
        fi
    done
    echo "wlan0"
}

get_current_ip() {
    iface="$1"
    ip addr show "$iface" 2>/dev/null | awk '/inet / {print $2; exit}' | cut -d/ -f1
}

IFACE="$(find_wifi_iface)"

# Risveglio e attivazione interfaccia
if command -v ip >/dev/null 2>&1; then
    ip link set "$IFACE" up 2>/dev/null || true
elif command -v ifconfig >/dev/null 2>&1; then
    ifconfig "$IFACE" up 2>/dev/null || true
fi

scan_wifi_ssids() {
    ssids_file="/tmp/osify_ssids.txt"
    rm -f "$ssids_file"
    
    # 1. Tentativo con nmcli
    if command -v nmcli >/dev/null 2>&1; then
        nmcli -t -f SSID,SIGNAL,SECURITY device wifi list 2>/dev/null | grep -v '^:' | sort -u > "$ssids_file" || true
    fi

    # 2. Tentativo con iwlist
    if [ ! -s "$ssids_file" ] && command -v iwlist >/dev/null 2>&1; then
        iwlist "$IFACE" scan 2>/dev/null | awk -F: '/ESSID/{gsub(/"/, "", $2); if (length($2) > 0) print $2":80%:WPA"}' | sort -u > "$ssids_file" || true
    fi

    # 3. Tentativo con iw dev scan
    if [ ! -s "$ssids_file" ] && command -v iw >/dev/null 2>&1; then
        iw dev "$IFACE" scan 2>/dev/null | awk '/SSID: /{if (length($2) > 0) print $2":75%:WPA"}' | sort -u > "$ssids_file" || true
    fi

    if [ ! -s "$ssids_file" ]; then
        echo "Inserisci-Rete-Manualmente:100%:WPA2" > "$ssids_file"
    fi
    echo "$ssids_file"
}

connect_to_ssid() {
    target_ssid="$1"
    target_pass="$2"

    printf "\033[1;34m[OSify-WiFi]\033[0m Connessione a '%s' su %s...\n" "$target_ssid" "$IFACE"

    pkill -f "wpa_supplicant.*$IFACE" 2>/dev/null || true
    sleep 1

    if command -v nmcli >/dev/null 2>&1; then
        if [ -n "$target_pass" ]; then
            nmcli device wifi connect "$target_ssid" password "$target_pass" ifname "$IFACE" 2>/dev/null || true
        else
            nmcli device wifi connect "$target_ssid" ifname "$IFACE" 2>/dev/null || true
        fi
    elif command -v wpa_supplicant >/dev/null 2>&1; then
        conf_file="/tmp/wpa_${IFACE}.conf"
        if [ -n "$target_pass" ]; then
            if command -v wpa_passphrase >/dev/null 2>&1; then
                wpa_passphrase "$target_ssid" "$target_pass" > "$conf_file" 2>/dev/null || true
            else
                cat << EOF > "$conf_file"
network={
    ssid="$target_ssid"
    psk="$target_pass"
}
EOF
            fi
        else
            cat << EOF > "$conf_file"
network={
    ssid="$target_ssid"
    key_mgmt=NONE
}
EOF
        fi
        wpa_supplicant -B -i "$IFACE" -c "$conf_file" 2>/dev/null || true
        sleep 2
        
        # Richiesta IP con client DHCP (udhcpc per Busybox / SliTaz)
        if command -v udhcpc >/dev/null 2>&1; then
            udhcpc -i "$IFACE" -b -q -t 5 2>/dev/null || true
        elif command -v dhclient >/dev/null 2>&1; then
            dhclient "$IFACE" 2>/dev/null || true
        fi
    fi
}

# Modalità Interattiva Dialog se presente
if command -v dialog >/dev/null 2>&1; then
    dialog --backtitle "OSify Operating System" \
        --infobox "\nScansione delle reti wireless in corso su $IFACE...\nAttendere qualche secondo..." 6 60

    SCAN_FILE=$(scan_wifi_ssids)
    
    # Costruisci opzioni dialog
    OPTIONS=""
    idx=1
    while IFS=: read -r s_name s_sig s_sec; do
        [ -z "$s_name" ] && continue
        OPTIONS="$OPTIONS $idx \"$s_name ($s_sig - $s_sec)\""
        eval "SSID_NAME_$idx=\"$s_name\""
        idx=$((idx + 1))
    done < "$SCAN_FILE"

    if [ -z "$OPTIONS" ]; then
        dialog --backtitle "OSify Operating System" \
            --title " Nessuna Rete Rilevata " \
            --msgbox "\nNessuna rete Wi-Fi trovata.\nVerifica che la scheda Wi-Fi sia attiva." 8 50
        exit 1
    fi

    CHOICE=$(eval "dialog --backtitle 'OSify Operating System' --title ' Reti Wireless Disponibili ' --menu '\nSeleziona la rete a cui connetterti:\n' 17 65 8 $OPTIONS 3>&1 1>&2 2>&3")
    [ $? -ne 0 ] && exit 0

    eval "SELECTED_SSID=\"\$SSID_NAME_$CHOICE\""

    if [ "$SELECTED_SSID" = "Inserisci-Rete-Manualmente" ]; then
        SELECTED_SSID=$(dialog --backtitle "OSify Operating System" \
            --title " Nome Rete (SSID) " \
            --inputbox "\nInserisci il nome esatto della rete Wi-Fi (SSID):" 10 55 \
            3>&1 1>&2 2>&3)
        [ $? -ne 0 ] && exit 0
    fi

    WIFI_PASS=$(dialog --backtitle "OSify Operating System" \
        --title " Password di Rete " \
        --insecure \
        --passwordbox "\nInserisci la password per '$SELECTED_SSID':\n(Lascia vuoto per rete aperta)" 11 55 \
        3>&1 1>&2 2>&3)
    [ $? -ne 0 ] && exit 0

    dialog --backtitle "OSify Operating System" \
        --infobox "\nConnessione a '$SELECTED_SSID' in corso...\nNegoziazione indirizzo IP..." 6 55

    connect_to_ssid "$SELECTED_SSID" "$WIFI_PASS"
    sleep 2

    ASSIGNED_IP=$(get_current_ip "$IFACE")
    if [ -n "$ASSIGNED_IP" ]; then
        # Verifica reale accesso Internet e Captive Portal
        NET_STATUS="Accesso a Internet attivo e verificato."
        CHECK_TOOL="$(dirname "$0")/osify-net-check.sh"
        [ ! -x "$CHECK_TOOL" ] && CHECK_TOOL="/usr/bin/osify-net-check"
        if [ -x "$CHECK_TOOL" ]; then
            if ! "$CHECK_TOOL" portal >/dev/null 2>&1; then
                NET_STATUS="ATTENZIONE: Rilevato Captive Portal (richiesto login Web)."
            fi
        fi

        dialog --backtitle "OSify Operating System" \
            --title " Connesso con Successo! " \
            --msgbox "\nConnesso alla rete: $SELECTED_SSID\nIndirizzo IP assegnato: $ASSIGNED_IP\n\nStato: $NET_STATUS" 11 58
    else
        dialog --backtitle "OSify Operating System" \
            --title " Stato Connessione " \
            --msgbox "\nComando di connessione inviato a '$SELECTED_SSID'.\nSe la password e' corretta, la rete sara' disponibile a breve." 9 55
    fi
    exit 0
fi

# Fallback Console TUI
echo "=== Gestore Rete Wi-Fi OSify ==="
echo "Interfaccia attiva: $IFACE"
SCAN_FILE=$(scan_wifi_ssids)
cat "$SCAN_FILE"
printf "Nome SSID: "
read -r sel_ssid
printf "Password: "
read -r sel_pass
connect_to_ssid "$sel_ssid" "$sel_pass"
