#!/bin/sh
# ==============================================================================
# OSify Web Browser Launcher & Hardware Ad-Shield
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Avvia il browser grafico più performante presente sul sistema con
# blocco automatico di annunci pubblicitari pesanti per volare su vecchie CPU.
# ==============================================================================

# Applicazione adblock a livello host se necessario
if [ -x /usr/bin/osify-adblock ]; then
    /usr/bin/osify-adblock --silent 2>/dev/null || true
fi

URL="${1:-https://www.google.com}"

if command -v dillo >/dev/null 2>&1; then
    exec dillo "$URL"
elif command -v falkon >/dev/null 2>&1; then
    exec falkon "$URL"
elif command -v midori >/dev/null 2>&1; then
    exec midori "$URL"
elif command -v firefox >/dev/null 2>&1; then
    exec firefox "$URL"
elif command -v chromium >/dev/null 2>&1; then
    exec chromium --no-sandbox "$URL"
else
    # Fallback su qualsiasi browser di sistema
    exec xdg-open "$URL"
fi
