#!/usr/bin/env bash
# ==============================================================================
# OSify Universal APK Runner — Transparent Android Application Handler
# ==============================================================================
# Invocato dal kernel per installare ed eseguire pacchetti Android (.apk)
# all'interno del container Waydroid LXC con accelerazione GPU diretta Mesa DRI3.
# ==============================================================================

set -euo pipefail

APK_FILE="${1:-}"

if [[ -z "$APK_FILE" || ! -f "$APK_FILE" ]]; then
    echo "[ERRORE] File APK non valido: $APK_FILE" >&2
    exit 1
fi

if ! command -v waydroid >/dev/null 2>&1; then
    echo "[ERRORE] Sottosistema Android (Waydroid) non installato. Abilitalo con: osify-ctl block enable android" >&2
    exit 1
fi

echo "[OSify UEM] Installazione applicazione Android in corso: $(basename "$APK_FILE")..."
waydroid app install "$APK_FILE"

# Tenta di estrarre il package name ed eseguirlo se aapt e' disponibile
if command -v aapt >/dev/null 2>&1; then
    PKG_NAME=$(aapt dump badging "$APK_FILE" | awk -F"'" '/package: name=/{print $2}')
    if [[ -n "$PKG_NAME" ]]; then
        echo "[OSify UEM] Avvio applicazione: $PKG_NAME..."
        exec waydroid app launch "$PKG_NAME"
    fi
fi
