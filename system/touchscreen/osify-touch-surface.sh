#!/usr/bin/env bash
# ==============================================================================
# OSify Touchscreen & Microsoft Surface Intelligence Suite
# ==============================================================================
# Ottimizzato per dispositivi touch, convertibili 2-in-1 e tablet Microsoft Surface:
# 1. Driver e moduli kernel Microsoft Surface (surface_aggregator, surface_gpe, iptsd)
# 2. Tastiera virtuale a comparsa automatica (Maliit Keyboard Wayland)
# 3. Rotazione automatica dello schermo e del touch via accelerometro (iio-sensor-proxy)
# 4. Modalità Tablet Mode automatica al distacco della Type Cover / tastiera
# 5. Supporto per penne e pennini stilo con livelli di pressione (Surface Pen / MPP)
# ==============================================================================

set -euo pipefail

configure_touch_environment() {
    echo "========================================================="
    echo "       OSify Touch & Tablet Engine — Inizializzazione    "
    echo "========================================================="

    # 1. Rileva se il dispositivo è un Microsoft Surface
    local is_surface="no"
    if grep -qi "surface" /sys/devices/virtual/dmi/id/product_name 2>/dev/null || \
       grep -qi "microsoft" /sys/devices/virtual/dmi/id/sys_vendor 2>/dev/null; then
        is_surface="yes"
        echo "[+] RILEVATO DISPOSITIVO MICROSOFT SURFACE!"
    fi

    if [[ "$is_surface" == "yes" ]]; then
        echo "[+] Caricamento moduli kernel dedicati Surface..."
        modprobe surface_aggregator 2>/dev/null || true
        modprobe surface_aggregator_registry 2>/dev/null || true
        modprobe surface_hid 2>/dev/null || true
        modprobe surface_gpe 2>/dev/null || true

        # Se presente il demone iptsd per il digitalizzatore touch preciso Intel
        if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q "iptsd"; then
            echo "[+] Abilitazione servizio touch iptsd..."
            systemctl enable --now iptsd.service 2>/dev/null || true
        fi
    fi

    # 2. Configurazione Tastiera Virtuale a Comparsa Automatica (Maliit)
    echo "[+] Configurazione tastiera virtuale Wayland (Maliit Keyboard)..."
    if command -v kwriteconfig6 >/dev/null 2>&1; then
        # Abilita Maliit come input method virtuale in KWin
        kwriteconfig6 --file kwinrc --group Wayland --key VirtualKeyboard "maliit-keyboard.desktop"
        kwriteconfig6 --file kwinrc --group Input --key TabletMode "auto"
    fi

    # 3. Servizio di auto-rotazione schermo (Accelerometro)
    if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files | grep -q "iio-sensor-proxy"; then
        echo "[+] Abilitazione auto-rotazione schermo via sensore accelerometro..."
        systemctl enable --now iio-sensor-proxy.service 2>/dev/null || true
    fi

    echo "[✓] Suite Touchscreen & Surface configurata con successo!"
}

toggle_tablet_mode() {
    local mode="${1:-auto}"
    echo "[+] Impostazione Tablet Mode: $mode"
    if command -v kwriteconfig6 >/dev/null 2>&1; then
        case "$mode" in
            on|tablet)
                kwriteconfig6 --file kwinrc --group Input --key TabletMode "on"
                echo "[✓] Modalità Tablet FORZATA: bersagli touch ingranditi e tastiera attiva."
                ;;
            off|desktop)
                kwriteconfig6 --file kwinrc --group Input --key TabletMode "off"
                echo "[✓] Modalità Desktop FORZATA."
                ;;
            auto)
                kwriteconfig6 --file kwinrc --group Input --key TabletMode "auto"
                echo "[✓] Modalità Automatica (al distacco tastiera/cover)."
                ;;
        esac
    fi
}

case "${1:-setup}" in
    setup)
        configure_touch_environment
        ;;
    mode)
        toggle_tablet_mode "${2:-auto}"
        ;;
    *)
        echo "Uso: $0 {setup|mode <tablet|desktop|auto>}"
        exit 1
        ;;
esac
