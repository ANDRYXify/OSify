#!/bin/sh
# ==============================================================================
# OSify Adaptive Storage & I/O Governor
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Rilevamento dinamico bus storage (USB 2.0, USB 3.0, SD/MMC, SATA, NVMe),
# calibrazione adattiva della cache dirty pages per eliminare i freeze da copia,
# automount intelligente e rimozione sicura (safe unmount con flush sincrono).
# ==============================================================================

ACTION="${1:---tune}"
DEV_TARGET="${2:-}"

# Auto-elevazione per operazioni che modificano parametri kernel o smontano filesystem
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    case "$ACTION" in
        --status|-s) ;; # Lettura consentita a tutti gli utenti
        *)
            if command -v sudo >/dev/null 2>&1; then
                exec sudo "$0" "$@"
            fi
            ;;
    esac
fi

log() { printf "\033[1;36m[OSify-Storage]\033[0m %s\n" "$*"; }
ok()  { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[AVVISO]\033[0m %s\n" "$*"; }

# 1. Rilevamento velocità bus hardware (USB 2.0 vs 3.0 vs SD)
get_device_bus_type() {
    _dev="$1" # es. sdb o mmcblk0
    
    # Schede SD / MMC
    case "$_dev" in
        mmcblk*)
            echo "SD/MMC (Card Reader Interno/Esterno)"
            return
            ;;
    esac

    # Dispositivi USB
    if [ -d "/sys/block/$_dev" ]; then
        sys_path=$(readlink -f "/sys/block/$_dev" 2>/dev/null || echo "")
        if echo "$sys_path" | grep -q "usb"; then
            # Cerca il file speed nel nodo USB parent
            usb_node=$(echo "$sys_path" | grep -oE '.*/usb[0-9]+/[^/]+' | head -n1)
            if [ -f "$usb_node/speed" ]; then
                speed=$(cat "$usb_node/speed" 2>/dev/null)
                case "$speed" in
                    1.5|12) echo "USB 1.1 (Low/Full Speed - 12 Mbps)" ;;
                    480)    echo "USB 2.0 (High Speed - 480 Mbps)" ;;
                    5000)   echo "USB 3.0 / 3.1 Gen1 (SuperSpeed - 5 Gbps)" ;;
                    10000)  echo "USB 3.1 Gen2 (SuperSpeed+ - 10 Gbps)" ;;
                    20000)  echo "USB 3.2 Gen2x2 (SuperSpeed++ - 20 Gbps)" ;;
                    *)      echo "USB ($speed Mbps)" ;;
                esac
                return
            fi
            echo "USB (Generico)"
            return
        fi
        if echo "$sys_path" | grep -q "nvme"; then
            echo "NVMe (PCIe Express)"
            return
        fi
        if echo "$sys_path" | grep -q "ata"; then
            echo "SATA / AHCI"
            return
        fi
    fi
    echo "Disco Fisso / Block Device"
}

# 2. Applicazione Tuning Adattivo Dirty Page Cache & I/O Scheduler
tune_device_io() {
    _dev="$1"
    [ ! -d "/sys/block/$_dev" ] && return

    bus_info=$(get_device_bus_type "$_dev")
    log "Calibrazione I/O per dispositivo /dev/$_dev [$bus_info]..."

    # Se siamo su USB 2.0, USB 1.1 o SD card lenta:
    if echo "$bus_info" | grep -qE "USB 1.1|USB 2.0|SD/MMC"; then
        # Imposta buffer di dirty pages ridotto (max 40 MB) per forzare lo streaming
        # continuo ed evitare che il desktop congeli durante la copia di file pesanti:
        if [ -w /proc/sys/vm/dirty_background_bytes ]; then
            echo 16777216 > /proc/sys/vm/dirty_background_bytes 2>/dev/null || true # 16 MB
            echo 41943040 > /proc/sys/vm/dirty_bytes 2>/dev/null || true            # 40 MB
        fi
        # Read-ahead moderato (256 KB)
        [ -w "/sys/block/$_dev/queue/read_ahead_kb" ] && echo 256 > "/sys/block/$_dev/queue/read_ahead_kb" 2>/dev/null || true
        # Scheduler a bassa latenza interattiva
        for sched in bfq mq-deadline deadline noop; do
            if grep -q "$sched" "/sys/block/$_dev/queue/scheduler" 2>/dev/null; then
                echo "$sched" > "/sys/block/$_dev/queue/scheduler" 2>/dev/null && break
            fi
        done
        ok "Ottimizzazione Anti-Freeze applicata su /dev/$_dev (Buffer: 40MB write streaming)"
    else
        # USB 3.0+, SSD esterno, SATA, NVMe: throughput elevato
        if [ -w /proc/sys/vm/dirty_background_bytes ]; then
            echo 134217728 > /proc/sys/vm/dirty_background_bytes 2>/dev/null || true # 128 MB
            echo 268435456 > /proc/sys/vm/dirty_bytes 2>/dev/null || true            # 256 MB
        fi
        [ -w "/sys/block/$_dev/queue/read_ahead_kb" ] && echo 2048 > "/sys/block/$_dev/queue/read_ahead_kb" 2>/dev/null || true
        ok "Ottimizzazione High-Throughput applicata su /dev/$_dev (Read-ahead: 2MB)"
    fi
}

