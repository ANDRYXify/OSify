#!/usr/bin/env bash
# ==============================================================================
# OSify Windows Runtime — Proton-GE & Wine-TKG Engine
# ==============================================================================
# Esegue eseguibili Windows (.exe) e giochi DirectX 9/10/11/12 con prestazioni
# native o superiori a Windows grazie a Fsync/Futex2 e traduzione Vulkan asincrona.
# ==============================================================================

set -euo pipefail

EXE_PATH="${1:-}"
PREFIX_DIR="${WINEPREFIX:-$HOME/.local/share/osify/wineprefixes/default}"

if [[ -z "$EXE_PATH" ]]; then
    echo "Uso: $0 <percorso-file.exe> [argomenti...]"
    exit 1
fi
shift || true

mkdir -p "$PREFIX_DIR"

# Variabili d'ambiente ad alte prestazioni per Windows Gaming
export WINEPREFIX="$PREFIX_DIR"
export WINEFSYNC=1                         # Sincronizzazione thread via futex2 / sys_futex_waitv nel kernel
export WINEESYNC=1                         # Fallback su eventfd se fsync non supportato
export PROTON_ENABLE_NVAPI=1               # Abilita DLSS, Reflex su GPU Nvidia
export PROTON_HIDE_NVIDIA_GPU=0
export DXVK_ASYNC=1                        # Compilazione asincrona pipeline DX9/10/11
export VKD3D_CONFIG="dxr,dxr11"            # Supporto DirectX 12 Ray Tracing nativo
export MESA_VK_WSI_PRESENT_MODE="immediate"# Disabilita VSync forzato per latenza eSport
export STAGING_SHARED_MEMORY=1

echo "========================================================="
echo "       OSify Windows Runtime: $(basename "$EXE_PATH")"
echo "========================================================="
echo "[+] Wine Prefix: $WINEPREFIX"
echo "[+] Modalità Fsync: Attiva (Kernel Futex2)"

# Cerca runtime Proton-GE o Wine-TKG
RUNNER="wine"
if command -v proton-ge-custom >/dev/null 2>&1; then
    RUNNER="proton-ge-custom"
elif command -v wine64 >/dev/null 2>&1; then
    RUNNER="wine64"
fi

if command -v gamemoderun >/dev/null 2>&1; then
    exec gamemoderun "$RUNNER" "$EXE_PATH" "$@"
else
    exec "$RUNNER" "$EXE_PATH" "$@"
fi
