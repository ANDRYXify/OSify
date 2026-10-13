#!/usr/bin/env bash
# ==============================================================================
# OSify ISO Builder — Generatore di Immagini Avviabili x86-64-v3
# ==============================================================================
# Utilizza la toolchain mkarchiso integrando:
# 1. Repository compilati per microarchitettura x86-64-v3 (AVX2/FMA)
# 2. Kernel BORE a bassa latenza (linux-cachyos-bore)
# 3. Pacchetti KDE Plasma 6 Wayland pre-configurati
# 4. Moduli OSify (sysctl, QoS, PipeWire pro-audio, udev controller rules)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="/tmp/osify-iso-work"
OUT_DIR="$SCRIPT_DIR/out"
PROFILE_DIR="$SCRIPT_DIR/profile"

check_dependencies() {
    echo "[Build] Verifica dipendenze di compilazione ISO..."
    if ! command -v mkarchiso >/dev/null 2>&1; then
        echo "[!] 'mkarchiso' non trovato nel sistema host."
        echo "    Nota: L'immagine finale va generata su un ambiente Linux con archiso installato."
        echo "    Se ti trovi su macOS, puoi eseguire questa build dentro un container Docker o VM QEMU/KVM."
    fi
}

prepare_profile() {
    echo "[Build] Preparazione directory di profilo..."
    mkdir -p "$PROFILE_DIR/airootfs/etc/sysctl.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/udev/rules.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/pipewire/pipewire.conf.d"
    mkdir -p "$PROFILE_DIR/airootfs/usr/local/bin"
    mkdir -p "$OUT_DIR"

    # Copia delle configurazioni OSify direttamente nella root del sistema live
    cp "$SCRIPT_DIR/../kernel/osify-sysctl.conf" "$PROFILE_DIR/airootfs/etc/sysctl.d/99-osify.conf"
    cp "$SCRIPT_DIR/../kernel/udev/99-osify-controllers.rules" "$PROFILE_DIR/airootfs/etc/udev/rules.d/"
    cp "$SCRIPT_DIR/../kernel/udev/99-osify-storage.rules" "$PROFILE_DIR/airootfs/etc/udev/rules.d/"
    cp "$SCRIPT_DIR/../audio/pipewire.conf.d/99-osify-proaudio.conf" "$PROFILE_DIR/airootfs/etc/pipewire/pipewire.conf.d/"
    
    # Copia toolchain CLI
    cp "$SCRIPT_DIR/../tools/osify-ctl" "$PROFILE_DIR/airootfs/usr/local/bin/"
    cp "$SCRIPT_DIR/../network/osify-qos.sh" "$PROFILE_DIR/airootfs/usr/local/bin/osify-qos"
    cp "$SCRIPT_DIR/../audio/osify-audio-setup.sh" "$PROFILE_DIR/airootfs/usr/local/bin/osify-audio"

    chmod +x "$PROFILE_DIR/airootfs/usr/local/bin/"*

    # Copia pacchetti
    cp "$SCRIPT_DIR/packages.x86_64" "$PROFILE_DIR/packages.x86_64"

    echo "[✓] Profilo ISO assemblato e pronto per la compilazione."
}

build_iso() {
    prepare_profile
    check_dependencies
    
    if command -v mkarchiso >/dev/null 2>&1; then
        echo "[+] Avvio compilazione ISO tramite mkarchiso..."
        sudo mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"
        echo "[✓] ISO generata con successo in: $OUT_DIR/"
    else
        echo "[i] Struttura profilo completata con successo. Per lanciare il build su Linux: 'sudo ./build-iso.sh'"
    fi
}

case "${1:-build}" in
    prepare)
        prepare_profile
        ;;
    build)
        build_iso
        ;;
    clean)
        rm -rf "$WORK_DIR" "$PROFILE_DIR"
        echo "[✓] Directory temporanee rimosse."
        ;;
    *)
        echo "Uso: $0 {build|prepare|clean}"
        exit 1
        ;;
esac