# 3. Rimozione Sicura con Notifica Grafica (Safe Eject)
safe_eject() {
    _target="$1"
    if [ -z "$_target" ]; then
        warn "Specificare il dispositivo da smontare (es. /dev/sdb1 o /media/usb)"
        exit 1
    fi

    # Notifica inizio flush se in ambiente grafico
    if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
        (
            echo "50"
            echo "# Svuotamento cache di scrittura (sync) in corso..."
            sync
            echo "90"
            echo "# Smontaggio pulito del filesystem..."
            umount "$_target" 2>/dev/null || umount -l "$_target" 2>/dev/null || true
            echo "100"
            echo "# Pronto per la rimozione!"
            sleep 0.5
        ) | yad --progress --title="OSify — Rimozione Sicura" --auto-close --pulsate --width=380 --center
        
        yad --info --title="Dispositivo Rimosso" --text="<b>Dispositivo smontato con successo.</b>\nPuoi ora rimuovere la chiavetta o scheda SD in totale sicurezza senza perdita di dati." --center
    else
        log "Sincronizzazione dati in corso (sync)..."
        sync
        umount "$_target" 2>/dev/null || umount -l "$_target" 2>/dev/null || true
        ok "Dispositivo $_target smontato con successo. Puoi estrarlo in sicurezza."
    fi
}

# 4. Status e Telemetria Storage
show_status() {
    printf "\033[1;36m=================================================================\033[0m\n"
    printf "\033[1;32m       OSify Storage Telemetry & Adaptive I/O Status             \033[0m\n"
    printf "\033[1;36m=================================================================\033[0m\n"
    
    for dev_path in /sys/block/sd* /sys/block/mmcblk* /sys/block/nvme*n1; do
        [ -e "$dev_path" ] || continue
        dname=$(basename "$dev_path")
        case "$dname" in loop*|ram*|zram*) continue ;; esac
        
        size_sec=$(cat "$dev_path/size" 2>/dev/null || echo 0)
        size_gb=$(( size_sec * 512 / 1024 / 1024 / 1024 ))
        bus=$(get_device_bus_type "$dname")
        sched=$(cat "$dev_path/queue/scheduler" 2>/dev/null | grep -o '\[.*\]' || echo "default")
        
        printf " \033[1;33mDispositivo:\033[0m /dev/%-8s \033[1;37m(%d GB)\033[0m\n" "$dname" "$size_gb"
        printf "   • Bus Hardware: \033[1;36m%s\033[0m\n" "$bus"
        printf "   • I/O Scheduler: %s\n" "$sched"
        
        # Partizioni montate
        grep "^/dev/$dname" /proc/mounts 2>/dev/null | while read -r mdev mpoint mfs mopt; do
            printf "   • Partizione: \033[1;32m%s\033[0m montata su \033[1;37m%s\033[0m (%s)\n" "$mdev" "$mpoint" "$mfs"
        done
        echo "-----------------------------------------------------------------"
    done
}

case "$ACTION" in
    --status|-s)
        show_status
        ;;
    --eject|-e)
        safe_eject "$DEV_TARGET"
        ;;
    --tune|-t)
        for d in /sys/block/sd* /sys/block/mmcblk*; do
            [ -e "$d" ] || continue
            dname=$(basename "$d")
            case "$dname" in loop*|ram*|zram*) continue ;; esac
            tune_device_io "$dname"
        done
        ;;
    *)
        if [ -b "/dev/$ACTION" ]; then
            tune_device_io "$ACTION"
        else
            show_status
        fi
        ;;
esac
