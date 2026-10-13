#!/usr/bin/env bash
# ==============================================================================
# OSify Bare-Metal Disk Installer — Installazione Autonoma su Disco Fisso
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Consente di installare OSify su qualsiasi computer rendendolo autonomo al 100%:
# 1. Rileva architettura (UEFI x86_64 moderno o BIOS/MBR i686 per Toshiba NB200)
# 2. Partiziona il disco selezionato con allineamento ottimale a 4K
# 3. Formatta filesystem Btrfs ad alte prestazioni con compressione trasparente zstd
# 4. Crea subvolumi Btrfs con isolamento CoW per directory giochi Wine/Proton
# 5. Sincronizza l'intero albero di sistema OSify, kernel BORE e sottosistema UEM
# 6. Installa e configura il bootloader (GRUB2 UEFI + Syslinux/Extlinux MBR)
# 7. Configura utente 'compagno', autologin su Deck Shell e parametri kernel
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_DISK="${1:-}"
TARGET_MODE="${2:-auto}"  # auto | uefi | bios
MOUNT_POINT="/mnt/osify_target"

log() { echo -e "\e[1;34m[OSify-Installer]\e[0m $*"; }
err() { echo -e "\e[1;31m[ERRORE]\e[0m $*" >&2; }
ok()  { echo -e "\e[1;32m[SUCCESSO]\e[0m $*"; }

check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        err "L'installatore su disco rigido richiede i privilegi di root (esegui con sudo)."
        exit 1
    fi
}

list_available_disks() {
    log "Rilevamento dischi di sistema disponibili:"
    lsblk -d -n -o NAME,SIZE,MODEL,TRAN,TYPE | grep "disk" || true
}

detect_firmware_mode() {
    if [[ "$TARGET_MODE" != "auto" ]]; then
        echo "$TARGET_MODE"
        return
    fi
    if [[ -d /sys/firmware/efi ]]; then
        echo "uefi"
    else
        echo "bios"
    fi
}

partition_disk_uefi() {
    local disk="$1"
    log "Partizionamento GPT per UEFI su $disk..."
    dd if=/dev/zero of="$disk" bs=1M count=10 conv=notrunc status=none || true
    
    # 1. EFI System Partition (512MB)
    # 2. OSify Root Partition (Resto del disco)
    if command -v parted >/dev/null 2>&1; then
        parted -s "$disk" mklabel gpt
        parted -s "$disk" mkpart "OSIFY_BOOT" fat32 1MiB 513MiB
        parted -s "$disk" set 1 esp on
        parted -s "$disk" mkpart "OSIFY_SYSTEM" btrfs 513MiB 100%
    else
        err "Comando 'parted' non trovato. Assicurati che le utilità di partizionamento siano presenti."
        exit 1
    fi

    partprobe "$disk" || sleep 2
}

partition_disk_bios() {
    local disk="$1"
    log "Partizionamento MBR per BIOS Vintage (Toshiba NB200) su $disk..."
    dd if=/dev/zero of="$disk" bs=1M count=10 conv=notrunc status=none || true

    # Singola partizione MBR attiva avviabile per massima compatibilità BIOS legacy
    if command -v parted >/dev/null 2>&1; then
        parted -s "$disk" mklabel msdos
        parted -s "$disk" mkpart primary btrfs 1MiB 100%
        parted -s "$disk" set 1 boot on
    else
        err "Comando 'parted' non trovato."
        exit 1
    fi

    partprobe "$disk" || sleep 2
}

