#!/bin/sh
# ==============================================================================
# OSify App Drawer Launcher
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

if [ -x /usr/bin/osify-app-drawer.py ]; then
    exec /usr/bin/osify-app-drawer.py "$@"
elif [ -f /opt/osify/tools/osify-gui/osify-app-drawer.py ]; then
    exec python3 /opt/osify/tools/osify-gui/osify-app-drawer.py "$@"
else
    exec /usr/bin/osify-hub "$@"
fi
