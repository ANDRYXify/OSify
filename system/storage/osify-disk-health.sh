#!/usr/bin/env bash
# ==============================================================================
# OSify Disk Health & Storage Telemetry — Diagnostica Dischi & S.M.A.R.T.
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

analyze_storage() {
    local report=""
    report+="=== STATO PARTIZIONI E SPAZIO LIBERO ===\n"
    report+="$(df -h -x tmpfs -x devtmpfs 2>/dev/null | awk 'NR==1 || /^\/dev/' || df -h)\n\n"

    report+="=== DISCHI FISICI RILEVATI ===\n"
    for d in /sys/block/sd* /sys/block/hd* /sys/block/nvme*n1 /sys/block/mmcblk*; do
        [ -e "$d" ] || continue
        dname=$(basename "$d")
        case "$dname" in loop*|ram*|zram*) continue ;; esac
        
        sectors=$(cat "$d/size" 2>/dev/null || echo 0)
        size_gb=$(( sectors * 512 / 1024 / 1024 / 1024 ))
        model=""
        [ -f "$d/device/model" ] && model=$(cat "$d/device/model" | tr -s ' ')
        
        report+="• Dispositivo: /dev/$dname (${size_gb} GB) $model\n"
        
        # Test SMART se smartctl è disponibile
        if command -v smartctl >/dev/null 2>&1; then
            smart_res=$(sudo smartctl -H "/dev/$dname" 2>/dev/null | grep -E "result:|PASSED|FAILED" || echo "SMART non supportato")
            report+="  Stato SMART: $smart_res\n"
        fi
    done
    echo -e "$report"
}

launch_gui() {
    local info
    info="$(analyze_storage)"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        yad --text-info --title="Salute Dischi & Archiviazione OSify" \
            --text="<b>Radiografia dello Spazio e Integrita dei Dischi</b>" \
            --window-icon="/usr/share/pixmaps/osify-files.png" \
            --width=540 --height=380 --center \
            --button="Chiudi:0" <<< "$info" >/dev/null 2>&1 || true
    else
        echo -e "$info"
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    cli|status) analyze_storage ;;
    *) echo "Uso: $0 {gui|status}" ;;
esac
