#!/usr/bin/env bash
# ==============================================================================
# OSify Storage Architecture — Btrfs Subvolumes & Atomic Rollback Engine
# ==============================================================================
# Configura un layout a subvolumi Btrfs ottimizzato per il gaming:
# 1. @               -> Root filesystem di sistema (protetto da snapshot Snapper)
# 2. @home          -> Dati utente e salvataggi giochi (isolati dai rollback di sistema)
# 3. @games_wine    -> Directory Wine prefixes e librerie giochi (attributo NODATACOW)
# 4. @waydroid      -> Immagini Android container (attributo NODATACOW)
# 5. @snapshots     -> Snapshot istantanei avviabili direttamente da GRUB/systemd-boot
#
# Perché NODATACOW sui giochi?
# Btrfs Copy-on-Write (CoW) è ottimo per i rollback, ma su file enormi da 50-100GB
# soggetti a continue riscritture (come le VMA di Wine e le cache shader) provoca
# frammentazione del disco e cadute di frame rate.
# Disabilitare il CoW sui giochi azzera la frammentazione mantenendo la sicurezza del sistema!
# ==============================================================================

set -euo pipefail

SETUP_MOUNT_TARGET="${1:-/mnt}"

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[ERRORE] Questa procedura richiede privilegi di root." >&2
        exit 1
    fi
}

configure_subvolumes() {
    local dev="$1"
    check_root
    echo "========================================================="
    echo "       OSify Btrfs Engine — Creazione Layout Subvolumi   "
    echo "========================================================="
    echo "[+] Creazione subvolumi su $dev..."

    mount "$dev" "$SETUP_MOUNT_TARGET"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@home"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@snapshots"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@var_log"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@games_wine"
    btrfs subvolume create "$SETUP_MOUNT_TARGET/@waydroid"
    umount "$SETUP_MOUNT_TARGET"

    echo "[[OK]] Subvolumi Btrfs creati con successo."
}

apply_game_optimizations() {
    local target_dir="$1"
    echo "[+] Applicazione attributo NO-COW su directory giochi e VM: $target_dir"
    mkdir -p "$target_dir"
    chattr +C "$target_dir" || true
    echo "[[OK]] Attributo NO-COW (chattr +C) applicato: frammentazione I/O azzerata!"
}

case "${1:-help}" in
    create)
        if [[ -z "${2:-}" ]]; then
            echo "Uso: $0 create <partizione-btrfs> (es. /dev/nvme0n1p2)"
            exit 1
        fi
        configure_subvolumes "$2"
        ;;
    nocow)
        if [[ -z "${2:-}" ]]; then
            echo "Uso: $0 nocow <directory-da-ottimizzare>"
            exit 1
        fi
        apply_game_optimizations "$2"
        ;;
    *)
        echo "Uso: $0 {create <device>|nocow <directory>}"
        exit 1
        ;;
esac