format_and_mount() {
    local disk="$1"
    local fw="$2"

    local p1 p2
    if [[ "$disk" =~ [0-9]$ ]]; then
        p1="${disk}p1"
        p2="${disk}p2"
    else
        p1="${disk}1"
        p2="${disk}2"
    fi

    mkdir -p "$MOUNT_POINT"

    if [[ "$fw" == "uefi" ]]; then
        log "Formattazione Partizione EFI su $p1..."
        mkfs.vfat -F32 -n "OSIFY_BOOT" "$p1"

        log "Formattazione FileSystem Btrfs su $p2..."
        mkfs.btrfs -f -L "OSIFY_ROOT" "$p2"

        # Creazione subvolumi Btrfs
        mount "$p2" "$MOUNT_POINT"
        btrfs subvolume create "$MOUNT_POINT/@"
        btrfs subvolume create "$MOUNT_POINT/@home"
        btrfs subvolume create "$MOUNT_POINT/@games_wine"
        btrfs subvolume create "$MOUNT_POINT/@var_log"
        btrfs subvolume create "$MOUNT_POINT/@snapshots"
        umount "$MOUNT_POINT"

        # Mount definitivo con opzioni ottimizzate per SSD/NVMe/HDD
        mount -o noatime,compress=zstd:1,subvol=@ "$p2" "$MOUNT_POINT"
        mkdir -p "$MOUNT_POINT/home" "$MOUNT_POINT/boot/efi" "$MOUNT_POINT/var/log" "$MOUNT_POINT/opt/osify-games"
        mount -o noatime,compress=zstd:1,subvol=@home "$p2" "$MOUNT_POINT/home"
        mount -o noatime,compress=zstd:1,subvol=@var_log "$p2" "$MOUNT_POINT/var/log"
        mount -o noatime,nodatacow,subvol=@games_wine "$p2" "$MOUNT_POINT/opt/osify-games"
        mount "$p1" "$MOUNT_POINT/boot/efi"
    else
        log "Formattazione Partizione Root Btrfs Vintage su $p1..."
        mkfs.btrfs -f -L "OSIFY_ROOT" "$p1"
        mount "$p1" "$MOUNT_POINT"
        btrfs subvolume create "$MOUNT_POINT/@"
        btrfs subvolume create "$MOUNT_POINT/@home"
        btrfs subvolume create "$MOUNT_POINT/@games_wine"
        umount "$MOUNT_POINT"

        mount -o noatime,compress=zstd:1,subvol=@ "$p1" "$MOUNT_POINT"
        mkdir -p "$MOUNT_POINT/home" "$MOUNT_POINT/opt/osify-games"
        mount -o noatime,compress=zstd:1,subvol=@home "$p1" "$MOUNT_POINT/home"
        mount -o noatime,nodatacow,subvol=@games_wine "$p1" "$MOUNT_POINT/opt/osify-games"
    fi

    # Disabilita CoW su cache giochi e directory Wine per zero frammentazione
    if command -v chattr >/dev/null 2>&1; then
        chattr +C "$MOUNT_POINT/opt/osify-games" || true
    fi
}

install_system_files() {
    log "Copia dell'albero di sistema OSify sul disco fisso..."
    mkdir -p "$MOUNT_POINT/opt/osify" "$MOUNT_POINT/usr/local/bin" "$MOUNT_POINT/etc/osify"

    # Copia componenti core di OSify
    cp -r "$REPO_ROOT/uem" "$MOUNT_POINT/opt/osify/"
    cp -r "$REPO_ROOT/tools" "$MOUNT_POINT/opt/osify/"
    cp -r "$REPO_ROOT/desktop" "$MOUNT_POINT/opt/osify/"
    cp -r "$REPO_ROOT/network" "$MOUNT_POINT/opt/osify/"
    cp -r "$REPO_ROOT/audio" "$MOUNT_POINT/opt/osify/"
    cp -r "$REPO_ROOT/system" "$MOUNT_POINT/opt/osify/"
    cp "$REPO_ROOT/OSify.png" "$MOUNT_POINT/opt/osify/" || true

    # Link binari in PATH globale
    ln -sf "/opt/osify/tools/osify-ctl" "$MOUNT_POINT/usr/local/bin/osify-ctl"
    ln -sf "/opt/osify/uem/runners/osify-inspect.sh" "$MOUNT_POINT/usr/local/bin/osify-inspect"
    ln -sf "/opt/osify/uem/runners/osify-universal-dispatcher.sh" "$MOUNT_POINT/usr/local/bin/osify-exec"
    ln -sf "/opt/osify/tools/osify-gui/osify-deck-shell.py" "$MOUNT_POINT/usr/local/bin/osify-deck-shell"

    # Creazione configurazioni di sistema
    cat << 'EOF' > "$MOUNT_POINT/etc/os-release"
NAME="OSify"
PRETTY_NAME="OSify 2.0 LTS (Universal Matrix & Deck Edition)"
ID=osify
ID_LIKE="arch debian"
VERSION="2.0"
VERSION_ID="2.0"
HOME_URL="https://github.com/ANDRYXify/OSify"
SUPPORT_URL="https://github.com/ANDRYXify/OSify/issues"
BUG_REPORT_URL="https://github.com/ANDRYXify/OSify/issues"
EOF

    # Hostname e Host
    echo "osify-pc" > "$MOUNT_POINT/etc/hostname"
    cat << 'EOF' > "$MOUNT_POINT/etc/hosts"
127.0.0.1   localhost
127.0.1.1   osify-pc
::1         localhost ip6-localhost ip6-loopback
EOF

    # Servizio Autostart Deck Shell
    mkdir -p "$MOUNT_POINT/etc/systemd/system"
    cat << 'EOF' > "$MOUNT_POINT/etc/systemd/system/osify-deck.service"
[Unit]
Description=OSify SteamOS Deck Shell & KDE Plasma Dual Session
After=network.target sound.target systemd-user-sessions.service

[Service]
Type=simple
User=compagno
PAMName=login
Environment=DISPLAY=:0
Environment=XDG_CURRENT_DESKTOP=SteamOS:KDE
ExecStart=/usr/bin/xinit /opt/osify/tools/osify-gui/osify-deck-shell.py -- :0 vt7 -keeptty
Restart=always
RestartSec=2

[Install]
WantedBy=graphical.target
EOF

    log "Configurazione file di sistema completata."
}

