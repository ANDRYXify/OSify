#!/bin/sh
# ==============================================================================
# OSify Indestructible Desktop Session Supervisor
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Mantiene la sessione grafica Xorg SEMPRE attiva, protegge da crash e
# inizializza in modo ordinato il desktop proprietario OSify.
# ==============================================================================

export DISPLAY="${DISPLAY:-:0.0}"
export XDG_CURRENT_DESKTOP="OSify"
export DESKTOP_SESSION="osify"

# 1. Inizializzazione D-Bus e autorizzazioni
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ] && command -v dbus-launch >/dev/null 2>&1; then
    eval $(dbus-launch --sh-syntax)
    export DBUS_SESSION_BUS_ADDRESS
    export DBUS_SESSION_BUS_PID
fi

# 2. Keymap tastiera italiana se configurata
if [ -f /etc/keymap.conf ]; then
    kmaplang=$(cat /etc/keymap.conf | awk -F'-' '{print $1}')
    [ -n "$kmaplang" ] && setxkbmap "$kmaplang" 2>/dev/null || true
fi

# 3. Configurazione Touchpad Universale (evdev/libinput/synaptics)
if [ -x /usr/bin/osify-input-setup ]; then
    /usr/bin/osify-input-setup &
fi

# 4. Sfondo Root Window Cyber-Dark
if command -v xsetroot >/dev/null 2>&1; then
    xsetroot -solid "#0b0d14" 2>/dev/null &
fi

# 5. Gestore Scrivania PCManFM (Sfondo nativo HD ed Icone Desktop)
if command -v pcmanfm >/dev/null 2>&1; then
    (sleep 0.5 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) 2>/dev/null &
fi

# 6. OSify Cyber-Bar (LXPanel Dock Moderno)
if command -v lxpanel >/dev/null 2>&1; then
    (sleep 0.8 && pgrep -x lxpanel >/dev/null || lxpanel --profile slitaz) 2>/dev/null &
fi

# 7. OSify Hub — Launchpad & Centro di Controllo
if [ -x /usr/bin/osify-hub ]; then
    (sleep 1.2 && terminal -geometry 74x20+140+100 -T 'OSify Hub' -e /usr/bin/osify-hub) 2>/dev/null &
fi

# 8. Loop di Vigilanza Indistruttibile del Window Manager (Supervisor)
# Se Openbox dovesse avere un'eccezione o crashare, viene riavviato istantaneamente
# SENZA MAI cadere su TTY o chiudere Xorg:
while true; do
    if command -v openbox >/dev/null 2>&1; then
        openbox
    else
        xterm
    fi
    sleep 1
done
