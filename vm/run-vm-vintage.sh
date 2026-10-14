#!/usr/bin/env bash
# ==============================================================================
# OSify Vintage VM Launcher — Emulatore Netbook / Vecchie Glorie (32-bit i686)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Emula fedelmente l'hardware di netbook vintage (Intel Atom / 1GB RAM / 1024x600)
# con supporto disco virtuale persistente per testare l'installazione bare-metal.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ISO_PATH="$REPO_ROOT/build/out/release/OSify-Vintage-i686.iso"
DISK_IMG="$SCRIPT_DIR/osify-vintage-disk.qcow2"

if [ ! -f "$ISO_PATH" ]; then
    echo "[!] File ISO non trovato in: $ISO_PATH"
    echo "[*] Esegui prima il download o la compilazione della ISO."
    exit 1
fi

# Creazione disco virtuale da 8GB se non esiste
if [ ! -f "$DISK_IMG" ]; then
    echo "[+] Creazione disco virtuale da 8 GB per test installazione..."
    qemu-img create -f qcow2 "$DISK_IMG" 8G >/dev/null
fi

QEMU_BIN="/opt/homebrew/bin/qemu-system-i386"
if [ ! -x "$QEMU_BIN" ]; then
    QEMU_BIN="$(which qemu-system-i386 2>/dev/null || which qemu-system-x86_64 2>/dev/null)"
fi

if [ -z "$QEMU_BIN" ]; then
    echo "[!] qemu-system-i386 non trovato su questo sistema."
    exit 1
fi

echo "========================================================="
echo "   OSify Vintage VM (Vecchie Glorie / Netbook 32-bit)    "
echo "========================================================="
echo " ISO        : $(basename "$ISO_PATH")"
echo " RAM        : 1024 MB"
echo " Disco      : 8 GB (qcow2 isolato)"
echo " Schermo    : 1024x600 Netbook Resolution (VESA/VGA)"
echo " Audio      : Intel AC97"
echo " Rete       : NAT con accesso internet"
echo "========================================================="
echo "[*] Avvio macchina virtuale in corso..."

exec "$QEMU_BIN" \
    -name "OSify Vintage 32-bit (Vecchie Glorie)" \
    -m 1024M \
    -smp 2 \
    -cdrom "$ISO_PATH" \
    -drive file="$DISK_IMG",format=qcow2,if=ide \
    -boot d \
    -vga std \
    -audiodev coreaudio,id=snd0 -device AC97,audiodev=snd0 \
    -netdev user,id=net0 -device rtl8139,netdev=net0 \
    -usb -device usb-tablet \
    -display cocoa
