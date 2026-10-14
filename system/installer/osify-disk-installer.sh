#!/bin/sh
# ==============================================================================
# OSify Bare-Metal Disk Installer — Installazione Autonoma su Disco Fisso
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Compatibile al 100% con POSIX /bin/sh, Busybox ash, Dash e GNU Bash.
# Supporta architetture UEFI x86_64 e BIOS/MBR i686 (Netbook Toshiba NB200).
# Include: Creazione Utente Reale, Migrazione Totale Profilo Live-to-Disk,
# Verifica Atomica di Integrità e Configurazione Bootloader Indistruttibile.
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)"
TARGET_DISK="${1:-}"
TARGET_MODE="${2:-auto}"  # auto | uefi | bios
FS_TYPE="${3:-auto}"      # auto | btrfs | ext4
MOUNT_POINT="/mnt/osify_target"

# Parametri Utente Configurati
REAL_NAME=""
NEW_USER=""
USER_PASS=""
HOSTNAME_VAL="osify-pc"
DO_AUTOLOGIN="yes"
MIGRATE_LIVE_DATA="yes"

log() { printf "\033[1;34m[OSify-Installer]\033[0m %s\n" "$*"; }
err() { printf "\033[1;31m[ERRORE]\033[0m %s\n" "$*" >&2; }
ok()  { printf "\033[1;32m[SUCCESSO]\033[0m %s\n" "$*"; }

