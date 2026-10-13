#!/bin/sh
# ==============================================================================
# OSify Bare-Metal Disk Installer — Installazione Autonoma su Disco Fisso
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Compatibile al 100% con POSIX /bin/sh, Busybox ash, Dash e GNU Bash.
# Supporta architetture UEFI x86_64 e BIOS/MBR i686 (Netbook Toshiba NB200).
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)"
TARGET_DISK="${1:-}"
TARGET_MODE="${2:-auto}"  # auto | uefi | bios
FS_TYPE="${3:-auto}"      # auto | btrfs | ext4
MOUNT_POINT="/mnt/osify_target"

log() { printf "\033[1;34m[OSify-Installer]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[ERRORE]\033[0m %s\n" "$*" >&2; }
ok()  { printf "\033[1;32m[SUCCESSO]\033[0m %s\n" "$*"; }

check_privileges() {
    if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
        err "L'installatore su disco rigido richiede i privilegi di root (esegui con sudo)."
        exit 1
    fi
}

detect_firmware_mode() {
    if [ "$TARGET_MODE" != "auto" ]; then
        echo "$TARGET_MODE"
        return
    fi
    if [ -d /sys/firmware/efi ]; then
        echo "uefi"
    else
        echo "bios"
    fi
}

get_part_names() {
    local_disk="$1"
    case "$local_disk" in
        *[0-9])
            echo "${local_disk}p1" "${local_disk}p2"
            ;;
        *)
            echo "${local_disk}1" "${local_disk}2"
            ;;
    esac
}

partition_disk_uefi() {
    d="$1"
    log "Partizionamento GPT per UEFI su $d..."
    dd if=/dev/zero of="$d" bs=1M count=10 conv=notrunc status=none 2>/dev/null || true
    
    if command -v parted >/dev/null 2>&1; then
        parted -s "$d" mklabel gpt
        parted -s "$d" mkpart "OSIFY_BOOT" fat32 1MiB 513MiB
        parted -s "$d" set 1 esp on
        parted -s "$d" mkpart "OSIFY_SYSTEM" btrfs 513MiB 100%
    else
        err "Comando 'parted' non trovato."
        exit 1
    fi

    partprobe "$d" 2>/dev/null || sleep 2
}

partition_disk_bios() {
    d="$1"
    log "Partizionamento MBR per BIOS Vintage (Toshiba NB200) su $d..."
    dd if=/dev/zero of="$d" bs=1M count=10 conv=notrunc status=none 2>/dev/null || true

    if command -v parted >/dev/null 2>&1; then
        parted -s "$d" mklabel msdos
        parted -s "$d" mkpart primary ext4 1MiB 100%
        parted -s "$d" set 1 boot on
    elif command -v fdisk >/dev/null 2>&1; then
        printf "o\nn\np\n1\n\n\na\n1\nw\n" | fdisk "$d" 2>/dev/null || true
    else
        err "Nessuna utilità di partizionamento disponibile (parted/fdisk)."
        exit 1
    fi

    partprobe "$d" 2>/dev/null || sleep 2
}

format_and_mount_btrfs() {
    d="$1"
    fw="$2"
    parts=$(get_part_names "$d")
    p1=$(echo "$parts" | awk '{print $1}')
    p2=$(echo "$parts" | awk '{print $2}')

    mkdir -p "$MOUNT_POINT"

    if [ "$fw" = "uefi" ]; then
        log "Formattazione Partizione EFI su $p1..."
        mkfs.vfat -F32 -n "OSIFY_BOOT" "$p1"

        log "Formattazione FileSystem Btrfs su $p2..."
        mkfs.btrfs -f -L "OSIFY_ROOT" "$p2"

        mount "$p2" "$MOUNT_POINT"
        btrfs subvolume create "$MOUNT_POINT/@"
        btrfs subvolume create "$MOUNT_POINT/@home"
        btrfs subvolume create "$MOUNT_POINT/@games_wine"
        btrfs subvolume create "$MOUNT_POINT/@var_log"
        btrfs subvolume create "$MOUNT_POINT/@snapshots"
        umount "$MOUNT_POINT"

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

    if command -v chattr >/dev/null 2>&1; then
        chattr +C "$MOUNT_POINT/opt/osify-games" 2>/dev/null || true
    fi
}

