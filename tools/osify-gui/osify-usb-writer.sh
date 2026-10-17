#!/usr/bin/env bash
# ==============================================================================
# OSify USB Image Writer — Scrittore Immagini ISO su Chiavette USB
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Scrive immagini ISO/IMG su pendrive USB con protezione dischi interni e sync finale.
# ==============================================================================

set -euo pipefail

get_usb_drives() {
    for dev in /sys/block/sd*; do
        [ -e "$dev" ] || continue
        local dname
        dname="$(basename "$dev")"
        # Verifica se rimovibile
        local rem
        rem="$(cat "$dev/removable" 2>/dev/null || echo "0")"
        if [ "$rem" = "1" ]; then
            local model
            model="$(cat "$dev/device/model" 2>/dev/null | tr -s ' ' || echo "USB Drive")"
            local size
            size="$(cat "$dev/size" 2>/dev/null || echo 0)"
            local size_gb=$(( size * 512 / 1024 / 1024 / 1024 ))
            echo "/dev/$dname (${size_gb} GB - $model)"
        fi
    done
}

write_iso() {
    local iso="$1"
    local target_dev="$2"

    if [ ! -f "$iso" ]; then
        echo "[!] Immagine ISO non trovata: $iso"
        return 1
    fi

    if [ ! -b "$target_dev" ]; then
        echo "[!] Dispositivo USB non valido: $target_dev"
        return 1
    fi

    echo "[*] Smontaggio partizioni attive su $target_dev..."
    sudo umount "${target_dev}"* 2>/dev/null || true

    echo "[+] Scrittura di $(basename "$iso") su $target_dev in corso..."
    sudo dd if="$iso" of="$target_dev" bs=4M status=progress conv=fdatasync
    sync
    echo "[[OK]] Scrittura completata con successo! La chiavetta USB e' ora avviabile."
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local iso
        iso="$(yad --file-selection --title="Seleziona Immagine ISO da Scrivere" \
            --file-filter="Immagini Disco (*.iso, *.img)|*.iso *.img" \
            --window-icon="/usr/share/pixmaps/osify-install.png" \
            --width=520 --center 2>/dev/null || echo "")"
        
        [ -z "$iso" ] && return 0

        local usb_list
        usb_list="$(get_usb_drives)"

        if [ -z "$usb_list" ]; then
            yad --error --title="Nessuna Chiavetta Rilevata" \
                --text="Inserisci una chiavetta USB e riprova." --center || true
            return 1
        fi

        local sel_usb
        sel_usb="$(yad --list --title="Seleziona Chiavetta USB di Destinazione" \
            --text="<b>ATTENZIONE:</b> I dati sulla chiavetta selezionata verranno sovrascritti!\nImmagine: <i>$(basename "$iso")</i>" \
            --window-icon="/usr/share/pixmaps/osify-install.png" \
            --width=480 --height=220 --center \
            --column="Dispositivo USB" $usb_list \
            --button="Scrivi Immagine:0" --button="Annulla:1" 2>/dev/null || echo "")"
        
        [ -z "$sel_usb" ] && return 0
        local dev_path
        dev_path="$(echo "$sel_usb" | cut -d' ' -f1 | cut -d'|' -f1)"

        if [ -b "$dev_path" ]; then
            if command -v terminal >/dev/null 2>&1; then
                terminal -geometry 75x15 -T "Scrittura ISO su USB" -e sudo "$0" --write "$iso" "$dev_path"
            else
                write_iso "$iso" "$dev_path"
            fi
        fi
    else
        echo "Uso: $0 --write <file.iso> <dispositivo_usb>"
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    --write) write_iso "${2:-}" "${3:-}" ;;
    *) echo "Uso: $0 {gui|--write <iso> <dev>}" ;;
esac
