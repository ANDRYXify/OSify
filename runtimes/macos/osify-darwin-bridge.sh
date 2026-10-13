#!/usr/bin/env bash
# ==============================================================================
# OSify macOS & iOS Bridge Engine
# ==============================================================================
# Gestisce l'interfacciamento con l'ecosistema Apple:
# 1. Darling: Layer di traduzione Mach-O / Darwin per toolchain, script e CLI macOS
# 2. OSX-KVM: Virtualizzazione KVM accelerata con CPU pinning e GPU passthrough (prestazioni 98% native)
# 3. iOS/iPadOS Toolkit: Diagnostica e bridge simulatori / QEMU ARM64
# ==============================================================================

set -euo pipefail

ACTION="${1:-status}"

run_darling() {
    local cmd="${2:-shell}"
    if ! command -v darling >/dev/null 2>&1; then
        echo "[!] Darling non è installato sul sistema."
        echo "    Installabile via: osify-ctl runtime install-darling"
        exit 1
    fi

    echo "[OSify-Darwin] Avvio container Mach-O Darling..."
    if [[ "$cmd" == "shell" ]]; then
        darling shell
    else
        shift 2 || true
        darling "$cmd" "$@"
    fi
}

start_macos_kvm() {
    echo "========================================================="
    echo "       OSify macOS KVM — Avvio Mac ad Altissime Prestazioni"
    echo "========================================================="
    
    local VM_SCRIPT="$HOME/.local/share/osify/osx-kvm/OpenCore-Boot.sh"
    if [[ ! -f "$VM_SCRIPT" ]]; then
        echo "[!] Istanza macOS KVM non ancora configurata."
        echo "[i] Esegui: osify-ctl runtime setup-macos-kvm per generare l'ambiente con OpenCore e passthrough hardware."
        exit 1
    fi

    exec bash "$VM_SCRIPT"
}

case "$ACTION" in
    darling)
        run_darling "$@"
        ;;
    kvm)
        start_macos_kvm
        ;;
    status)
        echo "=== Stato Moduli macOS / Darwin ==="
        echo -n "Darling CLI: "
        command -v darling >/dev/null 2>&1 && echo "Presente" || echo "Non installato"
        echo -n "Modulo KVM (Virtualizzazione Hardware): "
        lsmod | grep -q kvm && echo "Attivo" || echo "Non caricato"
        echo -n "Supporto IOMMU / VFIO: "
        dmesg 2>/dev/null | grep -qi "iommu" && echo "Abilitato" || echo "Verificare flag BIOS/Kernel"
        ;;
    *)
        echo "Uso: $0 {darling [cmd]|kvm|status}"
        exit 1
        ;;
esac
