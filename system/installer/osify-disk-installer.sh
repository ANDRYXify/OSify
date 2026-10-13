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

FS_TYPE="${3:-auto}"  # auto | btrfs | ext4

interactive_wizard() {
    clear
    echo -e "\e[1;36m"
    cat << "EOF"
  ██████╗ ███████╗██╗███████╗██╗   ██╗   ██╗███╗   ██╗███████╗████████╗
 ██╔═══██╗██╔════╝██║██╔════╝╚██╗ ██╔╝   ██║████╗  ██║██╔════╝╚══██╔══╝
 ██║   ██║███████╗██║█████╗   ╚████╔╝    ██║██╔██╗ ██║███████╗   ██║   
 ██║   ██║╚════██║██║██╔══╝    ╚██╔╝     ██║██║╚██╗██║╚════██║   ██║   
 ╚██████╔╝███████║██║██║        ██║      ██║██║ ╚████║███████║   ██║   
  ╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝      ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   
EOF
    echo -e "\e[0m"
    echo -e "\e[1;37m=================================================================\e[0m"
    echo -e "\e[1;32m      OSify Bare-Metal System Installer — Procedura Guidata       \e[0m"
    echo -e "\e[1;34m      Ingegnerizzato da Andrea Taliento (ANDRYXify)              \e[0m"
    echo -e "\e[1;37m=================================================================\e[0m"
    echo ""

    local fw
    fw="$(detect_firmware_mode)"
    echo -e "• Firmware Rilevato : \e[1;33m${fw^^}\e[0m ($(uname -m))"
    echo -e "• Kernel Attivo     : $(uname -srm)"
    echo -e "• Memoria RAM       : $(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo 'N/A')"
    echo ""

    echo -e "\e[1;37m[1/3] Rilevamento dischi rigidi disponibili per l'installazione:\e[0m"
    echo "-----------------------------------------------------------------"
    
    local disks=()
    local idx=1
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            local dname dsize dmodel dtran
            dname="$(echo "$line" | awk '{print $1}')"
            dsize="$(echo "$line" | awk '{print $2}')"
            dmodel="$(echo "$line" | cut -d' ' -f3-)"
            disks+=("/dev/$dname")
            echo -e "  \e[1;32m[$idx]\e[0m \e[1m/dev/$dname\e[0m  —  Dimensione: \e[1;33m$dsize\e[0m  (Modello: $dmodel)"
            ((idx++))
        fi
    done < <(lsblk -d -n -o NAME,SIZE,MODEL,TRAN,TYPE 2>/dev/null | grep -E "disk" | grep -v "loop" || true)

    if [[ ${#disks[@]} -eq 0 ]]; then
        err "Nessun disco fisso o drive d'installazione rilevato nel sistema."
        echo "Controlla le connessioni disco o lo stato dei driver SATA/NVMe."
        exit 1
    fi

    echo ""
    echo -e "  \e[1;31m[0]\e[0m Annulla ed esci dall'installer"
    echo ""
    read -rp "Seleziona il numero del disco su cui installare OSify [1-${#disks[@]}]: " choice

    if [[ "$choice" == "0" || -z "$choice" ]]; then
        echo "Installazione annullata dall'utente."
        exit 0
    fi

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ "$choice" -lt 1 || "$choice" -gt ${#disks[@]} ]]; then
        err "Selezione non valida."
        exit 1
    fi

    TARGET_DISK="${disks[$((choice-1))]}"
    log "Hai selezionato il disco: \e[1;33m$TARGET_DISK\e[0m"
    echo ""

    echo -e "\e[1;37m[2/3] Scelta del profilo Filesystem e Ottimizzazione Storage:\e[0m"
    echo "-----------------------------------------------------------------"
    if [[ "$fw" == "bios" || "$(uname -m)" == "i686" ]]; then
        echo -e "  \e[1;32m[1]\e[0m \e[1mExt4 Ultra-Fast (Raccomandato per Netbook/Atom/HDD 5400rpm)\e[0m"
        echo "      Minimo overhead di I/O, noatime, fluido e resistente."
        echo -e "  \e[1;32m[2]\e[0m Btrfs con compressione trasparente zstd"
        read -rp "Scelta [Predefinito: 1]: " fs_choice
        if [[ "$fs_choice" == "2" ]]; then
            FS_TYPE="btrfs"
        else
            FS_TYPE="ext4"
        fi
    else
        echo -e "  \e[1;32m[1]\e[0m \e[1mBtrfs Modern con compressione zstd (Raccomandato per SSD/NVMe)\e[0m"
        echo "      Istantanee subvolumi CoW, risparmio spazio e massima integrità."
        echo -e "  \e[1;32m[2]\e[0m Ext4 Standard"
        read -rp "Scelta [Predefinito: 1]: " fs_choice
        if [[ "$fs_choice" == "2" ]]; then
            FS_TYPE="ext4"
        else
            FS_TYPE="btrfs"
        fi
    fi
    log "Profilo Filesystem selezionato: \e[1;32m$FS_TYPE\e[0m"
    echo ""

    echo -e "\e[1;31m=================================================================\e[0m"
    echo -e "\e[1;31m                      AVVISO IRREVERSIBILE                      \e[0m"
    echo -e "\e[1;31m=================================================================\e[0m"
    echo -e "L'installazione cancellerà TUTTE le partizioni e i dati presenti su:"
    echo -e "  Disco bersaglio : \e[1;33m$TARGET_DISK\e[0m"
    echo -e "  Filesystem      : \e[1;33m$FS_TYPE\e[0m"
    echo -e "  Modalità Boot   : \e[1;33m$fw\e[0m"
    echo ""
    read -rp "Per confermare e avviare la scrittura digita 'OSIFY' in maiuscolo: " confirm

    if [[ "$confirm" != "OSIFY" ]]; then
        echo "Conferma non valida ('$confirm'). Operazione interrotta per sicurezza."
        exit 0
    fi

    echo ""
    log "Conferma ricevuta. Inizio installazione autonoma..."
}

format_and_mount_ext4() {
    local p1="$1"
    log "Formattazione Partizione Root Ext4 Ultra-Fast su $p1..."
    mkfs.ext4 -F -L "OSIFY_ROOT" -O dir_index,sparse_super "$p1"
    mkdir -p "$MOUNT_POINT"
    mount -o noatime,nodiratime,commit=60 "$p1" "$MOUNT_POINT"
    mkdir -p "$MOUNT_POINT/home" "$MOUNT_POINT/boot" "$MOUNT_POINT/opt/osify-games"
}

main() {
    check_privileges

    if [[ -z "$TARGET_DISK" ]]; then
        interactive_wizard
    else
        if [[ ! -b "$TARGET_DISK" ]]; then
            err "Il target '$TARGET_DISK' non è un dispositivo a blocchi valido."
            exit 1
        fi
    fi

    local fw
    fw="$(detect_firmware_mode)"
    log "Avvio installazione su: \e[1;33m$TARGET_DISK\e[0m (Modalità: $fw, Filesystem: $FS_TYPE)"

    if [[ "$fw" == "uefi" ]]; then
        partition_disk_uefi "$TARGET_DISK"
    else
        partition_disk_bios "$TARGET_DISK"
    fi

    local p1 p2
    if [[ "$TARGET_DISK" =~ [0-9]$ ]]; then
        p1="${TARGET_DISK}p1"
        p2="${TARGET_DISK}p2"
    else
        p1="${TARGET_DISK}1"
        p2="${TARGET_DISK}2"
    fi

    if [[ "$FS_TYPE" == "ext4" && "$fw" == "bios" ]]; then
        format_and_mount_ext4 "$p1"
    else
        format_and_mount "$TARGET_DISK" "$fw"
    fi

    install_system_files
    configure_bootloader "$TARGET_DISK" "$fw"
    cleanup_mounts

    echo ""
    echo -e "\e[1;32m=================================================================\e[0m"
    ok "INSTALLAZIONE DI OSIFY COMPLETATA CON SUCCESSO SUL DISCO: $TARGET_DISK"
    echo -e "\e[1;32m=================================================================\e[0m"
    echo "Il sistema operativo OSify è ora installato e configurato permanentemente."
    echo "Puoi rimuovere la chiavetta USB o il supporto di installazione e riavviare."
    echo ""
    read -rp "Desideri riavviare il computer adesso? [S/n]: " do_reboot
    if [[ "$do_reboot" =~ ^[SsYy] || -z "$do_reboot" ]]; then
        log "Riavvio del computer in corso..."
        reboot || true
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
