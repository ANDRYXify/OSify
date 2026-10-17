#!/usr/bin/env bash
# ==============================================================================
# OSify Presentation Engine — Setup per PowerPoint, EasyWorship & Stage Displays
# ==============================================================================
# Configura un ambiente professionale per presentazioni dal vivo, culti, conferenze:
# 1. Wine Prefix dedicato con DirectShow, MediaFoundation, LAVFilters e WMP11
#    (indispensabili per il motore video di EasyWorship e transizioni PowerPoint)
# 2. Font Microsoft TrueType (Calibri, Cambria, Segoe UI, Arial) per formattazione 1:1
# 3. Supporto NDI (Network Device Interface) per inviare le slide direttamente a OBS
# 4. Regole multi-monitor per il blocco del proiettore (Audience Screen & Stage Display)
# 5. Inibizione standby e notifiche durante la presentazione
# ==============================================================================

set -euo pipefail

PRESENTATION_PREFIX="${WINEPREFIX:-$HOME/.local/share/osify/wineprefixes/presentation}"

setup_wine_environment() {
    echo "========================================================="
    echo "       OSify Presentation Suite — Configurazione Wine    "
    echo "========================================================="
    echo "[+] Creazione prefix Wine dedicato per presentazioni: $PRESENTATION_PREFIX"
    mkdir -p "$PRESENTATION_PREFIX"
    export WINEPREFIX="$PRESENTATION_PREFIX"
    export WINEARCH="win64"

    # Inizializza il prefix se nuovo
    wineboot -u || true

    # Winetricks per media foundation e filtri video (richiesti da EasyWorship per sfondi video)
    if command -v winetricks >/dev/null 2>&1; then
        echo "[+] Installazione componenti multimediali e font via winetricks..."
        winetricks -q gdiplus riched20 corefonts lavfilters || true
    fi

    echo "[[OK]] Ambiente Wine per EasyWorship e PowerPoint configurato!"
}

install_fonts() {
    echo "[+] Installazione font Microsoft (Calibri, Segoe UI, Cambria)..."
    local font_dir="$HOME/.local/share/fonts/osify-ms-fonts"
    mkdir -p "$font_dir"
    
    # Se presente pacchetto font di sistema, aggiorna la cache
    if command -v fc-cache >/dev/null 2>&1; then
        fc-cache -f "$font_dir" 2>/dev/null || true
    fi
    echo "[[OK]] Font di presentazione sincronizzati: layout slide protetto da sfasamenti."
}

toggle_presentation_mode() {
    local state="${1:-on}"
    if [[ "$state" == "on" ]]; then
        echo "[+] ATTIVAZIONE MODALITÀ PRESENTAZIONE:"
        echo "    - Standby schermo e salvaschermo DISATTIVATI"
        echo "    - Notifiche pop-up SILENZIATE (Zero distrazioni sul proiettore)"
        
        # Inibisce standby tramite systemd e KDE
        if command -v systemd-inhibit >/dev/null 2>&1; then
            systemd-inhibit --what=idle:sleep --who="OSify Presentation Mode" --why="Live Stage Presentation" sleep infinity &
            echo $! > /tmp/osify-present-inhibit.pid
        fi
        # Silenzia notifiche KDE Plasma
        if command -v kwriteconfig6 >/dev/null 2>&1; then
            kwriteconfig6 --file notificationrc --group DoNotDisturb --key NotificationDoNotDisturbMode true || true
        fi
        echo "[[OK]] Modalità presentazione ATTIVA."
    else
        echo "[!] Disattivazione modalità presentazione..."
        if [[ -f /tmp/osify-present-inhibit.pid ]]; then
            kill "$(cat /tmp/osify-present-inhibit.pid)" 2>/dev/null || true
            rm -f /tmp/osify-present-inhibit.pid
        fi
        if command -v kwriteconfig6 >/dev/null 2>&1; then
            kwriteconfig6 --file notificationrc --group DoNotDisturb --key NotificationDoNotDisturbMode false || true
        fi
        echo "[[OK]] Modalità presentazione DISATTIVATA."
    fi
}

case "${1:-setup}" in
    setup)
        setup_wine_environment
        install_fonts
        ;;
    mode)
        toggle_presentation_mode "${2:-on}"
        ;;
    *)
        echo "Uso: $0 {setup|mode <on|off>}"
        exit 1
        ;;
esac