format_and_mount_ext4() {
    p1="$1"
    log "Formattazione Partizione Root Ext4 Ultra-Fast su $p1..."
    mkfs.ext4 -F -L "OSIFY_ROOT" -O dir_index,sparse_super "$p1"
    mkdir -p "$MOUNT_POINT"
    mount -o noatime,nodiratime,commit=60 "$p1" "$MOUNT_POINT"
    mkdir -p "$MOUNT_POINT/home" "$MOUNT_POINT/boot" "$MOUNT_POINT/opt/osify-games"
}

install_system_files() {
    log "Copia dell'albero di sistema OSify sul disco fisso..."
    mkdir -p "$MOUNT_POINT/opt/osify" "$MOUNT_POINT/usr/local/bin" "$MOUNT_POINT/etc/osify"

    if [ -d "$REPO_ROOT/uem" ]; then
        cp -r "$REPO_ROOT/uem" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi
    if [ -d "$REPO_ROOT/tools" ]; then
        cp -r "$REPO_ROOT/tools" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi
    if [ -d "$REPO_ROOT/desktop" ]; then
        cp -r "$REPO_ROOT/desktop" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi
    if [ -d "$REPO_ROOT/system" ]; then
        cp -r "$REPO_ROOT/system" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi
    if [ -f "$REPO_ROOT/OSify.png" ]; then
        cp "$REPO_ROOT/OSify.png" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi

    # Link binari in PATH globale
    ln -sf "/opt/osify/tools/osify-ctl" "$MOUNT_POINT/usr/local/bin/osify-ctl" 2>/dev/null || true
    ln -sf "/opt/osify/uem/runners/osify-inspect.sh" "$MOUNT_POINT/usr/local/bin/osify-inspect" 2>/dev/null || true
    ln -sf "/opt/osify/uem/runners/osify-universal-dispatcher.sh" "$MOUNT_POINT/usr/local/bin/osify-exec" 2>/dev/null || true

    # Configurazioni di sistema
    cat << 'EOF' > "$MOUNT_POINT/etc/os-release"
NAME="OSify"
PRETTY_NAME="OSify 2.0 LTS (Universal Matrix & Deck Edition)"
ID=osify
ID_LIKE="arch debian slitaz"
VERSION="2.0"
VERSION_ID="2.0"
HOME_URL="https://github.com/ANDRYXify/OSify"
EOF

    echo "osify-pc" > "$MOUNT_POINT/etc/hostname"
    cat << 'EOF' > "$MOUNT_POINT/etc/hosts"
127.0.0.1   localhost
127.0.1.1   osify-pc
::1         localhost ip6-localhost ip6-loopback
EOF

    # Creazione fstab ottimizzato
    log "Generazione fstab robusto..."
    cat << 'EOF' > "$MOUNT_POINT/etc/fstab"
# /etc/fstab: static file system information
LABEL=OSIFY_ROOT    /           auto    defaults,noatime,nodiratime    0 1
tmpfs               /tmp        tmpfs   defaults,nosuid,nodev,size=512M 0 0
EOF
}

configure_bootloader() {
    d="$1"
    fw="$2"
    log "Configurazione Bootloader per modalità: $fw..."

    if [ "$fw" = "uefi" ]; then
        mkdir -p "$MOUNT_POINT/boot/grub"
        cat << 'EOF' > "$MOUNT_POINT/boot/grub/grub.cfg"
set default=0
set timeout=3

menuentry "OSify Desktop System" {
    search --no-floppy --label --set=root OSIFY_ROOT
    linux /boot/vmlinuz root=LABEL=OSIFY_ROOT rw quiet splash
    initrd /boot/initramfs
}
EOF
        if command -v grub-install >/dev/null 2>&1; then
            grub-install --target=x86_64-efi --efi-directory="$MOUNT_POINT/boot/efi" --bootloader-id=OSify --recheck 2>/dev/null || true
        fi
    else
        # BIOS Vintage MBR
        mkdir -p "$MOUNT_POINT/boot/syslinux"
        cat << 'EOF' > "$MOUNT_POINT/boot/syslinux/syslinux.cfg"
DEFAULT osify
PROMPT 0
TIMEOUT 30

LABEL osify
    MENU LABEL OSify Vintage Edition
    LINUX /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=LABEL=OSIFY_ROOT rw quiet lang=it_IT kmap=it
EOF
        if command -v extlinux >/dev/null 2>&1; then
            extlinux --install "$MOUNT_POINT/boot/syslinux" 2>/dev/null || true
        fi
        if command -v dd >/dev/null 2>&1 && [ -f /usr/lib/syslinux/mbr.bin ]; then
            dd bs=440 count=1 conv=notrunc if=/usr/lib/syslinux/mbr.bin of="$d" 2>/dev/null || true
        fi
    fi
}

