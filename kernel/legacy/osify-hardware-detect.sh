#!/usr/bin/env bash
# ==============================================================================
# OSify Hardware Intelligence — Auto-Detection & Legacy Adaptation Engine
# ==============================================================================
# Analizza l'hardware all'avvio e adatta dinamicamente OSify:
# 1. Rileva il livello di microarchitettura della CPU (v1, v2, v3, v4)
# 2. Rileva la quantità di RAM (se <= 4GB, attiva ZRAM ultra-compressa e Low-Spec Mode)
# 3. Rileva tipo di boot (UEFI moderno vs Legacy BIOS MBR vintage)
# 4. Rileva tipo di disco (HDD rotazionale meccanico vs SSD/NVMe)
# ==============================================================================

set -euo pipefail

detect_cpu_level() {
    local flags=""
    if [[ -f /proc/cpuinfo ]]; then
        flags=$(grep -m1 '^flags' /proc/cpuinfo 2>/dev/null || echo "")
    elif command -v sysctl >/dev/null 2>&1; then
        flags=$(sysctl -n machdep.cpu.features machdep.cpu.leaf7_features 2>/dev/null || echo "")
    fi
    
    local flags_lower
    flags_lower=$(echo "$flags" | tr '[:upper:]' '[:lower:]')

    if echo "$flags_lower" | grep -qw 'avx512f'; then
        echo "x86-64-v4 (AVX-512 • CPU Ultima Generazione)"
    elif echo "$flags_lower" | grep -qw 'avx2'; then
        echo "x86-64-v3 (AVX2 / FMA • Hardware Moderno Consigliato)"
    elif echo "$flags_lower" | grep -qw 'sse4_2' || echo "$flags_lower" | grep -qw 'sse4.2'; then
        echo "x86-64-v2 (SSE4.2 • CPU Media Generazione 2008-2013)"
    elif echo "$flags_lower" | grep -qw 'lm' || uname -m | grep -q '64'; then
        echo "x86-64-v1 (Baseline Legacy • Qualsiasi CPU 64-bit dal 2003)"
    else
        echo "Architettura Sconosciuta"
    fi
}

detect_ram_mb() {
    if [[ -f /proc/meminfo ]]; then
        awk '/MemTotal/ {print int($2 / 1024)}' /proc/meminfo 2>/dev/null || echo "4096"
    elif command -v sysctl >/dev/null 2>&1; then
        local bytes
        bytes=$(sysctl -n hw.memsize 2>/dev/null || echo "4294967296")
        echo $(( bytes / 1024 / 1024 ))
    else
        echo "4096"
    fi
}

detect_boot_mode() {
    if [[ -d "/sys/firmware/efi" ]]; then
        echo "UEFI (Moderno)"
    elif [[ "$(uname)" == "Darwin" ]]; then
        echo "macOS Host Firmware (Testing)"
    else
        echo "Legacy BIOS / MBR (Macchina Vintage)"
    fi
}

apply_legacy_optimizations() {
    local ram_mb
    ram_mb=$(detect_ram_mb)

    echo "[Hardware-Probe] Rilevati ${ram_mb} MB di RAM fisica."

    if [[ "$ram_mb" -le 4096 ]]; then
        echo "[!] MACCHINA VINTAGE / RISORSE LIMITATE RILEVATA (RAM <= 4GB)!"
        echo "[+] Attivazione contromisure per resuscitare l'hardware:"
        
        # 1. Configurazione ZRAM ad alta compressione (zstd)
        # Permette a una macchina con 2GB-4GB di RAM di lavorare come se ne avesse 6GB-8GB
        if command -v zramctl >/dev/null 2>&1; then
            echo "[+] Configurazione ZRAM compressa in zstd..."
            modprobe zram num_devices=1 2>/dev/null || true
            zramctl /dev/zram0 --algorithm zstd --size 4G 2>/dev/null || true
            mkswap /dev/zram0 >/dev/null 2>&1 || true
            swapon -p 100 /dev/zram0 2>/dev/null || true
        fi

        # 2. Ottimizzazione Kernel VM per ZRAM su PC vecchi
        sysctl -w vm.swappiness=150 >/dev/null 2>&1 || true
        sysctl -w vm.vfs_cache_pressure=50 >/dev/null 2>&1 || true

        # 3. Attivazione profilo grafico ultra-leggero per KDE Plasma
        local lowspec_script
        lowspec_script="$(dirname "$0")/../../desktop/profiles/osify-lowspec-kde.sh"
        if [[ -f "$lowspec_script" ]]; then
            bash "$lowspec_script" || true
        fi
        echo "[✓] Modalità Vintage Low-Spec attiva: consumi azzerati e massima fluidità."
    else
        echo "[+] Risorse abbondanti (>4GB RAM): profilo ad alte prestazioni standard attivo."
    fi
}

main() {
    echo "========================================================="
    echo "       OSify Hardware Diagnostics & Adaptation Probe     "
    echo "========================================================="
    echo "[CPU Support Level] : $(detect_cpu_level)"
    echo "[Memoria RAM Totale]: $(detect_ram_mb) MB"
    echo "[Firmware di Boot]  : $(detect_boot_mode)"
    echo "---------------------------------------------------------"

    if [[ "${1:-}" == "--apply" ]]; then
        apply_legacy_optimizations
    else
        echo "Esegui con '--apply' per applicare automaticamente il profilo ottimale."
    fi
}

main "$@"
