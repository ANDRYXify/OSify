#!/bin/sh
# ==============================================================================
# OSify Universal Touchpad & Input Auto-Configurator
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Compatibile al 100% con evdev, synaptics e libinput su qualsiasi Netbook/Laptop
# (Incluso Toshiba NB200 con Touchpad Synaptics/Alps PS/2).
# ==============================================================================

# 1. Modulo Kernel psmouse
modprobe -q psmouse 2>/dev/null || true

# 2. Configurazione dinamica tramite xinput (Funziona sia con evdev sia con libinput)
if command -v xinput >/dev/null 2>&1; then
    for id in $(xinput list --id-only 2>/dev/null); do
        name=$(xinput list --name-only "$id" 2>/dev/null)
        case "$name" in
            *[Tt]ouchpad*|*SynPS/2*|*ALPS*|*Alps*|*TrackPoint*|*GlidePoint*|*Elantech*|*[Pp]ointer*)
                # Abilitazione Tap-To-Click universale
                xinput set-prop "$id" "libinput Tapping Enabled" 1 2>/dev/null || true
                xinput set-prop "$id" "libinput Natural Scrolling Enabled" 1 2>/dev/null || true
                xinput set-prop "$id" "Evdev Drag Lock Buttons" 1 2>/dev/null || true
                ;;
        esac
    done
fi

# 3. Fallback synclient se il modulo Xorg synaptics è attivo
if command -v synclient >/dev/null 2>&1; then
    synclient TapButton1=1 TapButton2=3 TapButton3=2 VertEdgeScroll=1 HorizEdgeScroll=1 PalmDetect=1 CoastingSpeed=20 2>/dev/null || true
fi

# 4. Eliminazione Input Lag Tastiera & Accelerazione Fluida Cursore
if [ -n "$DISPLAY" ] && command -v xset >/dev/null 2>&1; then
    # Ripetizione tasti reattiva (ritardo 250ms, 30 caratteri al secondo)
    xset r rate 250 30 2>/dev/null || true
    # Accelerazione del puntatore naturale
    xset m 2/1 4 2>/dev/null || true
    # Disabilita screensaver cieco di X11 (gestito da OSify Power Subsystem)
    xset s off -dpms 2>/dev/null || true
fi
