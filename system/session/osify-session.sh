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

# 4. Calibrazione Adattiva I/O Storage & USB Anti-Freeze Governor
if [ -x /usr/bin/osify-storage-governor ]; then
    /usr/bin/osify-storage-governor --tune &
fi

# 5. Bootsplash OLED OSify con Logo Luminescente e Barra di Caricamento
if [ -x /usr/bin/osify-bootsplash ]; then
    /usr/bin/osify-bootsplash
fi

# 6. Sfondo Root Window Cyber-Dark
if command -v xsetroot >/dev/null 2>&1; then
    xsetroot -solid "#0b0d14" 2>/dev/null &
fi

# 7. Gestore Scrivania PCManFM (Sfondo nativo HD ed Icone Desktop)
if command -v pcmanfm >/dev/null 2>&1; then
    (sleep 0.2 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) 2>/dev/null &
fi

# 8. OSify Top Menu Bar & Floating Dock (Dual-Panel macOS 2050)
(
    sleep 0.4
    if ! pgrep -x lxpanel >/dev/null 2>&1; then
        if command -v lxpanel >/dev/null 2>&1; then
            lxpanel --profile slitaz 2>/dev/null || lxpanel --profile default 2>/dev/null || lxpanel 2>/dev/null || true
        fi
    fi
) &

# 9. Intercettazione Diretta Modalità Installazione da Bootloader
if grep -qE "osify\.install=1|osify_mode=install|install_mode=1" /proc/cmdline 2>/dev/null; then
    (
        sleep 0.8
        if [ -x /usr/bin/osify-live-installer ]; then
            /usr/bin/osify-live-installer &
        elif [ -x /usr/bin/osify-install-gui ]; then
            /usr/bin/osify-install-gui &
        elif [ -x /usr/bin/osify-install ]; then
            /usr/bin/osify-install &
        fi
    ) &
else
    # 10. OSify OOBE — Assistente di Configurazione Primo Avvio (macOS Setup Assistant)
    (
        sleep 0.8
        SETUP_DONE="${HOME:-/home/osify}/.config/osify/setup_done"
        if [ ! -f "$SETUP_DONE" ]; then
            if [ -x /usr/bin/osify-oobe ]; then
                /usr/bin/osify-oobe
            elif [ -x /usr/bin/osify-welcome-wizard ]; then
                /usr/bin/osify-welcome-wizard &
            fi
        fi
    ) &
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
