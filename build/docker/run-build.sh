#!/usr/bin/env bash
# ==============================================================================
# OSify Docker ISO Builder Runner
# ==============================================================================
# Esegue la compilazione automatizzata dell'ISO di OSify dentro container Docker.
# Funziona su macOS (Apple Silicon / Intel) e su Linux.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERRORE] Docker non è installato o non è in esecuzione nel sistema." >&2
    echo "         Avvia Docker Desktop per procedere." >&2
    exit 1
fi

echo "========================================================="
echo "       OSify Containerized ISO Build System              "
echo "========================================================="

echo "[+] Costruzione immagine builder Docker (Arch Linux x86-64-v3)..."
docker build -t osify-builder -f "$SCRIPT_DIR/Dockerfile" "$SCRIPT_DIR"

echo "[+] Avvio compilazione ISO all'interno del container isolato..."
docker run --rm --privileged \
    -v "$REPO_ROOT:/workspace" \
    osify-builder

echo "[[OK]] Compilazione completata! Controlla la directory build/out/ per l'ISO finale."
