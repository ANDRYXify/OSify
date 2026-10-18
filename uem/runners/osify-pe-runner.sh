#!/usr/bin/env bash
# ==============================================================================
# OSify Universal PE Runner — Transparent Windows Executable Handler
# ==============================================================================
# Invocato automaticamente dal kernel (binfmt_misc) per eseguire qualsiasi
# binario Windows (.exe) adattando lo stack grafico e il runtime all'hardware reale:
# - Su x86_64 con Vulkan: Proton-GE + DXVK-Async + Fsync (futex2)
# - Su i686/Legacy (Toshiba NB200 / GMA 950): Wine 32-bit + WineD3D OpenGL nativo
# ==============================================================================

set -euo pipefail

EXE_FILE="${1:-}"

if [[ -z "$EXE_FILE" || ! -f "$EXE_FILE" ]]; then
    echo "[ERRORE] File eseguibile non valido: $EXE_FILE" >&2
    exit 1
fi
shift

HOST_ARCH="$(uname -m)"
HAS_VULKAN=0
if command -v vulkaninfo >/dev/null 2>&1 && vulkaninfo --summary >/dev/null 2>&1; then
    HAS_VULKAN=1
fi

export WINEPREFIX="${WINEPREFIX:-$HOME/.osify/runtimes/windows/default_pfx}"
mkdir -p "$WINEPREFIX"

# Ottimizzazioni per postazioni moderne x86_64 con Vulkan
if [[ "$HOST_ARCH" == "x86_64" && "$HAS_VULKAN" -eq 1 ]]; then
    export PROTON_ENABLE_NVAPI=1
    export DXVK_ASYNC=1
    export PROTON_ENABLE_EAC=1
    export PROTON_ENABLE_BATTLEYE=1
    export WINEFSYNC=1
    export RADV_PERFTEST=gpl

    if command -v proton-ge >/dev/null 2>&1; then
        exec proton-ge run "$EXE_FILE" "$@"
    elif command -v wine >/dev/null 2>&1; then
        exec wine "$EXE_FILE" "$@"
    fi
else
    # Profilo Vintage / GMA 950 / 32-bit (Toshiba NB200)
    # Nessun tentativo di caricare Vulkan o DXVK (fallirebbero con crash).
    # Forzato il renderer Direct3D su OpenGL classico (WineD3D).
    export WINEDEBUG="-all"
    export WINE_D3D_CONFIG="renderer=gl"
    export MESA_GL_VERSION_OVERRIDE="2.1"
    export MESA_GLSL_VERSION_OVERRIDE="120"

    if command -v wine >/dev/null 2>&1; then
        exec wine "$EXE_FILE" "$@"
    elif command -v wine32 >/dev/null 2>&1; then
        exec wine32 "$EXE_FILE" "$@"
    else
        echo "[ERRORE] Sottosistema Wine/Proton non installato sul sistema host." >&2
        exit 1
    fi
fi
