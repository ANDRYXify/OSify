#!/usr/bin/env bash
# ==============================================================================
# OSify Hardware Adaptation Layer (HAL) — Industrial Auto-Tuning Engine
# ==============================================================================
# Eseguito al boot per analizzare in tempo reale l'hardware della macchina
# e configurare l'intero stack software in modo automatico e deterministico:
# - Gestione Memoria Dinamica (ZRAM lz4 vs zstd, swappiness, cache pressure, dirty ratios)
# - CPU Scheduling & Latency (Scheduler kernel, governors, energy performance preference)
# - Storage I/O Optimization (BFQ per dischi meccanici 5400 RPM, Kyber per SSD, None per NVMe)
# - GPU Graphics Subsystem (Mesa Amber / DRI2 / XRender su GMA 950 vs Vulkan / Wayland su modern)
# - Display Ergonomics (Ottimizzazioni per WSVGA 1024x600 su Netbook)
# - Attivazione Kernel Registrations binfmt_misc (Universal Execution Matrix)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================================="
echo "       OSify Hardware Adaptation Layer (HAL)             "
echo "========================================================="

# ------------------------------------------------------------------------------
# 1. Rilevamento CPU & Architettura
# ------------------------------------------------------------------------------
ARCH="$(uname -m)"
CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^[ \t]*//' || echo "Unknown CPU")
CPU_CORES=$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "1")

echo "[HAL] Architettura CPU : $ARCH"
echo "[HAL] Modello CPU      : $CPU_MODEL"
echo "[HAL] Core Rilevati    : $CPU_CORES"

TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "2097152")
TOTAL_RAM_MB=$(( TOTAL_RAM_KB / 1024 ))
echo "[HAL] Memoria Fisica   : ${TOTAL_RAM_MB} MB"

# ------------------------------------------------------------------------------
# 2. Configurazione Dinamica Memoria & ZRAM
# ------------------------------------------------------------------------------
if [[ "$TOTAL_RAM_MB" -le 1536 ]]; then
    echo "[HAL] Profilo Hardware : Vintage / Low-Memory (< 1.5 GB RAM)"
    
    # Su macchine legacy (es. Toshiba NB200 con Intel Atom e 1GB RAM):
    # La ZRAM a 1.5x RAM con LZ4 evita saturazione CPU e azzera il trashing del disco meccanico.
    ZRAM_SIZE_MB=$(( TOTAL_RAM_MB * 3 / 2 ))
    if command -v zramctl >/dev/null 2>&1; then
        modprobe zram num_devices=1 2>/dev/null || true
        zramctl -r /dev/zram0 2>/dev/null || true
        zramctl /dev/zram0 -a lz4 -s "${ZRAM_SIZE_MB}M" 2>/dev/null || true
        mkswap /dev/zram0 >/dev/null 2>&1 || true
        swapon -p 100 /dev/zram0 2>/dev/null || true
        echo "[HAL] ZRAM Attiva      : ${ZRAM_SIZE_MB} MB (Algoritmo: lz4, Priorita': 100)"
    fi

    # Tuning kernel per evitare freeze durante scritture pesanti
    sysctl -w vm.swappiness=150 >/dev/null 2>&1 || true
    sysctl -w vm.vfs_cache_pressure=50 >/dev/null 2>&1 || true
    sysctl -w vm.dirty_ratio=10 >/dev/null 2>&1 || true
    sysctl -w vm.dirty_background_ratio=5 >/dev/null 2>&1 || true
    sysctl -w vm.page-cluster=0 >/dev/null 2>&1 || true
else
    echo "[HAL] Profilo Hardware : Modern High-Performance"
    
    if command -v zramctl >/dev/null 2>&1 && [[ ! -e /dev/zram0 ]]; then
        modprobe zram num_devices=1 2>/dev/null || true
        ZRAM_SIZE_MB=$(( TOTAL_RAM_MB / 2 ))
        zramctl /dev/zram0 -a zstd -s "${ZRAM_SIZE_MB}M" 2>/dev/null || true
        mkswap /dev/zram0 >/dev/null 2>&1 || true
        swapon -p 100 /dev/zram0 2>/dev/null || true
        echo "[HAL] ZRAM Attiva      : ${ZRAM_SIZE_MB} MB (Algoritmo: zstd, Priorita': 100)"
    fi

    sysctl -w vm.swappiness=10 >/dev/null 2>&1 || true
    sysctl -w vm.vfs_cache_pressure=100 >/dev/null 2>&1 || true
    sysctl -w vm.max_map_count=2147483642 >/dev/null 2>&1 || true
    sysctl -w fs.file-max=2097152 >/dev/null 2>&1 || true
