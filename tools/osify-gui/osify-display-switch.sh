#!/bin/sh
# ==============================================================================
# OSify Display Switcher — Gestione Uscite Video HDMI, VGA & Multi-Monitor
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Riconoscimento al volo monitor esterni, TV e proiettori:
# Clona, Estendi (Dual Monitor), Solo Esterno o Solo Laptop con un click.
# ==============================================================================

LOGO_IMG="/usr/share/pixmaps/osify-appearance.png"

INT_OUT=$(xrandr 2>/dev/null | grep ' connected' | grep -E 'LVDS|eDP|DSI' | awk '{print $1}' | head -n1)
[ -z "$INT_OUT" ] && INT_OUT=$(xrandr 2>/dev/null | grep ' connected' | awk '{print $1}' | head -n1)

EXT_OUT=$(xrandr 2>/dev/null | grep ' connected' | grep -v "$INT_OUT" | awk '{print $1}' | head -n1)

apply_display_mode() {
    _mode="$1"
    
    if [ -z "$EXT_OUT" ]; then
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --info --title="Nessun Monitor Esterno" --text="Nessun monitor HDMI o VGA esterno rilevato al momento." --center
        else
            echo "[!] Nessun monitor esterno rilevato."
        fi
        return
    fi

    case "$_mode" in
        mirror)
            xrandr --output "$INT_OUT" --auto --output "$EXT_OUT" --auto --same-as "$INT_OUT" 2>/dev/null || true
            ;;
        right)
            xrandr --output "$INT_OUT" --auto --output "$EXT_OUT" --auto --right-of "$INT_OUT" 2>/dev/null || true
            ;;
        left)
            xrandr --output "$INT_OUT" --auto --output "$EXT_OUT" --auto --left-of "$INT_OUT" 2>/dev/null || true
            ;;
        external_only)
            xrandr --output "$INT_OUT" --off --output "$EXT_OUT" --auto 2>/dev/null || true
            ;;
        internal_only)
            xrandr --output "$EXT_OUT" --off --output "$INT_OUT" --auto 2>/dev/null || true
            ;;
    esac

    # Ricarica wallpaper PCManFM
    if command -v pcmanfm >/dev/null 2>&1; then
        pcmanfm --reconfigure 2>/dev/null || true
    fi
}

if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    STATUS_TXT="Display Interno: <b>$INT_OUT</b>"
    if [ -n "$EXT_OUT" ]; then
        STATUS_TXT="$STATUS_TXT\nMonitor Esterno Rilevato: <b>$EXT_OUT (Connesso)</b>"
    else
        STATUS_TXT="$STATUS_TXT\nMonitor Esterno: <i>Nessuno rilevato su HDMI/VGA</i>"
    fi

    CHOICE=$(yad --form \
        --title="OSify — Uscite Video & Multi-Monitor" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Gestione Schermi & Uscite Video HDMI/VGA</b></big>\n$STATUS_TXT" \
        --width=480 --center \
        --field="Modalità Display:CB" "Clona Schermo (Mirroring HDMI/VGA per proiettori)!Estendi a Destra (Dual Monitor)!Estendi a Sinistra!Solo Monitor Esterno (Spegni schermo laptop)!Solo Schermo Laptop" \
        --button="Applica:0" --button="gtk-cancel:1")

    if [ $? -eq 0 ]; then
        M_CHOSEN=$(echo "$CHOICE" | awk -F'|' '{print $1}')
        case "$M_CHOSEN" in
            *Clona*)        apply_display_mode "mirror" ;;
            *Destra*)       apply_display_mode "right" ;;
            *Sinistra*)     apply_display_mode "left" ;;
            *"Solo Monitor"*) apply_display_mode "external_only" ;;
            *)              apply_display_mode "internal_only" ;;
        esac
    fi
    exit 0
fi

case "$1" in
    --mirror)   apply_display_mode "mirror" ;;
    --right)    apply_display_mode "right" ;;
    --external) apply_display_mode "external_only" ;;
    *)          apply_display_mode "mirror" ;;
esac
