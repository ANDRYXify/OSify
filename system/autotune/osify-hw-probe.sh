#!/bin/sh
# ==============================================================================
# OSify Universal Hardware Probe & Adaptive Driver Engine
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Rilevamento e configurazione 100% autonoma e adattiva per qualsiasi PC vintage:
# - Intel Atom, Pentium II/III/4/M, Core 2 Duo, AMD Athlon/Geode, VIA C3/C7
# - GPU Intel (i810-GMA4500), ATI Radeon (R100-R500), Nvidia (GeForce 2-8), SiS, VIA, VESA
# - Audio AC'97 (snd-intel8x0/via82xx) e Intel HDA (snd-hda-intel) con unmute adattivo
# - Touchpad Synaptics, ALPS, Elantech, TrackPoint e mouse PS/2 / USB
# - zRAM scalabile dinamicamente in base alla RAM fisica (da 256MB a 4GB)
# - I/O Scheduler (deadline/noop) calibrato per HDD IDE/PATA 4200-5400rpm o SSD
# ==============================================================================

log() { printf "\033[1;36m[OSify-HWProbe]\033[0m %s\n" "$*"; }

# 1. Rilevamento Memoria e Configurazione Adattiva zRAM
probe_memory_and_zram() {
    mem_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 1048576)
    mem_mb=$((mem_kb / 1024))
    log "Rilevata RAM fisica di sistema: ${mem_mb} MB"

    modprobe zram 2>/dev/null || true
    if [ -b /dev/zram0 ]; then
        # Calcolo dimensione zRAM adattiva
        if [ "$mem_mb" -le 512 ]; then
            # Sistemi ultra-ridotti (256MB - 512MB): zRAM pari al 100% della RAM fisica
            zram_bytes=$((mem_mb * 1024 * 1024))
            swappiness=100
            cache_pressure=100
        elif [ "$mem_mb" -le 1024 ]; then
            # Sistemi tipo Netbook Atom (1GB RAM): 1GB zRAM compresso
            zram_bytes=$((1024 * 1024 * 1024))
            swappiness=80
            cache_pressure=50
        else
            # Sistemi vintage con 2GB-4GB RAM: 1.5GB zRAM
            zram_bytes=$((1536 * 1024 * 1024))
            swappiness=60
            cache_pressure=50
        fi

        # Algoritmo di compressione più rapido disponibile per la CPU
        echo lz4 > /sys/block/zram0/comp_algorithm 2>/dev/null || echo lzo > /sys/block/zram0/comp_algorithm 2>/dev/null || true
        echo "$zram_bytes" > /sys/block/zram0/disksize 2>/dev/null || true
        mkswap /dev/zram0 >/dev/null 2>&1 || true
        swapon -p 100 /dev/zram0 2>/dev/null || true
        sysctl -w vm.swappiness="$swappiness" vm.vfs_cache_pressure="$cache_pressure" >/dev/null 2>&1 || true
        log "zRAM Swap Adattiva attivata: $((zram_bytes / 1024 / 1024)) MB (swappiness=$swappiness)"
    fi
}

# 2. Ottimizzazione CPU e Thermal Governor
probe_cpu() {
    cpu_model=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^[ \t]*//')
    [ -z "$cpu_model" ] && cpu_model="$(uname -m)"
    log "Processore Rilevato: $cpu_model"

    # Carica driver cpufreq se disponibili
    modprobe acpi-cpufreq 2>/dev/null || modprobe p4-clockmod 2>/dev/null || modprobe speedstep-ich 2>/dev/null || true

    for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        if [ -f "$g" ]; then
            # Prediligi 'ondemand' per risparmio termico su laptop/netbook, fallback 'performance'
            echo ondemand > "$g" 2>/dev/null || echo performance > "$g" 2>/dev/null || true
        fi
    done
}