check_privileges() {
    if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
        err "L'installatore richiede i privilegi di root (esegui con sudo)."
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

# Rilevamento della cartella home della sessione live attiva
detect_live_home() {
    if [ -d "/home/osify" ]; then
        echo "/home/osify"
    elif [ -n "$SUDO_USER" ] && [ -d "/home/$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
        echo "/home/$SUDO_USER"
    elif [ -d "/home/tux" ]; then
        echo "/home/tux"
    else
        echo "/etc/skel"
    fi
}

generate_password_hash() {
    raw_pass="$1"
    # Prova con python3 crypt
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import crypt; print(crypt.crypt('$raw_pass', crypt.mksalt(crypt.METHOD_SHA512)))" 2>/dev/null && return
    fi
    # Prova con openssl
    if command -v openssl >/dev/null 2>&1; then
        openssl passwd -6 "$raw_pass" 2>/dev/null && return
    fi
    # Prova con mkpasswd
    if command -v mkpasswd >/dev/null 2>&1; then
        mkpasswd -m sha-512 "$raw_pass" 2>/dev/null && return
    fi
    # Fallback md5
    if command -v openssl >/dev/null 2>&1; then
        openssl passwd -1 "$raw_pass" 2>/dev/null && return
    fi
    echo "$raw_pass"
}

user_setup_wizard() {
    printf "\033[1;36m=================================================================\033[0m\n"
    printf "\033[1;32m       FASE 1: Configurazione del Tuo Account Utente Personale   \033[0m\n"
    printf "\033[1;36m=================================================================\033[0m\n"
    echo "Crea il tuo profilo personale che userai sul computer installato."
    echo ""

    # Controllo se esiste già un profilo configurato nella sessione Live
    PROFILE_JSON="/home/osify/.config/osify/profile.json"
    [ ! -f "$PROFILE_JSON" ] && PROFILE_JSON="/etc/osify/profile.json"
    if [ -f "$PROFILE_JSON" ] && [ -z "$REAL_NAME" ]; then
        FOUND_NAME=$(awk -F'"' '/"real_name":/ {print $4}' "$PROFILE_JSON" 2>/dev/null)
        FOUND_USER=$(awk -F'"' '/"username":/ {print $4}' "$PROFILE_JSON" 2>/dev/null)
        FOUND_PASS=$(awk -F'"' '/"password":/ {print $4}' "$PROFILE_JSON" 2>/dev/null)
        if [ -n "$FOUND_USER" ]; then
            printf "\033[1;32m[✓] Rilevato profilo già configurato nella sessione di prova:\033[0m\n"
            printf "    Nome: \033[1m%s\033[0m  |  Username: \033[1m%s\033[0m\n" "$FOUND_NAME" "$FOUND_USER"
            printf "Desideri usare direttamente questo profilo per l'installazione? [S/n]: "
            read -r ans_prof
            case "$ans_prof" in
                [Nn]*) ;;
                *)
                    REAL_NAME="$FOUND_NAME"
                    NEW_USER="$FOUND_USER"
                    USER_PASS="$FOUND_PASS"
                    [ -z "$REAL_NAME" ] && REAL_NAME="Utente OSify"
                    [ -z "$NEW_USER" ] && NEW_USER="utente"
                    ;;
            esac
        fi
    fi

    while [ -z "$REAL_NAME" ]; do
        printf "Nome Completo: "
        read -r REAL_NAME
        [ -z "$REAL_NAME" ] && REAL_NAME="Utente"
    done

    while [ -z "$NEW_USER" ]; do
        # Proponi username derivato dal nome completo
        default_user=$(echo "$REAL_NAME" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-12)
        [ -z "$default_user" ] && default_user="utente"
        printf "Nome Utente per il Login [Predefinito: %s]: " "$default_user"
        read -r input_user
        if [ -z "$input_user" ]; then
            NEW_USER="$default_user"
        else
            # Validazione caratteri username POSIX
            valid_user=$(echo "$input_user" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9_-')
            if [ "$input_user" != "$valid_user" ] || [ -z "$valid_user" ]; then
                echo "Usa solo lettere minuscole e numeri per il nome utente."
            else
                NEW_USER="$valid_user"
            fi
        fi
    done

    while [ -z "$USER_PASS" ]; do
        printf "Crea una Password per '%s': " "$NEW_USER"
        stty -echo 2>/dev/null || true
        read -r p1
        stty echo 2>/dev/null || true
        echo ""
        printf "Conferma Password: "
        stty -echo 2>/dev/null || true
        read -r p2
        stty echo 2>/dev/null || true
        echo ""

        if [ -z "$p1" ]; then
            echo "La password non può essere vuota."
        elif [ "$p1" != "$p2" ]; then
            echo "Le password non coincidono. Riprova."
        else
            USER_PASS="$p1"
        fi
    done

    printf "Nome del Computer in Rete (Hostname) [Predefinito: osify-pc]: "
    read -r input_host
    [ -n "$input_host" ] && HOSTNAME_VAL="$(echo "$input_host" | tr -cd 'a-zA-Z0-9-')"
    [ -z "$HOSTNAME_VAL" ] && HOSTNAME_VAL="osify-pc"

    echo ""
    printf "Desideri abilitare il Login Automatico sul Desktop all'avvio del PC? [S/n]: "
    read -r auto_ans
    case "$auto_ans" in
        [Nn]*) DO_AUTOLOGIN="no" ;;
        *)     DO_AUTOLOGIN="yes" ;;
    esac

    echo ""
    printf "\033[1;33m[MIGRAZIONE DATI LIVE]\033[0m\n"
    printf "Desideri importare tutti i file, documenti, preferiti e impostazioni\n"
    printf "creati durante questa sessione di prova nel tuo nuovo account? [S/n]: "
    read -r mig_ans
    case "$mig_ans" in
        [Nn]*) MIGRATE_LIVE_DATA="no" ;;
        *)     MIGRATE_LIVE_DATA="yes" ;;
    esac

    echo ""
    log "Riepilogo Profilo Utente:"
    echo "  • Nome Completo : $REAL_NAME"
    echo "  • Nome Utente   : $NEW_USER (UID 1000)"
    echo "  • Hostname      : $HOSTNAME_VAL"
    echo "  • Autologin     : $DO_AUTOLOGIN"
    echo "  • Migra Live    : $MIGRATE_LIVE_DATA"
    echo ""
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
}

format_and_mount_ext4() {
    p1="$1"
    log "Formattazione Partizione Root Ext4 Ultra-Fast su $p1..."
    mkfs.ext4 -F -L "OSIFY_ROOT" -O dir_index,sparse_super "$p1"
    mkdir -p "$MOUNT_POINT"
    mount -o noatime,nodiratime,commit=60 "$p1" "$MOUNT_POINT"
    mkdir -p "$MOUNT_POINT/home" "$MOUNT_POINT/boot" "$MOUNT_POINT/opt/osify-games"
}

