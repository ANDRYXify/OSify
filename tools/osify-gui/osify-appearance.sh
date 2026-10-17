#!/bin/sh
# ==============================================================================
# OSify Appearance & Display Manager — Personalizzazione Completa
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta:
# - Virtual Scaler per Netbook (1024x600 -> 1280x768 per finestre complete)
# - Switcher Wallpaper OSify Cyber Dark ad alta risoluzione
# - Gestione Temi Openbox e stile interfaccia
# ==============================================================================

set -e

WALLPAPER_DIR="/usr/share/images"
CURRENT_RES=$(xrandr 2>/dev/null | grep -o '[0-9]\+x[0-9]\+' | head -n1 || echo "1024x600")

set_virtual_scaler() {
    output=$(xrandr 2>/dev/null | awk '/ connected/ {print $1; exit}')
    [ -z "$output" ] && output="LVDS1"
    
    # Toggle tra 1024x600 nativo e 1280x768 scalato
    if xrandr 2>/dev/null | grep -q "1280x768"; then
        # Ripristina 1024x600 nativo
        xrandr --output "$output" --panning 1024x600 --scale 1.0x1.0 2>/dev/null || true
        msg="Ripristinata risoluzione nativa 1024x600."
    else
        # Attiva scaling virtuale 1280x768
        xrandr --output "$output" --panning 1280x768 --scale 1.25x1.28 2>/dev/null || \
        xrandr --output "$output" --scale-from 1280x768 2>/dev/null || true
        msg="Attivato Virtual Scaler 1280x768! Tutte le finestre ora entrano nello schermo senza tagli."
    fi

    # Riavvia pcmanfm desktop per riallineare wallpaper
    pcmanfm --reconfigure 2>/dev/null || true

    if command -v dialog >/dev/null 2>&1; then
        dialog --title "Display Scaler" --msgbox "$msg" 7 50
    else
        echo "$msg"
        sleep 2
    fi
}

set_standard_resolution() {
    res="$1"
    output=$(xrandr 2>/dev/null | awk '/ connected/ {print $1; exit}')
    [ -z "$output" ] && output="LVDS1"
    xrandr --output "$output" --scale 1.0x1.0 --mode "$res" 2>/dev/null || xrandr -s "$res" 2>/dev/null || true
    pcmanfm --reconfigure 2>/dev/null || true
}

set_dark_background() {
    color="$1"
    if command -v xsetroot >/dev/null 2>&1; then
        xsetroot -solid "$color" 2>/dev/null || true
    fi
    # Se pcmanfm gestisce il desktop, aggiorniamo il file di configurazione
    for conf in "$HOME/.config/pcmanfm/default/pcmanfm.conf" "/etc/skel/.config/pcmanfm/default/pcmanfm.conf"; do
        if [ -f "$conf" ]; then
            sed -i "s/desktop_bg=.*/desktop_bg=$color/" "$conf" 2>/dev/null || true
            sed -i "s/desktop_shadow=.*/desktop_shadow=$color/" "$conf" 2>/dev/null || true
        fi
    done
    pcmanfm --reconfigure 2>/dev/null || true
}

if command -v dialog >/dev/null 2>&1; then
    while true; do
        A_OPT=$(dialog --stdout --backtitle "OSify Appearance — Andrea Taliento" \
            --title "  Personalizzazione Aspetto & Display " \
            --menu "Risoluzione Attuale: $CURRENT_RES\n\nScegli cosa personalizzare:" 16 65 6 \
            "1" "   Toggle Virtual Scaler Netbook (1024x600 ↔ 1280x768)" \
            "2" "  Sfondo: Dark Obsidian Matrix (Nero Assoluto #0b0d14)" \
            "3" "  Sfondo: Deep Cyber Navy (#0f172a)" \
            "4" "   Sfondo: Carbon Fiber Slate (#18181b)" \
            "5" "   Seleziona Risoluzione Grafica Tradizionale" \
            "0" "  Torna al Desktop" 2>/dev/null || echo "0")

        case "$A_OPT" in
            1) set_virtual_scaler ;;
            2) set_dark_background "#0b0d14" ;;
            3) set_dark_background "#0f172a" ;;
            4) set_dark_background "#18181b" ;;
            5)
                R_OPT=$(dialog --stdout --title "Risoluzioni" --menu "Seleziona risoluzione per display esterno o nativo:" 14 55 5 \
                    "1024x600"  "WSVGA Netbook (Toshiba NB200)" \
                    "1280x720"  "HD 720p Widescreen" \
                    "1280x800"  "WXGA 16:10 Laptop" \
                    "1366x768"  "HD Ready Standard" \
                    "1920x1080" "Full HD 1080p Monitor Esterno" 2>/dev/null || true)
                if [ -n "$R_OPT" ]; then
                    set_standard_resolution "$R_OPT"
                fi
                ;;
            0|"") clear; exit 0 ;;
        esac
    done
else
    clear
    echo "========================================================="
    echo "    OSify Appearance & Display Manager                "
    echo "========================================================="
    echo " 1)  Toggle Virtual Scaler Netbook (1024x600 ↔ 1280x768)"
    echo " 2)  Sfondo Obsidian Matrix (#0b0d14)"
    echo " 3)  Sfondo Deep Cyber Navy (#0f172a)"
    echo " 4)  Sfondo Carbon Slate (#18181b)"
    echo " 0)  Esci"
    echo "========================================================="
    read -rp "Selezione [0-4]: " a_opt
    case "$a_opt" in
        1) set_virtual_scaler ;;
        2) set_dark_background "#0b0d14" ;;
        3) set_dark_background "#0f172a" ;;
        4) set_dark_background "#18181b" ;;
        *) exit 0 ;;
    esac
fi
