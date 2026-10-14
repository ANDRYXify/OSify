#!/bin/sh
# ==============================================================================
# OSify Intelligent Automounter — Montaggio Istantaneo USB, SD & Hard Disk Esterni
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta filesystem multipli: FAT32, exFAT, NTFS, EXT2/3/4, BTRFS, XFS, ISO9660.
# Monta automaticamente i supporti rimovibili in /media/<LABEL> con permessi utente
# e applica in tempo reale il tuning anti-freeze di OSify Storage Governor.
# ==============================================================================

MEDIA_BASE="/media"
POLL_INTERVAL=2

# Auto-elevazione root necessaria per montare dischi
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    fi
fi

log() { printf "\033[1;36m[OSify-Automount]\033[0m %s\n" "$*"; }

# 1. Rileva se una partizione è montata
is_mounted() {
    _part="$1"
    grep -q "^$_part " /proc/mounts 2>/dev/null
}

# 2. Ottiene l'etichetta del volume o genera un nome amichevole
get_mount_label() {
    _part="$1"
    _pname=$(basename "$_part")
    
    # Prova blkid
    if command -v blkid >/dev/null 2>&1; then
        lbl=$(blkid -s LABEL -o value "$_part" 2>/dev/null || echo "")
        [ -n "$lbl" ] && echo "$lbl" | tr ' /' '_-' && return
    fi
    
    # Se è una scheda SD
    case "$_pname" in
        mmcblk*) echo "Scheda_SD_${_pname}" ; return ;;
    esac
    
    # Se è una chiavetta USB
    echo "USB_${_pname}"
}

# 3. Montaggio deterministico partizione
mount_partition() {
    _part="$1"
    [ -b "$_part" ] || return
    
    # Non montare partizioni di sistema interne o swap o EFI
    _parent=$(echo "$_part" | sed 's/[0-9]*$//;s/p$//')
    case "$_part" in
        /dev/loop*|/dev/ram*|/dev/zram*) return ;;
    esac

    # Se già montato, ignora
    is_mounted "$_part" && return

    # Rileva filesystem
    fstype=""
    if command -v blkid >/dev/null 2>&1; then
        fstype=$(blkid -s TYPE -o value "$_part" 2>/dev/null || echo "")
    fi
    case "$fstype" in
        swap) return ;; # Ignora partizioni swap
    esac

    label=$(get_mount_label "$_part")
    target_dir="$MEDIA_BASE/$label"
    
    # Se la directory esiste ed è occupata, aggiungi suffisso numerico
    if [ -d "$target_dir" ] && grep -q " $target_dir " /proc/mounts 2>/dev/null; then
        target_dir="${target_dir}_$$"
    fi
    mkdir -p "$target_dir"

    log "Montaggio partizione $_part ($fstype) in $target_dir..."

    mounted=0
    # Opzioni di montaggio sicure con permessi per l'utente desktop
    case "$fstype" in
        vfat|fat|msdos)
            mount -t vfat -o rw,uid=1000,gid=1000,umask=000,utf8,flush "$_part" "$target_dir" 2>/dev/null && mounted=1
            ;;
        ntfs)
            if command -v ntfs-3g >/dev/null 2>&1; then
                ntfs-3g -o rw,uid=1000,gid=1000,umask=000 "$_part" "$target_dir" 2>/dev/null && mounted=1
            else
                mount -t ntfs -o rw,uid=1000,gid=1000,umask=000 "$_part" "$target_dir" 2>/dev/null && mounted=1 || mount "$_part" "$target_dir" 2>/dev/null && mounted=1
            fi
            ;;
        exfat)
            mount -t exfat -o rw,uid=1000,gid=1000,umask=000 "$_part" "$target_dir" 2>/dev/null && mounted=1 || mount "$_part" "$target_dir" 2>/dev/null && mounted=1
            ;;
        ext2|ext3|ext4|btrfs|xfs)
            mount -o rw "$_part" "$target_dir" 2>/dev/null && mounted=1
            chmod 777 "$target_dir" 2>/dev/null || true
            ;;
        iso9660|udf)
            mount -t "$fstype" -o ro,uid=1000,gid=1000 "$_part" "$target_dir" 2>/dev/null && mounted=1
            ;;
        *)
            mount "$_part" "$target_dir" 2>/dev/null && mounted=1
            ;;
    esac

    if [ "$mounted" -eq 1 ]; then
        log "[OK] $_part montato con successo in $target_dir"
        
        # Applica tuning anti-freeze su device parent
        pdev=$(basename "$_parent")
        if [ -x /usr/bin/osify-storage-governor ]; then
            /usr/bin/osify-storage-governor "$pdev" >/dev/null 2>&1 &
        fi
        
        # Notifica desktop visiva
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --notification --image="/usr/share/pixmaps/osify-hub.png" \
                --text="Dispositivo collegato: $label in $target_dir" \
                --command="pcmanfm '$target_dir'" 2>/dev/null || true
        fi
    else
        rmdir "$target_dir" 2>/dev/null || true
    fi
}

# 4. Scansione di tutte le partizioni rimovibili
scan_and_mount() {
    for p in /dev/sd[b-z][0-9]* /dev/mmcblk[0-9]*p[0-9]*; do
        [ -b "$p" ] || continue
        mount_partition "$p"
    done
}

# 5. Pulizia cartelle mount point orfane in /media
clean_orphaned_mounts() {
    for d in "$MEDIA_BASE"/*; do
        [ -d "$d" ] || continue
        if ! grep -q " $d " /proc/mounts 2>/dev/null; then
            # Non eliminare cartelle occupate da file
            rmdir "$d" 2>/dev/null || true
        fi
    done
}

# ==============================================================================
# MODALITÀ DI ESECUZIONE
# ==============================================================================
case "${1:-scan}" in
    scan|--scan|-s)
        mkdir -p "$MEDIA_BASE"
        scan_and_mount
        clean_orphaned_mounts
        ;;
    daemon|--daemon|-d)
        log "Avvio demone OSify Automount in background..."
        mkdir -p "$MEDIA_BASE"
        while true; do
            scan_and_mount
            clean_orphaned_mounts
            sleep "$POLL_INTERVAL"
        done
        ;;
    *)
        if [ -b "$1" ]; then
            mount_partition "$1"
        else
            echo "Uso: $0 [scan|daemon|<dispositivo-partizione>]"
            exit 1
        fi
        ;;
esac
