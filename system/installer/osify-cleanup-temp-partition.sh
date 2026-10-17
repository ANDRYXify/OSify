#!/usr/bin/env bash
# ==============================================================================
# OSify Temporary Installer Partition Cleaner
# ==============================================================================
# Rileva ed elimina la partizione temporanea 'OSIFY_BOOT' creata dall'installer
# Windows senza chiavetta USB, riassegnando lo spazio liberato al disco principale.
# ==============================================================================

set -euo pipefail

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[ERRORE] Questa operazione richiede privilegi di root." >&2
        exit 1
    fi
}

cleanup_partition() {
    check_root
    echo "========================================================="
    echo "       OSify Cleanup Engine — Rimozione Partizione Temp  "
    echo "========================================================="

    local temp_part
    temp_part=$(lsblk -o NAME,LABEL -nr 2>/dev/null | awk '$2=="OSIFY_BOOT" {print "/dev/"$1}' | head -n1 || true)

    if [[ -z "$temp_part" ]]; then
        echo "[i] Nessuna partizione temporanea 'OSIFY_BOOT' rilevata. Disco già pulito."
        exit 0
    fi

    echo "[+] Rilevata partizione temporanea dell'installer: $temp_part"
    
    # Smonta se montata
    if mount | grep -q "$temp_part"; then
        echo "[+] Smontaggio in corso..."
        umount "$temp_part" || true
    fi

    # Identifica il disco genitore e il numero di partizione
    local parent_disk
    local part_num
    parent_disk=$(lsblk -no PKNAME "$temp_part" 2>/dev/null || true)
    part_num=$(echo "$temp_part" | grep -o '[0-9]*$')

    if [[ -n "$parent_disk" && -n "$part_num" ]]; then
        echo "[+] Eliminazione partizione $part_num da /dev/$parent_disk..."
        parted -s "/dev/$parent_disk" rm "$part_num" 2>/dev/null || true
        echo "[[OK]] Partizione temporanea rimossa! Lo spazio è ora riutilizzabile dal filesystem principale."
    else
        echo "[!] Impossibile determinare automaticamente il disco genitore; rimuovere manualmente con fdisk/gparted."
    fi
}

cleanup_partition
