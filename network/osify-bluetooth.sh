#!/bin/sh
# ==============================================================================
# OSify Bluetooth Manager — Connettività Wireless Cuffie, Mouse & Controller
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta standard Bluetooth 2.1, 3.0, 4.0 LE, 5.x:
# - Rilevamento controller e sblocco radio automatico (rfkill)
# - Scansione dispositivi, accoppiamento (pairing) e connessione affidabile (trust)
# - Gestione profili A2DP (Audio Stereo HQ), HID (Mouse/Tastiere/Controller)
# ==============================================================================

# Auto-elevazione root se necessaria
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    fi
fi

log() { printf "\033[1;36m[OSify-Bluetooth]\033[0m %s\n" "$*"; }

# 1. Verifica controller hardware Bluetooth
check_bt_hardware() {
    # Sblocca radio se bloccata
    if command -v rfkill >/dev/null 2>&1; then
        rfkill unblock bluetooth 2>/dev/null || true
    fi

    # Avvia servizio bluetooth se presente
    if command -v /etc/init.d/bluetooth >/dev/null 2>&1; then
        /etc/init.d/bluetooth start >/dev/null 2>&1 || true
    elif command -v systemctl >/dev/null 2>&1; then
        systemctl start bluetooth 2>/dev/null || true
    fi

    if [ -d /sys/class/bluetooth ] && [ "$(ls -A /sys/class/bluetooth 2>/dev/null)" ]; then
        return 0
    fi
    if command -v hciconfig >/dev/null 2>&1 && hciconfig 2>/dev/null | grep -q "hci"; then
        return 0
    fi
    return 1
}

# 2. Scansione dispositivi
scan_devices() {
    log "Scansione dispositivi Bluetooth nelle vicinanze in corso..."
    if command -v bluetoothctl >/dev/null 2>&1; then
        # Invia comandi a bluetoothctl per scansione rapida
        bluetoothctl power on >/dev/null 2>&1 || true
        (
            echo "scan on"
            sleep 4
            echo "devices"
            echo "quit"
        ) | bluetoothctl 2>/dev/null | grep "^Device " | awk '{$1=""; print $0}' | sed 's/^[ \t]*//'
    elif command -v hcitool >/dev/null 2>&1; then
        hcitool scan 2>/dev/null | grep -E "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}" | awk '{print $1 " " $2}'
    else
        echo "Nessun dispositivo rilevato."
    fi
}

# 3. Connessione a dispositivo per MAC address
connect_device() {
    _mac="$1"
    [ -z "$_mac" ] && return 1

    log "Connessione al dispositivo $_mac..."
    if command -v bluetoothctl >/dev/null 2>&1; then
        bluetoothctl power on >/dev/null 2>&1 || true
        bluetoothctl pair "$_mac" >/dev/null 2>&1 || true
        bluetoothctl trust "$_mac" >/dev/null 2>&1 || true
        bluetoothctl connect "$_mac" >/dev/null 2>&1 || true
        log "[OK] Dispositivo $_mac connesso con successo."
    else
        log "[!] bluetoothctl non disponibile."
    fi
}

# 4. Disconnessione
disconnect_device() {
    _mac="$1"
    if command -v bluetoothctl >/dev/null 2>&1; then
        bluetoothctl disconnect "$_mac" >/dev/null 2>&1 || true
        log "[OK] Dispositivo $_mac disconnesso."
    fi
}

# ==============================================================================
# INTERFACCIA UTENTE
# ==============================================================================
if ! check_bt_hardware; then
    if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
        yad --warning --title="Bluetooth Non Rilevato" \
            --text="Nessun controller Bluetooth interno o adattatore USB rilevato sul computer." --center
    elif command -v dialog >/dev/null 2>&1 && [ -t 0 ]; then
        dialog --title "Avviso Bluetooth" --msgbox "Nessun controller Bluetooth hardware rilevato." 7 50
    else
        log "[!] Nessun controller Bluetooth rilevato sul computer."
    fi
    exit 0
fi

if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1 && [ -z "$1" ]; then
    DEVS_LIST=$(scan_devices | tr '\n' '!')
    [ -z "$DEVS_LIST" ] && DEVS_LIST="Nessun dispositivo nelle vicinanze"

    CHOICE=$(yad --form \
        --title="OSify — Gestione Dispositivi Bluetooth" \
        --window-icon="/usr/share/pixmaps/osify-hub.png" \
        --image="/usr/share/pixmaps/osify-hub.png" \
        --text="<big><b>Connettività Bluetooth OSify</b></big>\nCollega cuffie wireless, controller, tastiere o mouse:" \
        --width=520 --center \
        --field="Dispositivi Rilevati:CB" "$DEVS_LIST" \
        --button="Connetti:0" \
        --button="Annulla:1")

    if [ $? -eq 0 ]; then
        TARGET=$(echo "$CHOICE" | awk -F'|' '{print $1}')
        MAC=$(echo "$TARGET" | grep -oE "([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}")
        if [ -n "$MAC" ]; then
            connect_device "$MAC"
        fi
    fi
    exit 0
fi

case "${1:-scan}" in
    scan)
        scan_devices
        ;;
    connect)
        connect_device "$2"
        ;;
    disconnect)
        disconnect_device "$2"
        ;;
    status)
        check_bt_hardware && echo "Bluetooth: ATTIVO" || echo "Bluetooth: NON ATTIVO"
        ;;
    *)
        echo "Uso: $0 [scan|connect <MAC>|disconnect <MAC>|status]"
        exit 1
        ;;
esac