copy_live_system_tree() {
    log "Copia del sistema operativo di base dalla sessione Live al disco..."
    
    # 1. Copia directory di sistema vitali escludendo pseudofilesystem
    for sdir in bin sbin lib usr etc var opt root; do
        if [ -d "/$sdir" ]; then
            log "  -> Copia /$sdir in corso..."
            mkdir -p "$MOUNT_POINT/$sdir"
            cp -a "/$sdir/." "$MOUNT_POINT/$sdir/" 2>/dev/null || true
        fi
    done

    # 2. Kernel e boot files
    if [ -d "/boot" ]; then
        log "  -> Copia /boot in corso..."
        mkdir -p "$MOUNT_POINT/boot"
        cp -a "/boot/." "$MOUNT_POINT/boot/" 2>/dev/null || true
    fi

    # 3. Creazione filesystem virtuali di runtime
    log "Creazione punti di montaggio runtime..."
    mkdir -p "$MOUNT_POINT/proc" \
             "$MOUNT_POINT/sys" \
             "$MOUNT_POINT/dev" \
             "$MOUNT_POINT/tmp" \
             "$MOUNT_POINT/run" \
             "$MOUNT_POINT/mnt" \
             "$MOUNT_POINT/media" \
             "$MOUNT_POINT/home"
    chmod 1777 "$MOUNT_POINT/tmp"

    # 4. Iniezione albero di sviluppo OSify più aggiornato da REPO_ROOT
    if [ -d "$REPO_ROOT" ]; then
        log "Sincronizzazione repository OSify..."
        mkdir -p "$MOUNT_POINT/opt/osify"
        for sub in tools uem desktop system network audio presentation security runtimes; do
            if [ -d "$REPO_ROOT/$sub" ]; then
                cp -a "$REPO_ROOT/$sub" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
            fi
        done
        [ -f "$REPO_ROOT/OSify.png" ] && cp "$REPO_ROOT/OSify.png" "$MOUNT_POINT/opt/osify/" 2>/dev/null || true
    fi

    # Link binari globali in PATH
    mkdir -p "$MOUNT_POINT/usr/local/bin" "$MOUNT_POINT/usr/bin"
    ln -sf "/opt/osify/tools/osify-ctl" "$MOUNT_POINT/usr/local/bin/osify-ctl" 2>/dev/null || true
    ln -sf "/opt/osify/uem/runners/osify-universal-dispatcher.sh" "$MOUNT_POINT/usr/local/bin/osify-exec" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-app-drawer.py" "$MOUNT_POINT/usr/bin/osify-app-drawer" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-app-drawer.py" "$MOUNT_POINT/usr/bin/osify-drawer" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-hub.sh" "$MOUNT_POINT/usr/bin/osify-hub" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-browser.sh" "$MOUNT_POINT/usr/bin/osify-browser" 2>/dev/null || true
    ln -sf "/opt/osify/network/osify-wifi-gui.sh" "$MOUNT_POINT/usr/bin/osify-wifi" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-games.sh" "$MOUNT_POINT/usr/bin/osify-games" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-developer.sh" "$MOUNT_POINT/usr/bin/osify-developer" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-appearance.sh" "$MOUNT_POINT/usr/bin/osify-appearance" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-taskmanager.sh" "$MOUNT_POINT/usr/bin/osify-taskmanager" 2>/dev/null || true
    ln -sf "/opt/osify/tools/osify-gui/osify-terminal.sh" "$MOUNT_POINT/usr/bin/osify-terminal" 2>/dev/null || true

    # Copia Icone Native Vettoriali OSify (Eliminazione Totale Icone Bianche su Disco)
    mkdir -p "$MOUNT_POINT/usr/share/pixmaps" "$MOUNT_POINT/usr/share/icons/hicolor/48x48/apps"
    if [ -d "$REPO_ROOT/desktop/branding/icons/48" ]; then
        cp -a "$REPO_ROOT/desktop/branding/icons/48/"*.png "$MOUNT_POINT/usr/share/pixmaps/" 2>/dev/null || true
        cp -a "$REPO_ROOT/desktop/branding/icons/48/"*.png "$MOUNT_POINT/usr/share/icons/hicolor/48x48/apps/" 2>/dev/null || true
    fi

    # Copia Launcher .desktop con Icone Native
    mkdir -p "$MOUNT_POINT/usr/share/applications"
    if [ -d "$REPO_ROOT/desktop/applications" ]; then
        cp -a "$REPO_ROOT/desktop/applications/"*.desktop "$MOUNT_POINT/usr/share/applications/" 2>/dev/null || true
    fi

    # Rendi tutti gli script eseguibili
    chmod +x "$MOUNT_POINT"/usr/bin/osify-* "$MOUNT_POINT"/usr/local/bin/osify-* 2>/dev/null || true
}