cleanup_mounts() {
    log "Sincronizzazione buffer e smontaggio..."
    sync
    umount -R "$MOUNT_POINT" 2>/dev/null || true
}

interactive_wizard() {
    clear
    printf "\033[1;36m"
    cat << 'EOF'
  ██████╗ ███████╗██╗███████╗██╗   ██╗
 ██╔═══██╗██╔════╝██║██╔════╝╚██╗ ██╔╝
 ██║   ██║███████╗██║█████╗   ╚████╔╝ 
 ██║   ██║╚════██║██║██╔══╝    ╚██╔╝  
 ╚██████╔╝███████║██║██║        ██║   
  ╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝   
EOF
    printf "\033[0m\n"
    printf "\033[1;37m=================================================================\033[0m\n"
    printf "\033[1;32m      OSify Bare-Metal System Installer — Procedura Guidata       \033[0m\n"
    printf "\033[1;34m      Ingegnerizzato da Andrea Taliento (ANDRYXify)              \033[0m\n"
    printf "\033[1;37m=================================================================\033[0m\n\n"

    fw="$(detect_firmware_mode)"
    fw_upper="$(echo "$fw" | tr '[:lower:]' '[:upper:]')"
    echo "• Firmware Rilevato : $fw_upper ($(uname -m))"
    echo "• Kernel Attivo     : $(uname -srm)"
    echo "• Memoria RAM       : $(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo 'N/A')"
    echo ""

    echo "[1/3] Rilevamento dischi rigidi disponibili per l'installazione:"
    echo "-----------------------------------------------------------------"
    
    disks_file="/tmp/osify_disks.txt"
    rm -f "$disks_file"
    lsblk -d -n -o NAME,SIZE,MODEL,TRAN,TYPE 2>/dev/null | grep -E "disk" | grep -v "loop" > "$disks_file" || true

    if [ ! -s "$disks_file" ]; then
        err "Nessun disco fisso o drive d'installazione rilevato nel sistema."
        echo "Controlla le connessioni disco o lo stato dei driver SATA/NVMe."
        rm -f "$disks_file"
        exit 1
    fi

    idx=1
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            dname="$(echo "$line" | awk '{print $1}')"
            dsize="$(echo "$line" | awk '{print $2}')"
            dmodel="$(echo "$line" | cut -d' ' -f3-)"
            printf "  \033[1;32m[%d]\033[0m \033[1m/dev/%s\033[0m  —  Dimensione: \033[1;33m%s\033[0m  (Modello: %s)\n" "$idx" "$dname" "$dsize" "$dmodel"
            idx=$((idx + 1))
        fi
    done < "$disks_file"
    total_disks=$((idx - 1))

    echo ""
    echo "  [0] Annulla ed esci dall'installer"
    echo ""
    printf "Seleziona il numero del disco su cui installare OSify [1-%d]: " "$total_disks"
    read -r choice

    if [ "$choice" = "0" ] || [ -z "$choice" ]; then
        echo "Installazione annullata dall'utente."
        rm -f "$disks_file"
        exit 0
    fi

    case "$choice" in
        *[!0-9]*)
            err "Selezione non valida."
            rm -f "$disks_file"
            exit 1
            ;;
    esac

    if [ "$choice" -lt 1 ] || [ "$choice" -gt "$total_disks" ]; then
        err "Selezione non valida."
        rm -f "$disks_file"
        exit 1
    fi

    selected_line="$(sed -n "${choice}p" "$disks_file")"
    selected_name="$(echo "$selected_line" | awk '{print $1}')"
    TARGET_DISK="/dev/$selected_name"
    rm -f "$disks_file"

    log "Hai selezionato il disco: $TARGET_DISK"
    echo ""

    echo "[2/3] Scelta del profilo Filesystem e Ottimizzazione Storage:"
    echo "-----------------------------------------------------------------"
    if [ "$fw" = "bios" ] || [ "$(uname -m)" = "i686" ]; then
        printf "  \033[1;32m[1]\033[0m \033[1mExt4 Ultra-Fast (Raccomandato per Netbook/Atom/HDD 5400rpm)\033[0m\n"
        echo "      Minimo overhead di I/O, noatime, fluido e resistente."
        echo "  [2] Btrfs con compressione trasparente zstd"
        printf "Scelta [Predefinito: 1]: "
        read -r fs_choice
        if [ "$fs_choice" = "2" ]; then
            FS_TYPE="btrfs"
        else
            FS_TYPE="ext4"
        fi
    else
        printf "  \033[1;32m[1]\033[0m \033[1mBtrfs Modern con compressione zstd (Raccomandato per SSD/NVMe)\033[0m\n"
        echo "      Istantanee subvolumi CoW, risparmio spazio e massima integrità."
        echo "  [2] Ext4 Standard"
        printf "Scelta [Predefinito: 1]: "
        read -r fs_choice
        if [ "$fs_choice" = "2" ]; then
            FS_TYPE="ext4"
        else
            FS_TYPE="btrfs"
        fi
    fi
    log "Profilo Filesystem selezionato: $FS_TYPE"
    echo ""

    printf "\033[1;31m=================================================================\033[0m\n"
    printf "\033[1;31m                      AVVISO IRREVERSIBILE                      \033[0m\n"
    printf "\033[1;31m=================================================================\033[0m\n"
    echo "L'installazione cancellerà TUTTE le partizioni e i dati presenti su:"
    echo "  Disco bersaglio : $TARGET_DISK"
    echo "  Filesystem      : $FS_TYPE"
    echo "  Modalità Boot   : $fw"
    echo ""
    printf "Per confermare e avviare la scrittura digita 'OSIFY' in maiuscolo: "
    read -r confirm

    if [ "$confirm" != "OSIFY" ]; then
        echo "Conferma non valida ('$confirm'). Operazione interrotta per sicurezza."
        exit 1
    fi
    log "Conferma ricevuta. Inizio installazione autonoma..."
}

