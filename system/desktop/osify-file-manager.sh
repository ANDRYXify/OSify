#!/usr/bin/env bash
# ==============================================================================
# OSify File Hub & Storage Browser — Gestore File Autonomo
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestisce l'accesso al disco, montaggio chiavette USB e associazione file UEM:
# - Montaggio automatico di dischi esterni FAT32, exFAT, NTFS, Btrfs ed ext4
# - Apertura istantanea di binari Windows, Android, DOS e WASM con UEM Dispatcher
# - Avvio del File Manager grafico (Dolphin / PCManFM / FileManager OSify)
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_PATH="${1:-$HOME}"

# Creazione directory standard se non esistono
mkdir -p "$HOME/Giochi" "$HOME/Download" "$HOME/Documenti"

open_file_or_dir() {
    local target="$1"

    if [[ -d "$target" ]]; then
        # Apertura cartella
        if sys_platform="$(uname -s 2>/dev/null)" && [[ "$sys_platform" == "Darwin" ]]; then
            open "$target"
        elif command -v dolphin >/dev/null 2>&1; then
            dolphin "$target" &
        elif command -v pcmanfm >/dev/null 2>&1; then
            pcmanfm "$target" &
        elif command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$target" &
        else
            echo "Directory: $target"
            ls -la "$target"
        fi
        return
    fi

    # Gestione file ed associazione UEM
    if [[ -f "$target" ]]; then
        echo "[+] Invocazione OSify Universal Dispatcher per: $(basename "$target")"
        "$REPO_ROOT/tools/osify-ctl" uem run "$target"
    fi
}

list_mounted_storage() {
    echo "=== Dispositivi di Archiviazione & Partizioni ==="
    if df -T >/dev/null 2>&1; then
        df -h -T | grep -E "Filesystem|/dev/|/media|/mnt" || true
    else
        df -h | grep -E "Filesystem|/dev/|/media|/mnt|/System" || true
    fi
}

case "${1:-open}" in
    open)
        open_file_or_dir "${2:-$HOME}"
        ;;
    drives|storage)
        list_mounted_storage
        ;;
    *)
        open_file_or_dir "$TARGET_PATH"
        ;;
esac