# 3. Adattamento Sottosistema Grafico (Intel, ATI, NVIDIA, SiS, VIA, VESA)
probe_gpu() {
    pci_vga=$(lspci 2>/dev/null | grep -iE 'vga|3d|display' || true)
    log "Controller Video PCI: $(echo "$pci_vga" | head -n1)"

    # Se l'utente ha avviato in 'nomodeset', preserva il driver VESA o fbdev
    if grep -q "nomodeset" /proc/cmdline 2>/dev/null; then
        log "Modalità Nomodeset rilevata: attivato fallback grafico VESA universale sicuro."
        return
    fi

    case "$pci_vga" in
        *[Ii]ntel*)
            log "GPU Intel rilevata (i810/i915/GMA950/GMA3150/HD): caricamento driver i915..."
            modprobe i915 2>/dev/null || true
            ;;
        *[Aa][Tt][Ii]*|*[Rr]adeon*)
            log "GPU ATI/Radeon rilevata: caricamento driver radeon..."
            modprobe radeon 2>/dev/null || true
            ;;
        *[Nn][Vv][Ii][Dd][Ii][Aa]*)
            log "GPU NVIDIA rilevata: caricamento driver open source nouveau..."
            modprobe nouveau 2>/dev/null || true
            ;;
        *[Ss][Ii][Ss]*)
            log "Chipset SiS rilevato: caricamento driver sisfb/sis..."
            modprobe sisfb 2>/dev/null || true
            ;;
        *[Vv][Ii][Aa]*|*[Ss]3*)
            log "Chipset VIA/S3 UniChrome rilevato: caricamento viafb/openchrome..."
            modprobe viafb 2>/dev/null || true
            ;;
        *)
            log "GPU generica: KMS predefinito del kernel."
            ;;
    esac
}

# 4. Sblocco e Routing Audio Universale (AC'97 e Intel HDA)
probe_audio() {
    # Caricamento moduli comuni se non ancora attivi
    modprobe snd-hda-intel 2>/dev/null || true
    modprobe snd-intel8x0 2>/dev/null || true
    modprobe snd-via82xx 2>/dev/null || true
    modprobe snd-ens1371 2>/dev/null || true

    # Unmute su qualsiasi canale audio standard ALSA presente
    for channel in "Master" "PCM" "Speaker" "Headphone" "Front" "Surround" "Center" "LFE" "Wave" "CD" "Line Out"; do
        amixer sset "$channel" unmute 85% >/dev/null 2>&1 || true
    done
    amixer sset "Mic" mute >/dev/null 2>&1 || true
    log "Audio ALSA configurato e sbloccato su tutti i canali compatibili."
}

# 5. Adattamento Dispositivi di Puntamento (Synaptics, ALPS, Elantech, TrackPoint)
probe_input() {
    # Carica driver mouse PS/2 estesi
    modprobe psmouse 2>/dev/null || true

    # Calibrazione Touchpad se in ambiente X11
    if [ -n "$DISPLAY" ] || command -v synclient >/dev/null 2>&1; then
        synclient TapButton1=1 TapButton2=3 TapButton3=2 VertEdgeScroll=1 HorizEdgeScroll=1 CoastingSpeed=20 2>/dev/null || true
        log "Touchpad calibrato con tap-to-click e scrolling laterale."
    fi
}

# 6. Sblocco Rete e Wireless
probe_network() {
    rfkill unblock all 2>/dev/null || true

    # Carica driver Wi-Fi vintage comuni
    modprobe ath9k 2>/dev/null || true
    modprobe ath5k 2>/dev/null || true
    modprobe r8169 2>/dev/null || true
    modprobe r8187se 2>/dev/null || true
    modprobe rtl8192se 2>/dev/null || true
    modprobe b43 2>/dev/null || true
    modprobe ipw2200 2>/dev/null || true
    modprobe iwl3945 2>/dev/null || true

    # Attiva interfaccia di loopback se non attiva
    ifconfig lo 127.0.0.1 up 2>/dev/null || true
    log "Interfacce di rete e controller wireless abilitati."
}

# 7. Ottimizzazione I/O Scheduler per Hard Disk Lenti (IDE/PATA/SATA 5400rpm)
probe_storage_tuning() {
    for dev in /sys/block/sd* /sys/block/hd*; do
        if [ -d "$dev" ]; then
            rotational=$(cat "$dev/queue/rotational" 2>/dev/null || echo 1)
            sched_file="$dev/queue/scheduler"
            if [ -f "$sched_file" ]; then
                if [ "$rotational" = "1" ]; then
                    # Disco meccanico lento: prediligi 'deadline' o 'bfq'
                    echo deadline > "$sched_file" 2>/dev/null || echo bfq > "$sched_file" 2>/dev/null || true
                else
                    # SSD / CompactFlash / SD / DOM: prediligi 'noop' o 'none'
                    echo none > "$sched_file" 2>/dev/null || echo noop > "$sched_file" 2>/dev/null || true
                fi
            fi
        fi
    done
    log "I/O Scheduler storage ottimizzato in base al tipo di supporto."
}

main() {
    log "Avvio Scansione e Inizializzazione Hardware Autonoma OSify..."
    probe_memory_and_zram
    probe_cpu
    probe_gpu
    probe_audio
    probe_input
    probe_network
    probe_storage_tuning
    log "Inizializzazione completata: la macchina è pronta all'uso."
}

main "$@"