main() {
    check_privileges

    if [ -z "$TARGET_DISK" ]; then
        interactive_wizard
    else
        if [ ! -b "$TARGET_DISK" ]; then
            err "Il target '$TARGET_DISK' non è un dispositivo a blocchi valido."
            exit 1
        fi
    fi

    fw="$(detect_firmware_mode)"
    log "Avvio installazione su: $TARGET_DISK (Modalità: $fw, Filesystem: $FS_TYPE)"

    if [ "$fw" = "uefi" ]; then
        partition_disk_uefi "$TARGET_DISK"
    else
        partition_disk_bios "$TARGET_DISK"
    fi

    parts=$(get_part_names "$TARGET_DISK")
    p1=$(echo "$parts" | awk '{print $1}')

    if [ "$FS_TYPE" = "ext4" ] && [ "$fw" = "bios" ]; then
        format_and_mount_ext4 "$p1"
    else
        format_and_mount_btrfs "$TARGET_DISK" "$fw"
    fi

    install_system_files
    configure_bootloader "$TARGET_DISK" "$fw"
    cleanup_mounts

    echo ""
    printf "\033[1;32m=================================================================\033[0m\n"
    ok "INSTALLAZIONE DI OSIFY COMPLETATA CON SUCCESSO SUL DISCO: $TARGET_DISK"
    printf "\033[1;32m=================================================================\033[0m\n"
    echo "Il sistema operativo OSify è ora installato e configurato permanentemente."
    echo "Puoi rimuovere la chiavetta USB o il supporto di installazione e riavviare."
    echo ""
    printf "Desideri riavviare il computer adesso? [S/n]: "
    read -r do_reboot
    case "$do_reboot" in
        [Nn]*)
            log "Installazione terminata. Puoi continuare a usare la sessione Live."
            ;;
        *)
            log "Riavvio del computer in corso..."
            reboot 2>/dev/null || true
            ;;
    esac
}

main "$@"
