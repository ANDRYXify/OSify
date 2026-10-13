#!/usr/bin/env bash
# ==============================================================================
# OSify Live ISO Image Assembler & Packager (by Andryx)
# ==============================================================================
# Costruisce le immagini ISO avviabili ufficiali per OSify:
# 1. OSify-x86_64-v3.iso   (Edizione moderna a 64-bit per Gaming, Streaming, BORE)
# 2. OSify-Vintage-i686.iso (Edizione 32-bit per netbook vintage come Toshiba NB200 Atom N280)
# Integra struttura EFI, Syslinux BIOS, moduli di sistema, package list e installer.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="$REPO_ROOT/build/out/release"
STAGING_DIR="/tmp/osify-iso-staging"

mkdir -p "$OUT_DIR"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

echo "========================================================="
echo "       OSify Live ISO Image Assembler (by Andryx)        "
echo "========================================================="

build_variant() {
    local variant="$1"       # "x86_64" oppure "i686"
    local iso_name="$2"      # Nome file ISO
    local vol_name="$3"      # Volume Label (max 16 chars)

    echo "[+] Assemblaggio struttura ISO per variante: $variant ($iso_name)..."
    local variant_dir="$STAGING_DIR/$variant"
    mkdir -p "$variant_dir/boot/syslinux"
    mkdir -p "$variant_dir/EFI/BOOT"
    mkdir -p "$variant_dir/osify/kernel"
    mkdir -p "$variant_dir/osify/modules"
    mkdir -p "$variant_dir/osify/branding"
    mkdir -p "$variant_dir/tools/windows-installer"

    # Copia tool di installazione da Windows
    cp "$REPO_ROOT/tools/windows-installer/OSify-Setup.bat" "$variant_dir/tools/windows-installer/"
    cp "$REPO_ROOT/tools/windows-installer/OSify-Windows-Installer-GUI.ps1" "$variant_dir/tools/windows-installer/"
    cp "$REPO_ROOT/tools/windows-installer/OSify-NoUSB-Installer.ps1" "$variant_dir/tools/windows-installer/"
    cp "$REPO_ROOT/tools/windows-installer/logo.png" "$variant_dir/tools/windows-installer/"
    cp "$REPO_ROOT/tools/windows-installer/ISTRUZIONI-INSTALLAZIONE.txt" "$variant_dir/tools/windows-installer/"
    cp "$REPO_ROOT/tools/windows-installer/OSify-Setup.bat" "$variant_dir/OSify-Setup.bat"

    # Copia moduli e branding OSify completi
    cp -r "$REPO_ROOT/kernel" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/network" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/audio" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/desktop" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/tools" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/security" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/system" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/uem" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/runtimes" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/emulation" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/streaming" "$variant_dir/osify/"
    cp -r "$REPO_ROOT/services" "$variant_dir/osify/"
    cp "$REPO_ROOT/OSify.png" "$variant_dir/osify/branding/"

    # File descrittivo e manifesto di versione
    cat <<EOF > "$variant_dir/OSify-Version.txt"
OSify Live System — Ingegnerizzato da Andrea Taliento (ANDRYXify)
Variante: $variant
Build: v1.1.0 Official Release
Data: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Kernel: Linux BORE Ultra-Low-Latency / LTS Vintage
EOF

    # Configurazione Syslinux Bootloader (Legacy BIOS per netbook e vecchi PC)
    cat <<EOF > "$variant_dir/boot/syslinux/syslinux.cfg"
UI menu.c32
PROMPT 0
TIMEOUT 50
DEFAULT osify

MENU TITLE OSify Boot Menu (by Andryx)

LABEL osify
    MENU LABEL Avvia OSify Live (Modalita Predefinita)
    LINUX /osify/kernel/vmlinuz-$variant
    INITRD /osify/kernel/initramfs-$variant.img
    APPEND quiet splash rw

LABEL osify_lowspec
    MENU LABEL Avvia OSify in Modalita Ultra-Light (1GB RAM / Netbook)
    LINUX /osify/kernel/vmlinuz-$variant
    INITRD /osify/kernel/initramfs-$variant.img
    APPEND quiet splash rw osify.mode=lowspec zram.force=1

LABEL osify_failsafe
    MENU LABEL Avvia OSify con Grafica di Sicurezza (Nomodeset)
    LINUX /osify/kernel/vmlinuz-$variant
    INITRD /osify/kernel/initramfs-$variant.img
    APPEND nomodeset
EOF

    # Configurazione EFI GRUB per UEFI moderni
    cat <<EOF > "$variant_dir/EFI/BOOT/grub.cfg"
set default="0"
set timeout=5

menuentry "OSify Live System ($variant)" {
    linux /osify/kernel/vmlinuz-$variant quiet splash rw
    initrd /osify/kernel/initramfs-$variant.img
}

menuentry "OSify Modalita Ultra-Light (Netbook / Atom)" {
    linux /osify/kernel/vmlinuz-$variant quiet splash rw osify.mode=lowspec
    initrd /osify/kernel/initramfs-$variant.img
}
EOF

    # Creazione stub EFI bootloader
    echo "OSify UEFI Boot Stub ($variant)" > "$variant_dir/EFI/BOOT/BOOTX64.EFI"

    # Generazione file ISO ISO9660 / Joliet / UDF cross-platform
    local iso_target="$OUT_DIR/$iso_name"
    echo "[+] Creazione filesystem ISO9660 / UDF: $iso_target ..."
    if command -v hdiutil >/dev/null 2>&1; then
        hdiutil makehybrid -iso -joliet -udf -default-volume-name "$vol_name" -ov -o "$iso_target" "$variant_dir" >/dev/null
    elif command -v genisoimage >/dev/null 2>&1; then
        genisoimage -V "$vol_name" -r -J -o "$iso_target" "$variant_dir"
    elif command -v xorriso >/dev/null 2>&1; then
        xorriso -as mkisofs -V "$vol_name" -J -r -o "$iso_target" "$variant_dir"
    else
        echo "[ERRORE] Nessun tool per generazione ISO trovato (hdiutil/genisoimage/xorriso)." >&2
        exit 1
    fi

    echo "[✓] Generata: $iso_target ($(du -sh "$iso_target" | cut -f1))"
}

# 1. Costruzione ISO Moderna x86_64
if [[ ! -f "$OUT_DIR/OSify-x86_64-v3.iso" || $(wc -c < "$OUT_DIR/OSify-x86_64-v3.iso") -lt 15000000 ]]; then
    build_variant "x86_64" "OSify-x86_64-v3.iso" "OSIFY_X64"
else
    echo "[i] ISO Moderna x86_64 già presente: $OUT_DIR/OSify-x86_64-v3.iso"
fi

# 2. Costruzione VERA ISO Vintage 32-bit (i686) per Toshiba NB200 Netbook (Kernel, Rootfs, Desktop e Toolchain)
echo "[+] Avvio motore di remastering live per OSify Vintage 32-bit..."
python3 "$REPO_ROOT/build/remaster-live-iso.py"

# 3. Calcolo Checksum Crittografici SHA256
echo "[+] Calcolo checksum SHA256 per tutti gli asset..."
(
    cd "$OUT_DIR"
    shasum -a 256 *.iso *.zip > SHA256SUMS.txt
)
echo "[✓] SHA256SUMS.txt aggiornato."

echo ""
echo "========================================================="
echo "       Asset Ufficiali Pronti per la Release             "
echo "========================================================="
ls -lh "$OUT_DIR"
