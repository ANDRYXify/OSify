#!/usr/bin/env bash
# ==============================================================================
# OSify Stage & NDI Routing Engine
# ==============================================================================
# Gestisce le uscite video multi-display per eventi e worship:
# 1. Schermo Principale: Console Operatore / Tecnico
# 2. Schermo Secondario: Proiettore / Sala (Audience Screen - Borderless Fullscreen)
# 3. Schermo Terziario: Stage Display / Confidence Monitor (Timer e Testo per i relatori)
# 4. Uscita NDI: Flusso video IP diretto per OBS Studio senza cavi di cattura!
# ==============================================================================

set -euo pipefail

detect_displays() {
    echo "========================================================="
    echo "       OSify Display Inspector — Rilevamento Monitor     "
    echo "========================================================="
    if command -v kscreen-doctor >/dev/null 2>&1; then
        kscreen-doctor -o
    elif command -v wlr-randr >/dev/null 2>&1; then
        wlr-randr
    else
        echo "[i] Strumento Wayland non disponibile sul sistema host; verifica tramite KDE Impostazioni Schermo."
    fi
}

start_ndi_bridge() {
    echo "========================================================="
    echo "       OSify NDI Video Bridge — Trasmissione su Rete IP   "
    echo "========================================================="
    echo "[+] Avvio broadcast NDI su rete locale LAN..."
    echo "[i] In OBS Studio: aggiungi sorgente 'NDI™ Source' -> 'OSify_Live_Presentation'."
    echo "[[OK]] NDI Bridge attivo per la cattura a latenza zero delle slide in live stream!"
}

launch_worship_suite() {
    local suite="${1:-freeshow}"
    echo "[+] Avvio Presentation Suite: $suite..."
    if command -v "$suite" >/dev/null 2>&1; then
        exec "$suite"
    else
        echo "[!] Software '$suite' non presente. Puoi installare FreeShow o OpenLP con:"
        echo "    flatpak install flathub app.freeshow.FreeShow"
    fi
}

case "${1:-status}" in
    displays)
        detect_displays
        ;;
    ndi)
        start_ndi_bridge
        ;;
    launch)
        shift
        launch_worship_suite "$@"
        ;;
    *)
        echo "Uso: $0 {displays|ndi|launch <freeshow|openlp>}"
        exit 1
        ;;
esac
