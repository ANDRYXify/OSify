#!/usr/bin/env bash
# ==============================================================================
# OSify Virtual Testbed & Hardware Simulator (by Andryx)
# ==============================================================================
# Permette di testare OSify in una macchina virtuale isolata direttamente su Mac
# o Linux, con tre profili principali:
#
# PROFILO 1: Modern Gaming & Streaming Rig (4 vCPU, 4GB RAM, Display 1080p)
# PROFILO 2: Toshiba NB200 Netbook Simulator (1 vCPU Intel Atom N270, 1GB RAM, Display 1024x600)
# PROFILO 3: Toshiba NB200 Extreme Stress-Test (512MB RAM, 1 vCPU, Display 1024x600)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DISK_IMAGE="$SCRIPT_DIR/osify-test-drive.qcow2"

find_iso_for_profile() {
    local profile="$1"
    local iso=""

    if [[ "$profile" =~ ^(2|nb200|toshiba|3|stress|extreme)$ ]]; then
        # Profilo Vintage 32-bit: desktop grafico pronto all'uso
        for candidate in \
            "$SCRIPT_DIR/OSify-Vintage-Live.iso" \
            "$SCRIPT_DIR/osify-vintage-desktop.iso" \
            "$SCRIPT_DIR/osify-vintage-base.iso" \
            "$REPO_ROOT/build/out/release/OSify-Vintage-i686.iso" \
            "$REPO_ROOT/build/out/"*vintage*.iso \
            "$REPO_ROOT/build/out/"*i686*.iso \
            "$SCRIPT_DIR/"*.iso; do
            if [[ -f "$candidate" ]]; then
                iso="$candidate"
                break
            fi
        done
    else
        # Profilo Modern 64-bit: cerca immagini x86_64
        for candidate in \
            "$REPO_ROOT/build/out/release/OSify-x86_64-v3.iso" \
            "$REPO_ROOT/build/out/"*x86_64*.iso \
            "$REPO_ROOT/build/out/"*.iso \
            "$SCRIPT_DIR/"*.iso; do
            if [[ -f "$candidate" ]]; then
                iso="$candidate"
                break
            fi
        done
    fi
    echo "$iso"
}

check_qemu() {
    if ! command -v qemu-system-x86_64 >/dev/null 2>&1 && ! command -v qemu-system-i386 >/dev/null 2>&1; then
        echo "[ERRORE] Binari QEMU non trovati nel sistema host."
        echo "         Puoi installarli su Mac con: brew install qemu"
        exit 1
    fi
}

create_virtual_disk() {
    if [[ ! -f "$DISK_IMAGE" ]]; then
        echo "[+] Creazione disco virtuale QCOW2 da 20 GB per il test..."
        qemu-img create -f qcow2 "$DISK_IMAGE" 20G >/dev/null
        echo "[✓] Disco virtuale pronto: $DISK_IMAGE"
    fi
}

