#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Cross-ISA Execution Engine (Box64 / Box86 / QEMU User)
# ==============================================================================
# Sfondamento delle barriere tra architetture hardware:
# Consente l'esecuzione trasparente di binari compilati per altre CPU
# (es. x86_64 su ARM64 / Apple Silicon, ARM64 su x86, RISC-V su x86).
# Sfrutta il wrapping nativo delle librerie OpenGL, Vulkan, OpenAL e libc.
# ==============================================================================

set -euo pipefail

BIN_FILE="${1:-}"

if [[ -z "$BIN_FILE" || ! -f "$BIN_FILE" ]]; then
    echo "[ERRORE] File eseguibile non valido: $BIN_FILE" >&2
    exit 1
fi

HOST_ARCH="$(uname -m)"
TARGET_ARCH="unknown"

if command -v file >/dev/null 2>&1; then
    FILE_INFO=$(file -b "$BIN_FILE")
    if [[ "$FILE_INFO" =~ "x86-64" ]]; then TARGET_ARCH="x86_64"; fi
    if [[ "$FILE_INFO" =~ "Intel 80386" ]]; then TARGET_ARCH="i686"; fi
    if [[ "$FILE_INFO" =~ "aarch64" || "$FILE_INFO" =~ "ARM aarch64" ]]; then TARGET_ARCH="aarch64"; fi
    if [[ "$FILE_INFO" =~ "RISC-V" ]]; then TARGET_ARCH="riscv64"; fi
fi

# 1. Caso x86_64 su Host ARM64 (es. Raspberry Pi 5, Apple Silicon Mac, Ampere)
if [[ "$HOST_ARCH" =~ ^(aarch64|arm64)$ && "$TARGET_ARCH" == "x86_64" ]]; then
    if command -v box64 >/dev/null 2>&1; then
        export BOX64_LOG=0
        export BOX64_DYNAREC=1
        exec box64 "$BIN_FILE" "$@"
    elif command -v fex-emu >/dev/null 2>&1; then
        exec fex-emu "$BIN_FILE" "$@"
    fi
fi

# 2. Caso x86 (32-bit) su Host ARM
if [[ "$HOST_ARCH" =~ ^(aarch64|arm64|armv7l)$ && "$TARGET_ARCH" == "i686" ]]; then
    if command -v box86 >/dev/null 2>&1; then
        export BOX86_LOG=0
        export BOX86_DYNAREC=1
        exec box86 "$BIN_FILE" "$@"
    fi
fi

# 3. Fallback Cross-Architecture con QEMU User Static
QEMU_USER_BIN=""
case "$TARGET_ARCH" in
    x86_64)   QEMU_USER_BIN="qemu-x86_64-static" ;;
    i686)     QEMU_USER_BIN="qemu-i386-static" ;;
    aarch64)  QEMU_USER_BIN="qemu-aarch64-static" ;;
    riscv64)  QEMU_USER_BIN="qemu-riscv64-static" ;;
esac

if [[ -n "$QEMU_USER_BIN" ]] && command -v "$QEMU_USER_BIN" >/dev/null 2>&1; then
    exec "$QEMU_USER_BIN" "$BIN_FILE" "$@"
fi

# 4. Se la CPU host non supporta l'istruzione (es. 64-bit su Atom 32-bit reale)
if [[ "$HOST_ARCH" =~ ^(i686|i386)$ && "$TARGET_ARCH" == "x86_64" ]]; then
    echo "[ERRORE HARDWARE] Impossibile eseguire un binario a 64-bit nativo su una CPU limitata a 32-bit ($HOST_ARCH)." >&2
    echo "                 Per eseguire questo software e' necessaria l'emulazione con QEMU User Static." >&2
    exit 126
fi

# Fallback nativo standard
exec "$BIN_FILE" "$@"
