#!/bin/sh
# ==============================================================================
# OSify Wi-Fi Manager — Connettività Wireless Guidata & Immediata
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Compatibile al 100% con POSIX /bin/sh, Busybox ash e GNU Bash.
# Supporta interfaccia interattiva dialog o modalità TUI console pura.
# ==============================================================================

set -e

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
    
    if command -v nmcli >/dev/null 2>&1; then
        nmcli -t -f SSID,SIGNAL,SECURITY device wifi list 2>/dev/null | grep -v '^:' | sort -u > "$ssids_file" || true
    elif command -v iwlist >/dev/null 2>&1; then
        iwlist "$IFACE" scan 2>/dev/null | awk -F: '/ESSID/{gsub(/"/, "", $2); if (length($2) > 0) print $2":80%:WPA"}' | sort -u > "$ssids_file" || true
    fi

    if [ ! -s "$ssids_file" ]; then
        # Se non ci sono reti o la scansione è vuota, aggiungiamo opzione manuale
        echo "Rete-Nascosta-o-Manuale:100%:WPA2" > "$ssids_file"
    fi
    echo "$ssids_file"
}

connect_to_ssid() {
    target_ssid="$1"
    target_pass="$2"

    printf "\033[1;34m[OSify-WiFi]\033[0m Connessione a '%s' su %s...\n" "$target_ssid" "$IFACE"

    # Termina istanze precedenti di wpa_supplicant su questa interfaccia
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
        
        # Richiesta DHCP
        if command -v udhcpc >/dev/null 2>&1; then
            udhcpc -i "$IFACE" -n -q -t 5 2>/dev/null || true
        elif command -v dhclient >/dev/null 2>&1; then
            dhclient -1 "$IFACE" 2>/dev/null || true
        fi
    fi

    # Configurazione DNS ad alte prestazioni e privacy (Cloudflare 1.1.1.1 e Quad9 9.9.9.9)
    if [ -w /etc/resolv.conf ]; then
        cat << 'EOF' > /etc/resolv.conf
# OSify Fast & Secure DNS Resolver
nameserver 1.1.1.1
nameserver 9.9.9.9
options timeout:1 attempts:2
EOF
    fi

    # Verifica connettività
    CUR_IP="$(get_current_ip "$IFACE")"
    if [ -n "$CUR_IP" ]; then
        return 0
    else
        # Test ping veloce
        if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then
            return 0
        fi
        return 1
    fi
}

# --- Modalità Interattiva Dialog ---
run_dialog_ui() {
    while true; do
        CUR_IP="$(get_current_ip "$IFACE")"
        if [ -n "$CUR_IP" ]; then
            STATUS_MSG="Stato: CONNESSO | IP: $CUR_IP ($IFACE)"
        else
            STATUS_MSG="Stato: NON CONNESSO | Interfaccia: $IFACE"
        fi

        ACTION=$(dialog --stdout --backtitle "OSify Wi-Fi Manager — Andrea Taliento" \
            --title " 🌐 Gestione Connessioni Wi-Fi & Rete " \
            --menu "$STATUS_MSG\n\nScegli un'operazione:" 15 65 5 \
            "1" "📡  Scansiona e Connettiti a una Rete Wi-Fi" \
            "2" "⌨️   Connettiti inserendo SSID Manuale / Nascosto" \
            "3" "🔄  Rilascia e Rinnova Indirizzo IP (DHCP)" \
            "4" "🛑  Disconnetti Wi-Fi corrente" \
            "0" "❌  Esci" 2>/dev/null || echo "0")

        case "$ACTION" in
            1)
                dialog --title "Ricerca Reti" --infobox "\nScansione frequenze wireless in corso...\n" 5 50
                sfile="$(scan_wifi_ssids)"
                
                # Prepara menu reti
                menu_args=""
                line_no=1
                while IFS=: read -r s_name s_sig s_sec; do
                    if [ -n "$s_name" ]; then
                        menu_args="$menu_args \"$s_name\" \"Segnale: $s_sig ($s_sec)\""
                        line_no=$((line_no + 1))
                    fi
                done < "$sfile"

                if [ -z "$menu_args" ]; then
                    dialog --title "Avviso" --msgbox "Nessuna rete Wi-Fi rilevata.\nVerifica che la scheda Wi-Fi sia attiva." 7 50
                    continue
                fi

                CHOSEN_SSID=$(eval "dialog --stdout --title 'Seleziona Rete Wi-Fi' --menu 'Scegli la rete a cui vuoi connetterti:' 18 65 8 $menu_args" 2>/dev/null || true)
                rm -f "$sfile"

                if [ -n "$CHOSEN_SSID" ]; then
                    PASS=$(dialog --stdout --title "Password Wi-Fi" --insecure --passwordbox "Inserisci la chiave di sicurezza per '$CHOSEN_SSID':\n(Lascia vuoto se la rete è aperta)" 9 55 2>/dev/null || true)
                    
                    dialog --title "Connessione" --infobox "\nNegoziazione crittografia e richiesta IP...\n" 5 50
                    if connect_to_ssid "$CHOSEN_SSID" "$PASS"; then
                        NEW_IP="$(get_current_ip "$IFACE")"
                        dialog --title "Connesso con Successo!" --msgbox "\n[✓] Connesso alla rete: $CHOSEN_SSID\n[✓] Indirizzo IP Assegnato: $NEW_IP\n[✓] Protezione DNS Attiva (1.1.1.1 / 9.9.9.9)\n" 9 55
                    else
                        dialog --title "Errore Connessione" --msgbox "\nImpossibile ottenere l'indirizzo IP da '$CHOSEN_SSID'.\nVerifica la password o la potenza del segnale." 8 55
                    fi
                fi
                ;;
            2)
                MAN_SSID=$(dialog --stdout --title "SSID Manuale" --inputbox "Inserisci il nome esatto della rete Wi-Fi (SSID):" 8 50 2>/dev/null || true)
                if [ -n "$MAN_SSID" ]; then
                    MAN_PASS=$(dialog --stdout --title "Password Wi-Fi" --insecure --passwordbox "Inserisci la password di rete:" 8 50 2>/dev/null || true)
                    dialog --title "Connessione" --infobox "\nConnessione a $MAN_SSID in corso...\n" 5 50
                    if connect_to_ssid "$MAN_SSID" "$MAN_PASS"; then
                        dialog --title "Connesso!" --msgbox "Connessione a $MAN_SSID completata con successo!" 6 45
                    else
                        dialog --title "Errore" --msgbox "Connessione fallita." 6 40
                    fi
                fi
                ;;
            3)
                pkill -f "udhcpc.*$IFACE" 2>/dev/null || true
                udhcpc -i "$IFACE" -n -q -t 5 2>/dev/null || true
                dialog --title "Rinnovo IP" --msgbox "Richiesta DHCP inviata su $IFACE." 6 45
                ;;
            4)
                pkill -f "wpa_supplicant.*$IFACE" 2>/dev/null || true
                pkill -f "udhcpc.*$IFACE" 2>/dev/null || true
                if command -v ip >/dev/null 2>&1; then
                    ip addr flush dev "$IFACE" 2>/dev/null || true
                fi
                dialog --title "Disconnesso" --msgbox "Interfaccia $IFACE disconnessa." 6 45
                ;;
            0|"")
                clear
                exit 0
                ;;
        esac
    done
}

