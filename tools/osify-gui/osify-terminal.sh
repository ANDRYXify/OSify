#!/bin/sh
# ==============================================================================
# OSify Terminal Launcher con Fastfetch / Hardware Forensics Banner
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

# Mostra il banner di benvenuto OSify se in ambiente interattivo
cat << "EOF"
[1;36m  ██████╗ ███████╗██╗███████╗██╗   ██╗[0m
[1;35m ██╔═══██╗██╔════╝██║██╔════╝╚██╗ ██╔╝[0m
[1;34m ██║   ██║███████╗██║█████╗   ╚████╔╝ [0m
[1;36m ██║   ██║╚════██║██║██╔══╝    ╚██╔╝  [0m
[1;32m ╚██████╔╝███████║██║██║        ██║   [0m
[1;30m  ╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝   [0m
[1;37m OSify Vintage Edition — Ingegnerizzato da Andrea Taliento (ANDRYXify)[0m
----------------------------------------------------------------------
EOF

echo "[1;33m[SISTEMA][0m  OSify Universal Live OS (32-bit i686)"
echo "[1;33m[KERNEL][0m   $(uname -srm)"
echo "[1;33m[CPU][0m      $(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//' || uname -m)"
echo "[1;33m[MEMORIA][0m  $(awk '/MemAvailable/ {print int($2/1024)"MB liberi su "}' /proc/meminfo 2>/dev/null)$(awk '/MemTotal/ {print int($2/1024)"MB totali"}' /proc/meminfo 2>/dev/null)"
echo "[1;33m[SCHERMO][0m  $(xrandr 2>/dev/null | grep -o '[0-9]\+x[0-9]\+' | head -n1 || echo '1024x600 WSVGA')"
echo "----------------------------------------------------------------------"
echo "[1;32mComandi rapidi disponibili:[0m"
echo "  [1;36mosify-hud[0m        - Quick Access HUD (Prestazioni, zRAM & Scaling)"
echo "  [1;36mosify-taskmanager[0m- Process Commander (Task Manager Grafico)"
echo "  [1;36mosify-settings[0m   - Centro di Controllo Impostazioni"
echo "  [1;36mosify-install[0m    - Installatore Guidato su Disco Fisso"
echo "  [1;36mosify-cleanmem[0m   - Pulizia e Compressione Istantanea RAM"
echo ""

# Avvia la shell dell'utente
if [ -x /bin/bash ]; then
    exec /bin/bash -i
else
    exec /bin/sh -i
fi