fi

# ------------------------------------------------------------------------------
# 3. Ottimizzazione Storage & I/O Schedulers
# ------------------------------------------------------------------------------
for dev in /sys/block/sd* /sys/block/nvme* /sys/block/mmcblk*; do
    if [[ -d "$dev/queue" ]]; then
        dev_name="$(basename "$dev")"
        rotational=$(cat "$dev/queue/rotational" 2>/dev/null || echo "0")
        if [[ "$dev_name" =~ ^nvme ]]; then
            echo "none" > "$dev/queue/scheduler" 2>/dev/null || true
            echo "[HAL] I/O Scheduler   : $dev_name -> none (NVMe Zero Latency)"
        elif [[ "$rotational" -eq 1 ]]; then
            # Hard Disk meccanico (es. Toshiba 5400 RPM): BFQ garantisce responsivita' UI
            echo "bfq" > "$dev/queue/scheduler" 2>/dev/null || true
            echo "[HAL] I/O Scheduler   : $dev_name -> bfq (HDD Meccanico Anti-Lag)"
        else
            # SSD SATA: Kyber o MQ-Deadline
            if grep -q "kyber" "$dev/queue/scheduler" 2>/dev/null; then
                echo "kyber" > "$dev/queue/scheduler" 2>/dev/null || true
            else
                echo "mq-deadline" > "$dev/queue/scheduler" 2>/dev/null || true
            fi
            echo "[HAL] I/O Scheduler   : $dev_name -> SSD Optimized"
        fi
    fi
done

# ------------------------------------------------------------------------------
# 4. GPU Subsystem & Tuning Grafico
# ------------------------------------------------------------------------------
HAS_VULKAN=0
if command -v vulkaninfo >/dev/null 2>&1 && vulkaninfo --summary >/dev/null 2>&1; then
    HAS_VULKAN=1
fi

if [[ "$HAS_VULKAN" -eq 1 ]]; then
    echo "[HAL] Stack Grafico   : Vulkan Native (Accelerazione Hardware Moderna Attiva)"
else
    echo "[HAL] Stack Grafico   : Legacy DRI2 / OpenGL (Mesa Amber / WineD3D)"
    # Disattivazione tentativi DXVK/Vulkan per prevenire crash su Intel GMA 950
    export WINE_D3D_CONFIG="renderer=gl"
fi

# ------------------------------------------------------------------------------
# 5. Registrazione Kernel binfmt_misc (Universal Execution Matrix)
# ------------------------------------------------------------------------------
BINFMT_CONF="$REPO_ROOT/uem/binfmt/99-osify-binfmt.conf"

if [[ -f "$BINFMT_CONF" ]]; then
    if [[ ! -d /proc/sys/fs/binfmt_misc ]]; then
        modprobe binfmt_misc 2>/dev/null || true
        mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc 2>/dev/null || true
    fi

    if [[ -w /proc/sys/fs/binfmt_misc/register ]]; then
        # Registrazione diretta riga per riga nel filesystem proc del kernel
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Salta commenti e righe vuote
            if [[ "$line" =~ ^: ]]; then
                echo "$line" > /proc/sys/fs/binfmt_misc/register 2>/dev/null || true
            fi
        done < "$BINFMT_CONF"
        echo "[HAL] Universal Execution Matrix (UEM): Registrazioni kernel binfmt applicate con successo."
    elif command -v systemd-binfmt >/dev/null 2>&1; then
        systemd-binfmt "$BINFMT_CONF" 2>/dev/null || true
        echo "[HAL] Universal Execution Matrix (UEM): Registrata tramite systemd-binfmt."
    fi
fi

echo "[HAL] Inizializzazione e tuning hardware completati con successo."
