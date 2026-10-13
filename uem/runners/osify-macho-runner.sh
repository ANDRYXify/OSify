#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Mach-O Runner — Transparent Darwin / macOS Application Handler
# ==============================================================================
# Invocato dal kernel per eseguire binari nativi Darwin/macOS (Mach-O)
# o bundle applicativi (.app) tramite il translation layer Darling.
# ==============================================================================

set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" || (! -f "$TARGET" && ! -d "$TARGET") ]]; then
    echo "[ERRORE] File o bundle macOS non valido: $TARGET" >&2
    exit 1
fi

# Se è una directory bundle .app, individua il binario principale in Contents/MacOS
EXECUTABLE="$TARGET"
if [[ -d "$TARGET" && "$TARGET" =~ \.app/?$ ]]; then
    MACOS_DIR="$TARGET/Contents/MacOS"
    if [[ -d "$MACOS_DIR" ]]; then
        # Prende il primo eseguibile presente nella cartella MacOS
        CANDIDATE=$(find "$MACOS_DIR" -maxdepth 1 -type f -perm -111 2>/dev/null | head -n 1 || true)
        if [[ -n "$CANDIDATE" && -f "$CANDIDATE" ]]; then
            EXECUTABLE="$CANDIDATE"
        fi
    fi
fi

if command -v darling >/dev/null 2>&1; then
    exec darling shell "$EXECUTABLE" "${@:2}"
else
    echo "[ERRORE] Runtime Darwin (Darling) non installato nel sistema host." >&2
    echo "         Abilitalo tramite: osify-ctl block enable darwin" >&2
    exit 1
fi
