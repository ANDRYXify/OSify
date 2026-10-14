#!/bin/sh
# ==============================================================================
# OSify Fastfetch & Neofetch Native Engine (Zero Dipendenze, Ultra-Rapido)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# ==============================================================================

C_RESET=$(printf '\033[0m')
C_BOLD=$(printf '\033[1m')
C_CYAN=$(printf '\033[1;36m')
C_MAGENTA=$(printf '\033[1;35m')
C_BLUE=$(printf '\033[1;34m')
C_GREEN=$(printf '\033[1;32m')
C_YELLOW=$(printf '\033[1;33m')
C_WHITE=$(printf '\033[1;37m')

# Metriche hardware
OS_NAME="OSify $(cat /etc/osify-version 2>/dev/null || echo '1.5.0') (Vintage Universal)"
HOST_NAME="$(cat /etc/hostname 2>/dev/null || hostname 2>/dev/null || echo 'osify')"
USER_NAME="$(whoami)"
KERNEL_VER="$(uname -srm)"
UPTIME_STR="$(uptime -p 2>/dev/null || uptime | awk -F',' '{print $1}')"

CPU_NAME=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//')
[ -z "$CPU_NAME" ] && CPU_NAME="$(uname -m)"
CPU_CORES=$(grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo 1)

RAM_AVAIL_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 512)
RAM_TOTAL_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 1024)
RAM_USED_MB=$((RAM_TOTAL_MB - RAM_AVAIL_MB))
[ "$RAM_USED_MB" -lt 0 ] && RAM_USED_MB=0

RES_STR=$(xrandr 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1 || echo "1024x600")
WM_NAME="Openbox (OSify Supervisor)"

# Output affiancato Logo ANSI + Dati di Sistema
cat << EOF

${C_CYAN}    ██████╗ ███████╗${C_RESET}     ${C_BOLD}${C_WHITE}${USER_NAME}${C_RESET}@${C_BOLD}${C_CYAN}${HOST_NAME}${C_RESET}
${C_MAGENTA}   ██╔═══██╗██╔════╝${C_RESET}     ----------------------------------------
${C_BLUE}   ██║   ██║███████╗${C_RESET}     ${C_CYAN}OS:${C_RESET}        $OS_NAME
${C_CYAN}   ██║   ██║╚════██║${C_RESET}     ${C_CYAN}Kernel:${C_RESET}    $KERNEL_VER
${C_GREEN}   ╚██████╔╝███████║${C_RESET}     ${C_CYAN}Uptime:${C_RESET}    $UPTIME_STR
${C_WHITE}    ╚═════╝ ╚══════╝${C_RESET}     ${C_CYAN}WM:${C_RESET}        $WM_NAME
${C_BLUE}   ███████╗██╗██╗   ${C_RESET}     ${C_CYAN}Display:${C_RESET}   $RES_STR
${C_CYAN}   ██╔════╝██║██║   ${C_RESET}     ${C_CYAN}CPU:${C_RESET}       $CPU_NAME ($CPU_CORES Core)
${C_GREEN}   █████╗  ██║██║   ${C_RESET}     ${C_CYAN}Memoria:${C_RESET}   ${RAM_USED_MB}MiB / ${RAM_TOTAL_MB}MiB
${C_YELLOW}   ██╔══╝  ██║██║   ${C_RESET}     ${C_CYAN}Ingegnere:${C_RESET} Andrea Taliento (ANDRYXify)
${C_WHITE}   ██║     ██║██████${C_RESET}     
${C_MAGENTA}   ╚═╝     ╚═╝╚═════${C_RESET}     ${C_CYAN}███${C_RESET}${C_MAGENTA}███${C_RESET}${C_BLUE}███${C_RESET}${C_GREEN}███${C_RESET}${C_YELLOW}███${C_RESET}${C_WHITE}███${C_RESET}

EOF
