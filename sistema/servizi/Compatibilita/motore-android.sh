#!/usr/bin/env bash
# ==============================================================================
# OSify Android Runtime — Waydroid Native Container Engine
# ==============================================================================
# Esegue applicazioni e giochi Android (APK) direttamente sul kernel Linux host
# tramite container LXC e accelerazione grafica diretta GPU (Mesa/dri3).
# Include installazione automatizzata del bridge ARM (libndk) per app ARM64 su x86.
# ==============================================================================

set -euo pipefail

ACTION="${1:-status}"

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[ERRORE] Questa operazione richiede privilegi di root." >&2
        exit 1
    fi
}

init_waydroid() {
    check_root
    echo "========================================================="
    echo "       OSify Android Engine — Inizializzazione LXC       "
    echo "========================================================="

    # 1. Moduli kernel richiesti: binder_linux, ashmem
    echo "[+] Caricamento moduli kernel Android (binder)..."
    modprobe binder_linux || true

    # 2. Inizializzazione immagini Waydroid con supporto Google Apps / MicroG
    echo "[+] Inizializzazione immagini di sistema Waydroid..."
    if ! waydroid status | grep -q "INITIALIZED"; then
        waydroid init -s GAPPS || waydroid init
    fi

    # 3. Abilitazione servizio di background
    systemctl enable --now waydroid-container.service

    # 4. Configurazione traduzione ARM (libndk) per APK compilati per smartphone
    echo "[+] Installazione bridge di traduzione ARM64 -> x86_64 (libndk)..."
    if command -v waydroid-extras >/dev/null 2>&1; then
        waydroid-extras install libndk
    fi

    echo "[[OK]] Runtime Android configurato! Le app Android compariranno nativamente nel menu di KDE Plasma."
}

launch_app() {
    local package_name="${2:-}"
    if [[ -z "$package_name" ]]; then
        echo "Uso: $0 launch <nome.package.android>"
        exit 1
    fi

    # Assicura che la sessione Waydroid sia avviata
    if ! waydroid status | grep -q "RUNNING"; then
        waydroid session start &
        sleep 2
    fi

    echo "[+] Avvio app Android: $package_name"
    waydroid app launch "$package_name"
}

case "$ACTION" in
    init)
        init_waydroid
        ;;
    start)
        waydroid session start
        ;;
    stop)
        waydroid session stop
        ;;
    launch)
        launch_app "$@"
        ;;
    status)
        waydroid status 2>/dev/null || echo "Waydroid non installato o non inizializzato."
        ;;
    *)
        echo "Uso: $0 {init|start|stop|launch <pkg>|status}"
        exit 1
        ;;
esac
