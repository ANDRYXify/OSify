#!/bin/sh
# ==============================================================================
# OSify Cyber-Dock — Barra di Emergenza & Dock Autonomo di Riserva
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Garantisce che sul desktop sia SEMPRE presente una barra delle applicazioni
# anche se LXPanel dovesse subire crash o anomalie grafiche.
# ==============================================================================

if pgrep -x lxpanel >/dev/null 2>&1; then
    # Se LXPanel è già attivo, non serve duplicare
    exit 0
fi

# Se abbiamo YAD, possiamo creare una barra / notification dock ultra-leggera
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    # YAD Notification icon o panel bar
    yad --notification \
        --image="/usr/share/pixmaps/osify-drawer.png" \
        --text="OSify Cyber-Bar • Clicca per aprire le Applicazioni" \
        --command="/usr/bin/osify-app-drawer" 2>/dev/null &
fi

# Fallback xclock / monitor minimale se necessario
if command -v xsetroot >/dev/null 2>&1; then
    xsetroot -name "OSify $(date +'%H:%M') • Super/F1 per App Drawer" 2>/dev/null || true
fi