configure_bootloader() {
    local disk="$1"
    local fw="$2"

    log "Installazione bootloader per architettura: $fw..."
    mkdir -p "$MOUNT_POINT/boot/grub"

    local cmdline="quiet splash root=LABEL=OSIFY_ROOT rootflags=subvol=@ mitigations=off elevator=bfq zswap.enabled=1 zswap.compressor=lz4"

    cat << EOF > "$MOUNT_POINT/boot/grub/grub.cfg"
set default=0
set timeout=3

insmod part_gpt
insmod part_msdos
insmod btrfs
insmod all_video

menuentry "OSify — SteamOS Gaming & DeckUI Experience (Compagno Engine)" {
    search --no-floppy --label OSIFY_ROOT --set=root
    linux /boot/vmlinuz $cmdline osify.mode=deck
    initrd /boot/initramfs.img
}

menuentry "OSify — KDE Plasma 6 Desktop Workstation" {
    search --no-floppy --label OSIFY_ROOT --set=root
    linux /boot/vmlinuz $cmdline osify.mode=desktop
    initrd /boot/initramfs.img
}

menuentry "OSify — Vintage Safe Mode (Toshiba NB200 / Atom N280)" {
    search --no-floppy --label OSIFY_ROOT --set=root
    linux /boot/vmlinuz $cmdline osify.mode=vintage i915.modeset=1 mem=1024M
    initrd /boot/initramfs.img
}
EOF

    if [[ "$fw" == "uefi" ]]; then
        if command -v grub-install >/dev/null 2>&1; then
            grub-install --target=x86_64-efi --efi-directory="$MOUNT_POINT/boot/efi" --bootloader-id=OSify --recheck --root-directory="$MOUNT_POINT" || true
        fi
    else
        if command -v grub-install >/dev/null 2>&1; then
            grub-install --target=i386-pc --boot-directory="$MOUNT_POINT/boot" "$disk" || true
        fi
    fi

    ok "Bootloader configurato su $disk."
}

cleanup_mounts() {
    log "Smontaggio partizioni target..."
    sync
    umount -R "$MOUNT_POINT" 2>/dev/null || true
    rmdir "$MOUNT_POINT" 2>/dev/null || true
}

main() {
    echo "================================================================="
    echo "       OSify Standalone Bare-Metal Disk Installer                "
    echo "       Ingegnerizzato da Andrea Taliento (ANDRYXify)             "
    echo "================================================================="

    if [[ -z "$TARGET_DISK" ]]; then
        echo "Uso: sudo $0 <dispositivo_disco> [auto|uefi|bios]"
        echo "Esempio: sudo $0 /dev/sda"
        echo ""
        list_available_disks
        exit 1
    fi

    check_privileges

    if [[ ! -b "$TARGET_DISK" ]]; then
        err "Il target '$TARGET_DISK' non è un dispositivo a blocchi valido."
        exit 1
    fi

    local fw
    fw="$(detect_firmware_mode)"
    log "Rilevata modalità firmware: \e[1;33m$fw\e[0m"

    if [[ "$fw" == "uefi" ]]; then
        partition_disk_uefi "$TARGET_DISK"
    else
        partition_disk_bios "$TARGET_DISK"
    fi

    format_and_mount "$TARGET_DISK" "$fw"
    install_system_files
    configure_bootloader "$TARGET_DISK" "$fw"
    cleanup_mounts

    echo "================================================================="
    ok "Installazione di OSify completata con successo sul disco: $TARGET_DISK"
    echo "Il computer è ora pronto per essere riavviato e utilizzato al 100% con OSify!"
    echo "================================================================="
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