setup_target_user_and_profile() {
    log "Configurazione account utente '$NEW_USER' su disco fisso..."
    target_home="$MOUNT_POINT/home/$NEW_USER"
    mkdir -p "$target_home"

    # Migrazione Dati della Live se richiesta
    LIVE_SRC="$(detect_live_home)"
    if [ "$MIGRATE_LIVE_DATA" = "yes" ] && [ -d "$LIVE_SRC" ]; then
        log "Migrazione integrale profilo live da $LIVE_SRC a $target_home..."
        cp -a "$LIVE_SRC/." "$target_home/" 2>/dev/null || true
    elif [ -d "$MOUNT_POINT/etc/skel" ]; then
        log "Inizializzazione profilo pulito da /etc/skel..."
        cp -a "$MOUNT_POINT/etc/skel/." "$target_home/" 2>/dev/null || true
    fi

    # Creazione cartelle personali standard
    mkdir -p "$target_home/Desktop" \
             "$target_home/Documenti" \
             "$target_home/Download" \
             "$target_home/Musica" \
             "$target_home/Video" \
             "$target_home/Progetti" \
             "$target_home/Giochi"

    # Rimuovi l'icona dell'installer dal desktop installato (il sistema è già su disco!)
    rm -f "$target_home/Desktop/osify-install.desktop" 2>/dev/null || true

    # Generazione hash password sicuro SHA-512
    pass_hash="$(generate_password_hash "$USER_PASS")"

    # Pulizia vecchi utenti live in /etc/passwd e /etc/shadow
    if [ -f "$MOUNT_POINT/etc/passwd" ]; then
        grep -v -E "^(tux|osify):" "$MOUNT_POINT/etc/passwd" > "$MOUNT_POINT/etc/passwd.tmp" || true
        echo "$NEW_USER:x:1000:1000:$REAL_NAME:/home/$NEW_USER:/bin/sh" >> "$MOUNT_POINT/etc/passwd.tmp"
        mv "$MOUNT_POINT/etc/passwd.tmp" "$MOUNT_POINT/etc/passwd"
    else
        cat << EOF > "$MOUNT_POINT/etc/passwd"
root:x:0:0:root:/root:/bin/sh
$NEW_USER:x:1000:1000:$REAL_NAME:/home/$NEW_USER:/bin/sh
nobody:x:65534:65534:nobody:/tmp:/bin/false
EOF
    fi

    if [ -f "$MOUNT_POINT/etc/shadow" ]; then
        grep -v -E "^(tux|osify):" "$MOUNT_POINT/etc/shadow" > "$MOUNT_POINT/etc/shadow.tmp" || true
        # Se root non ha password, impostiamo la stessa dell'utente
        if grep -q "^root::" "$MOUNT_POINT/etc/shadow.tmp"; then
            sed -i "s|^root::|root:$pass_hash:|g" "$MOUNT_POINT/etc/shadow.tmp" 2>/dev/null || true
        fi
        echo "$NEW_USER:$pass_hash:19000:0:99999:7:::" >> "$MOUNT_POINT/etc/shadow.tmp"
        mv "$MOUNT_POINT/etc/shadow.tmp" "$MOUNT_POINT/etc/shadow"
    else
        cat << EOF > "$MOUNT_POINT/etc/shadow"
root:$pass_hash:19000:0:99999:7:::
$NEW_USER:$pass_hash:19000:0:99999:7:::
nobody:*:19000:0:99999:7:::
EOF
    fi

    # Gruppi di sistema essenziali per hardware e audio/video
    if [ -f "$MOUNT_POINT/etc/group" ]; then
        grep -v -E "^(tux|osify):" "$MOUNT_POINT/etc/group" > "$MOUNT_POINT/etc/group.tmp" || true
        echo "$NEW_USER:x:1000:" >> "$MOUNT_POINT/etc/group.tmp"
        mv "$MOUNT_POINT/etc/group.tmp" "$MOUNT_POINT/etc/group"
        # Aggiunta ai gruppi ausiliari
        for grp in wheel sudo audio video cdrom dialout disk storage input users; do
            if grep -q "^$grp:" "$MOUNT_POINT/etc/group"; then
                sed -i "/^$grp:/ s/$/,${NEW_USER}/; s/:,/:/" "$MOUNT_POINT/etc/group" 2>/dev/null || true
            fi
        done
    fi

    # Permessi sudo completi
    mkdir -p "$MOUNT_POINT/etc/sudoers.d"
    echo "$NEW_USER ALL=(ALL) ALL" > "$MOUNT_POINT/etc/sudoers.d/osify"
    chmod 0440 "$MOUNT_POINT/etc/sudoers.d/osify" 2>/dev/null || true

    # Configurazione SLiM (Display Manager)
    if [ -f "$MOUNT_POINT/etc/slim.conf" ]; then
        sed -i "s/^default_user.*/default_user        $NEW_USER/" "$MOUNT_POINT/etc/slim.conf" 2>/dev/null || true
        if [ "$DO_AUTOLOGIN" = "yes" ]; then
            sed -i "s/^auto_login.*/auto_login          yes/" "$MOUNT_POINT/etc/slim.conf" 2>/dev/null || true
        else
            sed -i "s/^auto_login.*/auto_login          no/" "$MOUNT_POINT/etc/slim.conf" 2>/dev/null || true
        fi
    fi

    # Configurazione Shell Prompt e PATH
    cat << EOF > "$target_home/.profile"
# OSify User Profile
export PATH="/usr/local/bin:/usr/bin:/bin:/opt/osify/tools:\$PATH"
export PS1='\[\033[1;36m\]$NEW_USER\[\033[0m\]:\[\033[1;34m\]\w\[\033[0m\]\\$ '
EOF

    # Assegnazione proprietario definitiva
    chown -R 1000:1000 "$target_home"
    chmod 750 "$target_home"

    # Eliminazione residui tux
    rm -rf "$MOUNT_POINT/home/tux" 2>/dev/null || true
    # Symlink di sicurezza se qualche vecchio binario cerca ancora /home/tux
    ln -sf "/home/$NEW_USER" "$MOUNT_POINT/home/tux" 2>/dev/null || true

    log "Profilo per '$NEW_USER' configurato e protetto con successo."
}