# --- Modalità TUI Testuale ---
run_cli_ui() {
    clear
    printf "\033[1;36m=========================================================\033[0m\n"
    printf "\033[1;32m      OSify Wi-Fi Manager — Connettività Wireless        \033[0m\n"
    printf "\033[1;34m      Ingegnerizzato da Andrea Taliento (ANDRYXify)     \033[0m\n"
    printf "\033[1;36m=========================================================\033[0m\n\n"
    
    CUR_IP="$(get_current_ip "$IFACE")"
    if [ -n "$CUR_IP" ]; then
        echo "• Stato: CONNESSO (IP: $CUR_IP su $IFACE)"
    else
        echo "• Stato: NON CONNESSO (Interfaccia: $IFACE)"
    fi
    echo ""
    echo "1) Scansiona reti Wi-Fi e connettiti"
    echo "2) Inserisci SSID manuale e password"
    echo "3) Disconnetti"
    echo "0) Esci"
    echo ""
    printf "Scelta [0-3]: "
    read -r opt
    case "$opt" in
        1)
            echo "[+] Scansione reti wireless in corso..."
            sfile="$(scan_wifi_ssids)"
            idx=1
            while IFS=: read -r s_name s_sig s_sec; do
                if [ -n "$s_name" ]; then
                    printf "  [%d] %-25s (Segnale: %s | %s)\n" "$idx" "$s_name" "$s_sig" "$s_sec"
                    idx=$((idx + 1))
                fi
            done < "$sfile"
            total=$((idx - 1))
            if [ "$total" -eq 0 ]; then
                echo "Nessuna rete trovata."
                rm -f "$sfile"
                return
            fi
            printf "\nSeleziona numero rete [1-%d]: " "$total"
            read -r num
            selected_ssid="$(sed -n "${num}p" "$sfile" | cut -d: -f1)"
            rm -f "$sfile"
            if [ -n "$selected_ssid" ]; then
                printf "Password per '%s': " "$selected_ssid"
                read -r wpass
                connect_to_ssid "$selected_ssid" "$wpass"
            fi
            ;;
        2)
            printf "Nome SSID: "
            read -r m_ssid
            printf "Password: "
            read -r m_pass
            connect_to_ssid "$m_ssid" "$m_pass"
            ;;
        3)
            pkill -f "wpa_supplicant.*$IFACE" 2>/dev/null || true
            echo "Disconnesso."
            ;;
        *)
            exit 0
            ;;
    esac
}

if command -v dialog >/dev/null 2>&1; then
    run_dialog_ui
else
    run_cli_ui
fi
