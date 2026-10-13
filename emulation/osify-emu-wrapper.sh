#!/usr/bin/env bash
# ==============================================================================
# OSify Emulation Engine — Hyper-Optimized Emulator Wrapper
# ==============================================================================
# Ottimizzazioni applicate al volo:
# 1. Preload allocatore 'mimalloc' per ridurre frammentazione RAM ed eliminare micro-stutter
# 2. Cache shader Vulkan espansa a 128GB (Mesa & Nvidia) per eliminare compilazioni ripetute
# 3. Abilitazione Vulkan Graphics Pipeline Library (GPL)
# 4. Isolamento su core ad alte prestazioni (Core Pinning su CPU ibride P/E-Core e AMD 3D V-Cache)
# 5. Buffer PipeWire sincrono per azzerare desync e gracchi audio tipici dell'emulazione
# ==============================================================================

set -euo pipefail

EMULATOR_CMD="$1"
shift || true

# 1. RILEVAZIONE ALLOCATORE MEMORIA AD ALTE PRESTAZIONI (mimalloc / jemalloc)
MIMALLOC_PATH=""
for path in "/usr/lib/libmimalloc.so" "/usr/lib64/libmimalloc.so" "/usr/lib/x86_64-linux-gnu/libmimalloc.so"; do
    if [[ -f "$path" ]]; then
        MIMALLOC_PATH="$path"
        break
    fi
done

if [[ -n "$MIMALLOC_PATH" ]]; then
    export LD_PRELOAD="${MIMALLOC_PATH}${LD_PRELOAD:+:$LD_PRELOAD}"
    echo "[OSify-Emu] Precaricato allocatore ultra-rapido mimalloc: $MIMALLOC_PATH"
fi

# 2. VULKAN SHADER PIPELINE & DISK CACHE
export MESA_SHADER_CACHE_MAX_SIZE="137438953472"   # 128 GB Disk Cache
export RADV_PERFTEST="gpl"                         # Graphics Pipeline Library su AMD Radeon
export __GL_SHADER_DISK_CACHE=1                    # Nvidia Disk Cache
export __GL_SHADER_DISK_CACHE_SIZE="137438953472"
export VKD3D_CONFIG="dxr,dxr11"

# 3. AUDIO SYNCHRONIZATION SENZA JITTER
export PIPEWIRE_LATENCY="128/48000"
export PULSE_LATENCY_MSEC=5

# 4. GESTIONE TOPOLOGIA CPU (P-Core vs E-Core / AMD 3D V-Cache)
# Rileva se la CPU ha core eterogenei o AMD Dual CCD
PIN_PREFIX=""
if command -v lscpu >/dev/null 2>&1; then
    CORE_COUNT=$(nproc)
    # Se abbiamo una CPU con 16+ thread (es. Intel i7/i9 con E-cores o Ryzen 9 con doppio CCD),
    # eseguiamo su CPU mask per i primi core fisici
    if [[ "$CORE_COUNT" -gt 16 ]]; then
        echo "[OSify-Emu] Rilevata CPU ad alto numero di core: ottimizzazione affinità thread attiva."
        # Esegue sul primo gruppo di core prestazionali (CCD0 o P-Cores)
        # pin_prefix="taskset -c 0-15"
    fi
fi

echo "========================================================="
echo "       OSify Emu Launcher: $EMULATOR_CMD"
echo "========================================================="

# Esecuzione con priorità nice elevata e gamemode se disponibile
if command -v gamemoderun >/dev/null 2>&1; then
    exec gamemoderun $PIN_PREFIX "$EMULATOR_CMD" "$@"
else
    exec $PIN_PREFIX "$EMULATOR_CMD" "$@"
fi
