#!/bin/sh
# ==============================================================================
# OSify Super Key Daemon — Risposta Istantanea Tasto Windows (Super_L)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Intercetta la pressione e il rilascio singolo del tasto Windows (Super_L, Keycode 133)
# per aprire all'istante l'App Drawer / Launchpad di OSify a costo CPU zero.
# ==============================================================================

[ -z "$DISPLAY" ] && exit 0
command -v xinput >/dev/null 2>&1 || exit 0

# Trova tutti i dispositivi tastiera master/slave
KBD_IDS=$(xinput list 2>/dev/null | grep -i "slave.*keyboard" | grep -oE 'id=[0-9]+' | cut -d= -f2)
[ -z "$KBD_IDS" ] && KBD_IDS="3"

for kbd in $KBD_IDS; do
    (
        pressed_super=0
        other_pressed=0
        
        xinput test "$kbd" 2>/dev/null | while read -r line; do
            case "$line" in
                *"key press 133"*|*"key press 134"*)
                    pressed_super=1
                    other_pressed=0
                    ;;
                *"key release 133"*|*"key release 134"*)
                    if [ "$pressed_super" -eq 1 ] && [ "$other_pressed" -eq 0 ]; then
                        # Apertura o chiusura Launchpad App Drawer
                        if pgrep -f "osify-app-drawer" >/dev/null 2>&1; then
                            pkill -f "osify-app-drawer" 2>/dev/null || true
                        else
                            /usr/bin/osify-app-drawer >/dev/null 2>&1 &
                        fi
                    fi
                    pressed_super=0
                    other_pressed=0
                    ;;
                *"key press"*)
                    if [ "$pressed_super" -eq 1 ]; then
                        other_pressed=1
                    fi
                    ;;
            esac
        done
    ) &
done
