#!/bin/sh
# ==============================================================================
# OSify Process Commander — Gestione Attività e Monitor Risorse
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# ==============================================================================

if command -v htop >/dev/null 2>&1; then
    exec /usr/bin/terminal -geometry 95x28 -T "Gestione Attivita OSify" -e /usr/bin/htop
elif command -v top >/dev/null 2>&1; then
    exec /usr/bin/terminal -geometry 90x25 -T "Gestione Attivita OSify" -e /usr/bin/top
else
    exec /usr/bin/terminal -geometry 80x24 -T "Gestione Attivita OSify" -e ps -ef
fi
