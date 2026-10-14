#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Image Viewer Wrapper
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

IMG="${1:-}"

if [ -z "$IMG" ]; then
    echo "Uso: $0 <percorso_immagine>"
    exit 0
fi

if command -v gpicview >/dev/null 2>&1; then
    exec gpicview "$IMG"
elif command -v viewnior >/dev/null 2>&1; then
    exec viewnior "$IMG"
elif command -v feh >/dev/null 2>&1; then
    exec feh -. "$IMG"
elif command -v display >/dev/null 2>&1; then
    exec display "$IMG"
elif command -v dillo >/dev/null 2>&1; then
    ABS_IMG="$(readlink -f "$IMG" 2>/dev/null || echo "$IMG")"
    exec dillo "file://${ABS_IMG}"
else
    echo "[!] Nessun visualizzatore immagini grafico rilevato."
fi
