#!/usr/bin/env bash
# ==============================================================================
# OSify Desktop Factory Reset — Ripristino Impostazioni Grafiche Originali
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Ripristina istantaneamente l'aspetto grafico, la taskbar, le icone del desktop
# e i menu alle impostazioni di fabbrica OSify preservando intatti tutti i dati
# e i documenti personali dell'utente.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"
USER_HOME="${HOME:-/home/osify}"

reset_desktop_settings() {
    echo "==> Ripristino impostazioni di fabbrica OSify in corso..."

    # 1. Ripristino configurazioni Openbox
    if [ -d "/etc/skel/.config/openbox" ]; then
        mkdir -p "$USER_HOME/.config/openbox"
        cp -rf /etc/skel/.config/openbox/* "$USER_HOME/.config/openbox/" 2>/dev/null || true
    fi

    # 2. Ripristino LXPanel
    if [ -d "/etc/skel/.config/lxpanel" ]; then
        mkdir -p "$USER_HOME/.config/lxpanel"
        cp -rf /etc/skel/.config/lxpanel/* "$USER_HOME/.config/lxpanel/" 2>/dev/null || true
    fi

    # 3. Ripristino PCManFM e LibFM
    if [ -d "/etc/skel/.config/pcmanfm" ]; then
        mkdir -p "$USER_HOME/.config/pcmanfm"
        cp -rf /etc/skel/.config/pcmanfm/* "$USER_HOME/.config/pcmanfm/" 2>/dev/null || true
    fi
    if [ -d "/etc/skel/.config/libfm" ]; then
        mkdir -p "$USER_HOME/.config/libfm"
        cp -rf /etc/skel/.config/libfm/* "$USER_HOME/.config/libfm/" 2>/dev/null || true
    fi

    # 4. Ripristino icone del Desktop
    if [ -d "/etc/skel/Desktop" ]; then
        mkdir -p "$USER_HOME/Desktop"
        cp -rf /etc/skel/Desktop/* "$USER_HOME/Desktop/" 2>/dev/null || true
        chmod +x "$USER_HOME/Desktop/"*.desktop 2>/dev/null || true
    fi

    # 5. Hot-reload componenti grafici attivi
    if command -v openbox >/dev/null 2>&1; then
        openbox --reconfigure 2>/dev/null || true
    fi
    if command -v lxpanel >/dev/null 2>&1; then
        pkill lxpanel 2>/dev/null || true
        (sleep 1 && lxpanel --profile default &) 2>/dev/null || true
    fi
    if command -v pcmanfm >/dev/null 2>&1; then
        pcmanfm --reconfigure 2>/dev/null || true
    fi

    echo "[OK] Ripristino completato con successo!"
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        reset_desktop_settings
        return 0
    fi

    if yad --question \
        --title="OSify — Ripristino Impostazioni Desktop" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Ripristino Aspetto di Fabbrica</b></big>\n\nVuoi ripristinare la barra delle applicazioni, le icone del desktop e i menu alle impostazioni originali di OSify?\n\n<b>I tuoi file personali, foto e documenti NON verranno toccati.</b>" \
        --button="Ripristina Desktop:0" \
        --button="Annulla:1" \
        --center 2>/dev/null; then

        reset_desktop_settings
        yad --info --title="Ripristino Concluso" \
            --text="<big><b>Desktop Ripristinato!</b></big>\n\nLe impostazioni originali di OSify sono state ristabilite." \
            --center 2>/dev/null || true
    fi
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui
        else
            reset_desktop_settings
        fi
        ;;
    reset|force)
        reset_desktop_settings
        ;;
    *)
        echo "Uso: $0 {gui|reset}"
        exit 1
        ;;
esac