start_vm() {
    local profile="${1:-1}"
    check_qemu
    create_virtual_disk

    local MEM="4096M"
    local CPUS="4"
    local RESOLUTION="1920x1080"
    local CPU_MODEL="max"
    local QEMU_BIN="qemu-system-x86_64"
    local PROFILE_NAME=""

    case "$profile" in
        1|modern)
            PROFILE_NAME="Modern Gaming & Streaming Rig (x86_64)"
            MEM="4096M"
            CPUS="4"
            RESOLUTION="1920x1080"
            CPU_MODEL="max"
            QEMU_BIN="qemu-system-x86_64"
            ;;
        2|nb200|toshiba)
            PROFILE_NAME="Toshiba NB200 Netbook Simulator (Intel Atom N270 • 1GB RAM • 1024x600)"
            MEM="1024M"
            CPUS="1"
            RESOLUTION="1024x600"
            CPU_MODEL="n270"
            if command -v qemu-system-i386 >/dev/null 2>&1; then
                QEMU_BIN="qemu-system-i386"
            else
                QEMU_BIN="qemu-system-x86_64"
            fi
            ;;
        3|stress|extreme)
            PROFILE_NAME="Toshiba NB200 Extreme Stress-Test (Intel Atom • 512MB RAM • 1024x600)"
            MEM="512M"
            CPUS="1"
            RESOLUTION="1024x600"
            CPU_MODEL="n270"
            if command -v qemu-system-i386 >/dev/null 2>&1; then
                QEMU_BIN="qemu-system-i386"
            else
                QEMU_BIN="qemu-system-x86_64"
            fi
            ;;
        *)
            echo "Profilo non valido. Scegli '1' (Modern), '2' (Toshiba NB200) o '3' (Stress 512MB)."
            exit 1
            ;;
    esac

    local ISO_IMAGE
    ISO_IMAGE=$(find_iso_for_profile "$profile")

    echo "========================================================="
    echo "       OSify Virtual Testbed — Avvio Simulazione         "
    echo "========================================================="
    echo "[+] Profilo Attivo : $PROFILE_NAME"
    echo "[+] Binario QEMU   : $QEMU_BIN"
    echo "[+] Modello CPU    : $CPU_MODEL (Atom Diamondville 32-bit)"
    echo "[+] RAM Allocata   : $MEM"
    echo "[+] vCPU Assegnate : $CPUS"
    echo "[+] Risoluzione    : $RESOLUTION"
    echo "[+] Disco Target   : $DISK_IMAGE"

    local DISPLAY_OPT="default,show-cursor=on"
    if [[ "$(uname)" == "Darwin" ]]; then
        DISPLAY_OPT="cocoa,show-cursor=on"
    fi

    # Parametri base QEMU
    QEMU_ARGS=(
        -m "$MEM"
        -smp "$CPUS"
        -cpu "$CPU_MODEL"
        -drive file="$DISK_IMAGE",format=qcow2,if=virtio
        -net nic,model=virtio -net user,hostfwd=tcp::2222-:22
        -vga std
        -display "$DISPLAY_OPT"
        -usb -device usb-tablet
        -qmp unix:/tmp/osify-qmp.sock,server,nowait
    )

    # Accelerazione hardware solo se l'architettura host coincide
    if [[ "$(uname -m)" == "x86_64" && "$(uname)" == "Darwin" && "$QEMU_BIN" == "qemu-system-x86_64" ]]; then
        QEMU_ARGS+=(-accel hvf)
    elif [[ "$(uname)" == "Linux" && -e /dev/kvm && "$(uname -m)" == "x86_64" && "$QEMU_BIN" == "qemu-system-x86_64" ]]; then
        QEMU_ARGS+=(-enable-kvm)
    fi

    local KERNEL_BIN="$SCRIPT_DIR/live-kernel/bzImage"
    local INITRD_BIN="$SCRIPT_DIR/live-kernel/osify-initrd.gz"

    if [[ -f "$KERNEL_BIN" && -f "$INITRD_BIN" ]]; then
        echo "[+] Avvio Diretto Kernel OSify (Zero Wait Boot):"
        echo "    • Kernel : bzImage"
        echo "    • Initrd : osify-initrd.gz (Live RootFS)"
        QEMU_ARGS+=(
            -kernel "$KERNEL_BIN"
            -initrd "$INITRD_BIN"
            -append "root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet"
        )
    elif [[ -n "$ISO_IMAGE" && -f "$ISO_IMAGE" ]]; then
        echo "[+] Immagine ISO collegata: $(basename "$ISO_IMAGE")"
        QEMU_ARGS+=(-cdrom "$ISO_IMAGE" -boot d)
    else
        echo ""
        echo "[!] NOTA: Nessuna immagine ISO trovata."
        echo "    Avvio della VM in modalita' disco..."
        QEMU_ARGS+=(-boot c)
    fi

    echo ""
    echo "[+] Avvio istanza grafica QEMU per il Toshiba NB200..."
    echo "[i] Si aprira la finestra nativa di macOS con la VM."
    echo "[i] All'interno potrai eseguire il login (utente: root, senza password)."
    echo "[i] La directory di OSify e montabile con: mount -t 9p -o trans=virtio osify /mnt"
    echo "========================================================="
    exec "$QEMU_BIN" "${QEMU_ARGS[@]}"
}

menu() {
    echo "========================================================="
    echo "       OSify Virtual Testbed & Hardware Simulator        "
    echo "========================================================="
    echo "Seleziona l'ambiente che desideri simulare:"
    echo "  1) Modern Gaming & Streaming Rig (4 Core, 4GB RAM, 1080p)"
    echo "  2) Toshiba NB200 Netbook Simulator (Atom N270, 1GB RAM, 1024x600)"
    echo "  3) Toshiba NB200 Extreme Stress-Test (Atom N270, 512MB RAM, 1024x600)"
    echo "  4) Resetta disco virtuale di test"
    echo "========================================================="
    read -r -p "Scelta [1-4]: " choice

    case "$choice" in
        1) start_vm 1 ;;
        2) start_vm 2 ;;
        3) start_vm 3 ;;
        4) rm -f "$DISK_IMAGE" && echo "[✓] Disco virtuale resettato." ;;
        *) echo "Scelta non valida." ;;
    esac
}

if [[ $# -gt 0 ]]; then
    start_vm "$1"
else
    menu
fi
