#!/usr/bin/env bash
# ==============================================================================
# OSify System Hardware Spec Report — Scheda Tecnica & Diagnostica Completa
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Rilevamento deterministico e dettagliato di CPU, RAM, GPU, dischi, batteria,
# schede di rete e BIOS con esportazione istantanea report per assistenza tecnica.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-settings.png"

generate_report() {
    local cpu_model cpu_cores cpu_arch
    cpu_model="$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^[ \t]*//' || echo "CPU Standard")"
    cpu_cores="$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo 1)"
    cpu_arch="$(uname -m)"

    local ram_total ram_avail
    ram_total="$(grep "MemTotal:" /proc/meminfo 2>/dev/null | awk '{print int($2/1024) " MB"}' || echo "N/D")"
    ram_avail="$(grep "MemAvailable:" /proc/meminfo 2>/dev/null | awk '{print int($2/1024) " MB"}' || echo "N/D")"

    local gpu_info
    gpu_info="$(lspci 2>/dev/null | grep -iE 'vga|3d|display' | cut -d: -f3 | sed 's/^[ \t]*//' | head -n1 || echo "Adattatore Grafico Standard")"
    [ -z "$gpu_info" ] && gpu_info="Adattatore Video KMS"

    local screen_res
    screen_res="$(xrandr --current 2>/dev/null | grep -m1 "\*" | awk '{print $1}' || echo "Standard")"

    local disk_info
    disk_info="$(df -h / 2>/dev/null | awk 'NR==2 {print $2 " Totali (" $4 " Disponibili, " $5 " in uso)"}' || echo "N/D")"

    local bat_status
    if [ -d /sys/class/power_supply/BAT0 ] || [ -d /sys/class/power_supply/BAT1 ]; then
        local b_path
        b_path="$(ls -d /sys/class/power_supply/BAT* 2>/dev/null | head -n1)"
        local b_cap b_stat
        b_cap="$(cat "$b_path/capacity" 2>/dev/null || echo "100")"
        b_stat="$(cat "$b_path/status" 2>/dev/null || echo "Presente")"
        bat_status="$b_cap% ($b_stat)"
    else
        bat_status="Alimentazione Fissa / Rete Elettrica"
    fi

    local bios_vendor bios_ver bios_date
    bios_vendor="$(cat /sys/class/dmi/id/bios_vendor 2>/dev/null || cat /sys/devices/virtual/dmi/id/bios_vendor 2>/dev/null || echo "Generico")"
    bios_ver="$(cat /sys/class/dmi/id/bios_version 2>/dev/null || cat /sys/devices/virtual/dmi/id/bios_version 2>/dev/null || echo "N/D")"
    bios_date="$(cat /sys/class/dmi/id/bios_date 2>/dev/null || cat /sys/devices/virtual/dmi/id/bios_date 2>/dev/null || echo "N/D")"

    local kernel_ver os_name
    kernel_ver="$(uname -r)"
    os_name="OSify Universal Operating System"

    cat <<EOF
================================================================================
                    SCHEDA TECNICA HARDWARE — OSIFY
================================================================================
Sistema Operativo  : $os_name
Kernel Linux       : $kernel_ver ($cpu_arch)
Data Diagnostica   : $(date '+%Y-%m-%d %H:%M:%S')
--------------------------------------------------------------------------------
PROCESSORE (CPU)
Modello            : $cpu_model
Core / Thread      : $cpu_cores
Architettura       : $cpu_arch

MEMORIA RAM
Capacità Totale    : $ram_total
Memoria Disponibile: $ram_avail

GRAFICA E DISPLAY
Scheda Video       : $gpu_info
Risoluzione Attuale: $screen_res

ARCHIVIAZIONE & DISCO
Spazio Filesystem  : $disk_info

ALIMENTAZIONE & BATTERIA
Stato Batteria     : $bat_status

SCHEDA MADRE & FIRMWARE
Produttore BIOS    : $bios_vendor
Versione Firmware  : $bios_ver (Rilascio: $bios_date)
================================================================================
EOF
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        generate_report
        return 0
    fi

    local rep
    rep="$(generate_report)"
    local report_file="${HOME:-/root}/Desktop/Report_Hardware_OSify.txt"

    yad --text-info \
        --title="OSify — Scheda Tecnica e Diagnostica Hardware" \
        --window-icon="$LOGO_IMG" \
        --width=620 --height=450 --center \
        --button="Esporta sul Desktop:2" \
        --button="Chiudi:0" <<< "$rep"
    local ret=$?

    if [ $ret -eq 2 ]; then
        echo "$rep" > "$report_file"
        yad --info --title="Report Salvato" \
            --text="<big><b>Scheda Tecnica Esportata!</b></big>\n\nSalvata sul Desktop in:\n<b>$report_file</b>" \
            --center 2>/dev/null || true
    fi
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui
        else
            generate_report
        fi
        ;;
    report|cli|text)
        generate_report
        ;;
    *)
        echo "Uso: $0 {gui|report}"
        exit 1
        ;;
esac
