#!/usr/bin/env bash
# ==============================================================================
# OSify Modern 64-bit VM Launcher — Emulatore Desktop Moderno / Gaming
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Emulatore ad alte prestazioni per testare l'edizione x86_64-v3 di OSify,
# con supporto accelerazione grafica VirtIO, disco da 20GB e rete ad alta velocità.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ISO_PATH="$REPO_ROOT/build/out/release/OSify-x86_64-v3.iso"
DISK_IMG="$SCRIPT_DIR/osify-pro-disk.qcow2"

if [ ! -f "$ISO_PATH" ]; then
    echo "[!] File ISO non trovato in: $ISO_PATH"
    echo "[*] Esegui prima il download o la compilazione della ISO."
    exit 1
fi

# Creazione disco virtuale da 20GB se non esiste
if [ ! -f "$DISK_IMG" ]; then
    echo "[+] Creazione disco virtuale da 20 GB per test installazione..."
    qemu-img create -f qcow2 "$DISK_IMG" 20G >/dev/null
fi

QEMU_BIN="/opt/homebrew/bin/qemu-system-x86_64"
if [ ! -x "$QEMU_BIN" ]; then
    QEMU_BIN="$(which qemu-system-x86_64 2>/dev/null)"
fi

if [ -z "$QEMU_BIN" ]; then
    echo "[!] qemu-system-x86_64 non trovato su questo sistema."
    exit 1
fi

echo "========================================================="
echo "   OSify Pro Modern VM (x86_64-v3 Gaming & Streaming)    "
echo "========================================================="
echo " ISO        : $(basename "$ISO_PATH")"
echo " RAM        : 3072 MB"
echo " vCPU       : 4 core"
echo " Disco      : 20 GB (qcow2 isolato)"
echo " Grafica    : VirtIO GPU accelerata"
echo " Audio      : Intel HD Audio"
echo " Rete       : VirtIO Gigabit NAT"
echo "========================================================="
echo "[*] Avvio macchina virtuale in corso..."

exec "$QEMU_BIN" \
    -name "OSify Pro Modern 64-bit" \
    -m 3072M \
    -smp 4 \
    -cdrom "$ISO_PATH" \
    -drive file="$DISK_IMG",format=qcow2,if=virtio \
    -boot d \
    -vga virtio \
    -audiodev coreaudio,id=snd0 -device intel-hda -device hda-duplex,audiodev=snd0 \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -usb -device usb-tablet \
    -display cocoa
