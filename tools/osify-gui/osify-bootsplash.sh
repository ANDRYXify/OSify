#!/bin/sh
# ==============================================================================
# OSify Universal Bootsplash Launcher
# ==============================================================================
# Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
# Mostra la schermata di caricamento macOS con logo e progress bar
# ==============================================================================

if command -v python3 >/dev/null 2>&1 && [ -f /usr/bin/osify-bootsplash.py ]; then
    python3 /usr/bin/osify-bootsplash.py
    exit 0
fi

# Fallback grafico nativo YAD / GTK2
SPLASH_IMG="/usr/share/pixmaps/osify-bootsplash.jpg"
if [ ! -f "$SPLASH_IMG" ]; then
    SPLASH_IMG="/usr/share/images/osify-wallpaper.jpg"
fi

if command -v yad >/dev/null 2>&1 && [ -f "$SPLASH_IMG" ]; then
    yad --title="OSify" \
        --undecorated \
        --center \
        --image="$SPLASH_IMG" \
        --timeout=2 \
        --no-buttons \
        --width=640 --height=400 2>/dev/null || true
fi
