#!/bin/sh
# ==============================================================================
# OSify Terminal Launcher — Interfaccia Shell Inedita & Fastfetch Banner
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# ==============================================================================

# Palette ANSI
C_RESET=$(printf '\033[0m')
C_BOLD=$(printf '\033[1m')
C_CYAN=$(printf '\033[1;36m')
C_MAGENTA=$(printf '\033[1;35m')
C_BLUE=$(printf '\033[1;34m')
C_GREEN=$(printf '\033[1;32m')
C_YELLOW=$(printf '\033[1;33m')
C_RED=$(printf '\033[1;31m')
C_WHITE=$(printf '\033[1;37m')
C_DIM=$(printf '\033[2m')

# Saluto orario
_hour=$(date +%H 2>/dev/null || echo 12)
if [ "$_hour" -ge 5 ] && [ "$_hour" -lt 13 ]; then
    GREETING="Buongiorno, Compagno!"
elif [ "$_hour" -ge 13 ] && [ "$_hour" -lt 18 ]; then
    GREETING="Buon pomeriggio, Compagno!"
elif [ "$_hour" -ge 18 ] && [ "$_hour" -lt 23 ]; then
    GREETING="Buonasera, Compagno!"
else
    GREETING="Buona notte nel Cyber-Spazio di OSify, Compagno!"
fi

# Rilevamento metriche sintetiche
CPU_MODEL=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//')
[ -z "$CPU_MODEL" ] && CPU_MODEL="$(uname -m)"

RAM_AVAIL_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "512")
RAM_TOTAL_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "1024")
RAM_USED_MB=$((RAM_TOTAL_MB - RAM_AVAIL_MB))
[ "$RAM_USED_MB" -lt 0 ] && RAM_USED_MB=0

RES_INFO=$(xrandr 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1 || echo "1024x600")

# Mostra il banner di benvenuto OSify
cat << EOF
${C_CYAN}    ██████╗ ███████╗██╗███████╗██╗   ██╗${C_RESET}
${C_MAGENTA}   ██╔═══██╗██╔════╝██║██╔════╝╚██╗ ██╔╝${C_RESET}
${C_BLUE}   ██║   ██║███████╗██║█████╗   ╚████╔╝ ${C_RESET}
${C_CYAN}   ██║   ██║╚════██║██║██╔══╝    ╚██╔╝  ${C_RESET}
${C_GREEN}   ╚██████╔╝███████║██║██║        ██║   ${C_RESET}
${C_DIM}    ╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝   ${C_RESET}
${C_WHITE}   OSify — Sistema Operativo Universale & Resurrezione Hardware${C_RESET}
EOF

echo ""
echo " ${C_GREEN}👋 $GREETING${C_RESET}"
echo "${C_BOLD}┌────────────────────────────────────────────────────────────────────────┐${C_RESET}"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Host / Utente" "$(whoami) @ $(cat /etc/hostname 2>/dev/null || echo osify)"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Edizione" "OSify $(cat /etc/osify-version 2>/dev/null || echo '1.5.0') Vintage Edition"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Kernel" "$(uname -srm)"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Processore" "$CPU_MODEL"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Memoria RAM" "${RAM_USED_MB} MB usati / ${RAM_TOTAL_MB} MB totali (${RAM_AVAIL_MB} MB liberi)"
printf "│ ${C_CYAN}%-14s${C_RESET} : %-55s │\n" "Risoluzione" "$RES_INFO (Pannello Netbook WSVGA)"
echo "${C_BOLD}└────────────────────────────────────────────────────────────────────────┘${C_RESET}"
echo ""
echo " ${C_YELLOW}⚡ Comandi Inediti OSify (Pronti all'uso):${C_RESET}"
echo "    ${C_WHITE}osify${C_RESET}          -> Apre la Dashboard Interattiva a 360°"
echo "    ${C_WHITE}osify turbo${C_RESET}    -> Spinge la CPU a 1.66GHz e attiva zRAM LZ4"
echo "    ${C_WHITE}osify pulisci${C_RESET}  -> Libera istantaneamente RAM e cache di sistema"
echo "    ${C_WHITE}osify wifi${C_RESET}     -> Scansione e connessione rapida alle reti wireless"
echo "    ${C_WHITE}osify schermo${C_RESET}  -> Risoluzioni: 1024x600, 1280x768 (Virtual HD) o HDMI"
echo "    ${C_WHITE}osify installa${C_RESET} -> Installatore guidato su disco fisso HDD/SSD"
echo "    ${C_WHITE}osify aiuto${C_RESET}    -> Manuale completo e scorciatoie da tastiera"
echo ""

# Prompt Cyber-OSify personalizzato
export PS1="${C_CYAN}⚡ [OSify:${C_GREEN}\u${C_CYAN}@${C_MAGENTA}\h ${C_YELLOW}\W${C_CYAN}]\\$ ${C_RESET}"

# Avvia la shell dell'utente in modalità interattiva
if [ -x /bin/bash ]; then
    exec /bin/bash --norc -i
else
    exec /bin/sh -i
fi
