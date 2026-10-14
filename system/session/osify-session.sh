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
    (sleep 0.4 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) 2>/dev/null &
fi

# 6. OSify Cyber-Bar (LXPanel Dock Moderno con Supervisore Resiliente)
(
    sleep 0.6
    if ! pgrep -x lxpanel >/dev/null 2>&1; then
        if command -v lxpanel >/dev/null 2>&1; then
            lxpanel --profile default 2>/dev/null || lxpanel --profile slitaz 2>/dev/null || lxpanel 2>/dev/null || true
        fi
    fi
    # Fallback se lxpanel non dovesse partire
    sleep 1.0
    if ! pgrep -x lxpanel >/dev/null 2>&1; then
        [ -x /usr/bin/osify-cyber-dock ] && /usr/bin/osify-cyber-dock &
    fi
) &

# 7. OSify Profile & Multi-User Setup (OOBE al Primo Avvio Garantito)
# Sia in versione Live che installata, se l'utente non ha ancora configurato
# il profilo, si avvia il wizard in primo piano:
(
    sleep 1.0
    FLAG_CONF="${HOME:-/home/osify}/.config/osify/profile_configured"
    if [ ! -f "$FLAG_CONF" ]; then
        if [ -x /usr/bin/osify-profile-setup ]; then
            /usr/bin/osify-profile-setup
        fi
    fi
) &

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
