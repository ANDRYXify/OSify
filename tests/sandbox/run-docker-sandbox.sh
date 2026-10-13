#!/usr/bin/env bash
# ==============================================================================
# OSify Docker Interactive Linux Sandbox (by Andryx)
# ==============================================================================
# Avvia un ambiente Linux completo e isolato all'interno di un container Docker,
# montando il codice di OSify in /workspace.
# Consente di testare i tool, gli script sysctl, i comandi di rete e la CLI osify-ctl
# senza rischiare di toccare il sistema host.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERRORE] Docker non è installato o in esecuzione nel sistema." >&2
    exit 1
fi

echo "========================================================="
echo "       OSify Interactive Docker Sandbox (Arch Linux)     "
echo "========================================================="
echo "[+] Root di progetto montata su: /workspace"
echo "[+] Avvio shell Linux interattiva con permessi elevati..."
echo "[i] Digita 'exit' per uscire dal sandbox."
echo "========================================================="

docker run --rm -it --privileged \
    -v "$REPO_ROOT:/workspace" \
    -w /workspace \
    archlinux:latest \
    /bin/bash -c "
        echo '[Sandbox] Aggiornamento keyring e installazione Python & Bash...';
        pacman -Sy --noconfirm python bash iproute2 sudo >/dev/null 2>&1 || true;
        echo '[✓] Ambiente pronto!';
        echo '[i] Prova a digitare: ./tools/osify-ctl status';
        echo '[i] Prova a digitare: ./tools/osify-ctl block list';
        exec /bin/bash
    "
