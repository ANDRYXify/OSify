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

# 5. Sfondo Root Window Cyber-Dark
if command -v xsetroot >/dev/null 2>&1; then
    xsetroot -solid "#0b0d14" 2>/dev/null &
fi

# 6. Gestore Scrivania PCManFM (Sfondo nativo HD ed Icone Desktop)
if command -v pcmanfm >/dev/null 2>&1; then
    (sleep 0.3 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) 2>/dev/null &
fi

# 7. OSify Cyber-Bar (LXPanel Dock Moderno con Profilo slitaz/default)
(
    sleep 0.6
    if ! pgrep -x lxpanel >/dev/null 2>&1; then
        if command -v lxpanel >/dev/null 2>&1; then
            lxpanel --profile slitaz 2>/dev/null || lxpanel --profile default 2>/dev/null || lxpanel 2>/dev/null || true
        fi
    fi
    sleep 1.0
    if ! pgrep -x lxpanel >/dev/null 2>&1; then
        [ -x /usr/bin/osify-cyber-dock ] && /usr/bin/osify-cyber-dock &
    fi
) &

# 8. Intercettazione Diretta Modalità Installazione da Bootloader (Opzione 4 ISO)
# Se l'utente ha scelto 'Installa OSify su Disco Fisso' al menu di avvio USB,
# si apre SUBITO l'installer su finestra grafica in primo piano senza interrompere la sessione Xorg:
if grep -qE "osify\.install=1|osify_mode=install|install_mode=1" /proc/cmdline 2>/dev/null; then
    (
        sleep 1.0
        if command -v sakura >/dev/null 2>&1; then
            sakura -T "OSify — Installazione Guidata su Disco" -e /usr/bin/osify-install
        elif command -v xterm >/dev/null 2>&1; then
            xterm -geometry 95x26 -T "OSify — Installazione Guidata su Disco" -e /usr/bin/osify-install
        elif [ -x /usr/bin/osify-install ]; then
            /usr/bin/osify-install &
        fi
    ) &
else
    # 9. OSify Profile & Multi-User Setup (OOBE al Primo Avvio Live / Installato)
    (
        sleep 1.2
        FLAG_CONF="${HOME:-/home/osify}/.config/osify/profile_configured"
        if [ ! -f "$FLAG_CONF" ]; then
            if command -v sakura >/dev/null 2>&1; then
                sakura -T "OSify — Configurazione Profilo Iniziale" -e /usr/bin/osify-profile-setup
            elif command -v xterm >/dev/null 2>&1; then
                xterm -geometry 80x25 -T "OSify — Configurazione Profilo Iniziale" -e /usr/bin/osify-profile-setup
            elif [ -x /usr/bin/osify-profile-setup ]; then
                /usr/bin/osify-profile-setup &
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