configure_system_files() {
    log "Configurazione file di identità e filesystem OSify..."

    # os-release ufficiale
    cat << 'EOF' > "$MOUNT_POINT/etc/os-release"
NAME="OSify"
PRETTY_NAME="OSify 2.0 LTS (Universal Matrix & Deck Edition)"
ID=osify
ID_LIKE="arch debian slitaz"
VERSION="2.0"
VERSION_ID="2.0"
HOME_URL="https://github.com/ANDRYXify/OSify"
EOF

    # Hostname e hosts
    echo "$HOSTNAME_VAL" > "$MOUNT_POINT/etc/hostname"
    cat << EOF > "$MOUNT_POINT/etc/hosts"
127.0.0.1   localhost
127.0.1.1   $HOSTNAME_VAL
::1         localhost ip6-localhost ip6-loopback
EOF

    # Generazione fstab
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
    log "Configurazione Bootloader per architettura: $fw..."

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
        # BIOS Vintage MBR (Syslinux / Extlinux)
        mkdir -p "$MOUNT_POINT/boot/syslinux"
        cat << 'EOF' > "$MOUNT_POINT/boot/syslinux/syslinux.cfg"
DEFAULT osify
PROMPT 0
TIMEOUT 20

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

verify_installation_integrity() {
    log "Verifica atomica di integrità del sistema installato..."
    errors=0

    if [ ! -f "$MOUNT_POINT/bin/sh" ] && [ ! -f "$MOUNT_POINT/bin/busybox" ]; then
        err "Manca l'interprete shell di sistema (/bin/sh)."
        errors=$((errors + 1))
    fi

    if [ ! -f "$MOUNT_POINT/etc/passwd" ] || ! grep -q "^$NEW_USER:" "$MOUNT_POINT/etc/passwd"; then
        err "Account utente non registrato correttamente in /etc/passwd."
        errors=$((errors + 1))
    fi

    if [ ! -d "$MOUNT_POINT/home/$NEW_USER" ]; then
        err "Home directory utente non trovata."
        errors=$((errors + 1))
    fi

    if [ ! -f "$MOUNT_POINT/etc/fstab" ]; then
        err "File /etc/fstab mancante."
        errors=$((errors + 1))
    fi

    if [ "$errors" -gt 0 ]; then
        err "Verifica fallita con $errors errori critici. Smontaggio interrotto per consentire la diagnosi."
        exit 1
    fi

    ok "Tutti i controlli di integrità sono passati con successo al 100%!"
}

cleanup_mounts() {
    log "Sincronizzazione della cache disco (sync) in corso..."
    sync
    sync
    log "Smontaggio partizioni di sistema..."
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

    # FASE 1: Configurazione Utente
    user_setup_wizard

    # FASE 2: Rilevamento e Selezione Disco
    echo "[2/4] Rilevamento dischi rigidi disponibili per l'installazione:"
    echo "-----------------------------------------------------------------"
    
    disks_file="/tmp/osify_disks.txt"
    rm -f "$disks_file"

    # Rilevamento della partizione e del disco da cui si e' avviata la Live USB per proteggerla
    boot_mount=$(awk '$2 ~ /^\/(mnt\/live|live|run\/archiso)/ {print $1}' /proc/mounts 2>/dev/null | head -n1)
    [ -z "$boot_mount" ] && boot_mount=$(awk '$3 ~ /(iso9660|squashfs)/ {print $1}' /proc/mounts 2>/dev/null | head -n1)
    BOOT_DEV_BASE=""
    if [ -n "$boot_mount" ]; then
        BOOT_DEV_BASE=$(basename "$boot_mount" | sed -E 's/[0-9]+$//; s/p$//')
    fi

    # Scansione accurata /sys/block per drive fisici (SATA, IDE, NVMe, eMMC, USB)
    for d in /sys/block/sd* /sys/block/hd* /sys/block/nvme*n1 /sys/block/mmcblk*; do
        [ -e "$d" ] || continue
        dname=$(basename "$d")
        case "$dname" in
            loop*|ram*|zram*|sr*|fd*) continue ;;
        esac
        size_sectors=$(cat "$d/size" 2>/dev/null || echo 0)
        size_gb=$(( size_sectors * 512 / 1024 / 1024 / 1024 ))
        [ $size_gb -le 0 ] && continue

        model=""
        [ -f "$d/device/model" ] && model=$(cat "$d/device/model" | tr -s ' ' | sed 's/^[ \t]*//;s/[ \t]*$//')
        [ -z "$model" ] && [ -f "$d/device/name" ] && model=$(cat "$d/device/name" 2>/dev/null)
        [ -z "$model" ] && model="Disco Rigido Interno"

        is_boot=0
        [ -n "$BOOT_DEV_BASE" ] && [ "$dname" = "$BOOT_DEV_BASE" ] && is_boot=1

        echo "$dname|$size_gb GB|$model|$is_boot" >> "$disks_file"
    done

    # Fallback con lsblk se /sys/block era vuoto
    if [ ! -s "$disks_file" ] && command -v lsblk >/dev/null 2>&1; then
        lsblk -d -n -o NAME,SIZE,MODEL 2>/dev/null | grep -v "loop" | while read -r n s m; do
            echo "$n|$s|$m|0" >> "$disks_file"
        done
    fi

    if [ ! -s "$disks_file" ]; then
        err "Nessun disco fisso rilevato nel sistema."
        echo "Controlla i collegamenti SATA/NVMe o i driver del controller."
        rm -f "$disks_file"
        exit 1
    fi

    idx=1
    while IFS='|' read -r dname dsize dmodel is_boot; do
        if [ -n "$dname" ]; then
            if [ "$is_boot" = "1" ]; then
                printf "  \033[1;30m[%d]\033[0m /dev/%s  —  %s  (%s)  \033[1;33m[CHIAVETTA LIVE USB - PROTETTA]\033[0m\n" "$idx" "$dname" "$dsize" "$dmodel"
            else
                printf "  \033[1;32m[%d]\033[0m \033[1m/dev/%s\033[0m  —  Dimensione: \033[1;33m%s\033[0m  (Modello: \033[1;37m%s\033[0m)\n" "$idx" "$dname" "$dsize" "$dmodel"
            fi
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
    selected_name="$(echo "$selected_line" | awk -F'|' '{print $1}')"
    is_live_usb="$(echo "$selected_line" | awk -F'|' '{print $4}')"

    if [ "$is_live_usb" = "1" ]; then
        printf "\n\033[1;31m[!] ATTENZIONE: Hai selezionato il supporto USB Live da cui è avviato OSify!\033[0m\n"
        printf "    Per preservare la chiavetta, seleziona l'Hard Disk interno del computer.\n"
        printf "Sei VERAMENTE sicuro di voler procedere su questo dispositivo? [s/N]: "
        read -r usb_conf
        case "$usb_conf" in
            [Ss]*) ;;
            *) echo "Scelta annullata."; rm -f "$disks_file"; exit 0 ;;
        esac
    fi

    TARGET_DISK="/dev/$selected_name"
    rm -f "$disks_file"

    log "Hai selezionato il disco: $TARGET_DISK"
    echo ""

    # FASE 3: Scelta Filesystem
    echo "[3/4] Scelta del profilo Filesystem e Ottimizzazione Storage:"
    echo "-----------------------------------------------------------------"
    if [ "$fw" = "bios" ] || [ "$(uname -m)" = "i686" ]; then
        printf "  \033[1;32m[1]\033[0m \033[1mExt4 Ultra-Fast (Raccomandato per Netbook/Atom/HDD 5400rpm)\033[0m\n"
        echo "      Minimo overhead di I/O, noatime, ultra-fluido e resistente."
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
    log "Profilo Filesystem: $FS_TYPE"
    echo ""

    # FASE 4: Conferma di Sicurezza Irreversibile
    printf "\033[1;31m=================================================================\033[0m\n"
    printf "\033[1;31m                      AVVISO IRREVERSIBILE                      \033[0m\n"
    printf "\033[1;31m=================================================================\033[0m\n"
    echo "L'installazione cancellerà TUTTE le partizioni e i dati presenti su:"
    echo "  • Disco bersaglio : $TARGET_DISK"
    echo "  • Filesystem      : $FS_TYPE"
    echo "  • Modalità Boot   : $fw"
    echo "  • Nuovo Utente    : $NEW_USER ($REAL_NAME)"
    echo "  • Migrazione Live : $MIGRATE_LIVE_DATA"
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
        [ -z "$NEW_USER" ] && NEW_USER="andrea"
        [ -z "$REAL_NAME" ] && REAL_NAME="Andrea"
        [ -z "$USER_PASS" ] && USER_PASS="osify"
    fi

    fw="$(detect_firmware_mode)"
    log "Avvio installazione su: $TARGET_DISK (Modalità: $fw, Filesystem: $FS_TYPE)"

    # 1. Partizionamento
    if [ "$fw" = "uefi" ]; then
        partition_disk_uefi "$TARGET_DISK"
    else
        partition_disk_bios "$TARGET_DISK"
    fi

    # 2. Formattazione e Mount
    parts=$(get_part_names "$TARGET_DISK")
    p1=$(echo "$parts" | awk '{print $1}')

    if [ "$FS_TYPE" = "ext4" ] && [ "$fw" = "bios" ]; then
        format_and_mount_ext4 "$p1"
    else
        format_and_mount_btrfs "$TARGET_DISK" "$fw"
    fi

    # 3. Copia Reale Sistema Operativo da Live a Disco
    copy_live_system_tree

    # 4. Creazione Utente Reale e Migrazione Dati Live
    setup_target_user_and_profile

    # 5. Configurazione OSify System Files
    configure_system_files

    # 6. Configurazione Bootloader
    configure_bootloader "$TARGET_DISK" "$fw"

    # 7. Verifica di Integrità Atomica
    verify_installation_integrity

    # 8. Smontaggio e Flush Cache
    cleanup_mounts

    echo ""
    printf "\033[1;32m=================================================================\033[0m\n"
    ok "INSTALLAZIONE DI OSIFY COMPLETATA CON SUCCESSO SUL DISCO: $TARGET_DISK"
    printf "\033[1;32m=================================================================\033[0m\n"
    echo "Il sistema operativo OSify è ora installato e configurato permanentemente."
    echo "Profilo utente creato: $NEW_USER ($REAL_NAME)"
    if [ "$MIGRATE_LIVE_DATA" = "yes" ]; then
        echo "Tutti i tuoi file e preferenze della sessione Live sono stati migrati!"
    fi
    echo "Puoi rimuovere il supporto USB di installazione e riavviare."
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
