#!/usr/bin/env bash
# ==============================================================================
# OSify Archive Manager — Gestore Universale Archivi Compressi
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta: ZIP, TAR, GZ, BZ2, XZ, 7Z, ISO senza dipendenze complesse.
# ==============================================================================

set -euo pipefail

TARGET_ARCHIVE="${1:-}"

extract_archive() {
    local arch="$1"
    local dest_dir="${2:-}"
    
    if [ ! -f "$arch" ]; then
        echo "[!] Archivio non trovato: $arch"
        return 1
    fi

    local base_name
    base_name="$(basename "$arch")"
    local parent_dir
    parent_dir="$(dirname "$arch")"

    if [ -z "$dest_dir" ]; then
        # Cartella con nome dell'archivio (senza estensione)
        local raw_name="${base_name%.*}"
        raw_name="${raw_name%.tar}"
        dest_dir="${parent_dir}/${raw_name}"
    fi

    mkdir -p "$dest_dir"
    echo "[+] Estrazione di $base_name in $dest_dir..."

    case "$arch" in
        *.tar.gz|*.tgz)
            tar -xzf "$arch" -C "$dest_dir" ;;
        *.tar.xz|*.txz)
            tar -xJf "$arch" -C "$dest_dir" ;;
        *.tar.bz2|*.tbz2)
            tar -xjf "$arch" -C "$dest_dir" ;;
        *.tar)
            tar -xf "$arch" -C "$dest_dir" ;;
        *.zip)
            if command -v unzip >/dev/null 2>&1; then
                unzip -q -o "$arch" -d "$dest_dir"
            elif command -v 7z >/dev/null 2>&1; then
                7z x -y "-o${dest_dir}" "$arch" >/dev/null
            elif command -v python3 >/dev/null 2>&1; then
                python3 -c "import zipfile; zipfile.ZipFile('$arch').extractall('$dest_dir')"
            fi ;;
        *.7z)
            if command -v 7z >/dev/null 2>&1; then
                7z x -y "-o${dest_dir}" "$arch" >/dev/null
            fi ;;
        *)
            if command -v 7z >/dev/null 2>&1; then
                7z x -y "-o${dest_dir}" "$arch" >/dev/null
            else
                tar -xf "$arch" -C "$dest_dir" 2>/dev/null || true
            fi ;;
    esac

    echo "[[OK]] Estrazione completata: $dest_dir"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "OSify Archivi" "Archivio estratto in: $(basename "$dest_dir")" -i /usr/share/pixmaps/osify-files.png || true
    fi
}

create_archive() {
    local src="$1"
    local out_arch="${2:-}"
    
    if [ ! -e "$src" ]; then
        echo "[!] File o cartella non trovata: $src"
        return 1
    fi

    local base_src
    base_src="$(basename "$src")"
    local parent_src
    parent_src="$(dirname "$src")"

    if [ -z "$out_arch" ]; then
        out_arch="${parent_src}/${base_src}.zip"
    fi

    echo "[+] Compressione di $base_src in $out_arch..."
    case "$out_arch" in
        *.zip)
            if command -v zip >/dev/null 2>&1; then
                (cd "$parent_src" && zip -r -q "$out_arch" "$base_src")
            elif command -v python3 >/dev/null 2>&1; then
                python3 -c "import shutil, os; shutil.make_archive('${out_arch%.zip}', 'zip', '$parent_src', '$base_src')"
            fi ;;
        *.tar.gz|*.tgz)
            tar -czf "$out_arch" -C "$parent_src" "$base_src" ;;
        *.tar.xz)
            tar -cJf "$out_arch" -C "$parent_src" "$base_src" ;;
        *)
            tar -czf "$out_arch" -C "$parent_src" "$base_src" ;;
    esac

    echo "[[OK]] Archivio creato: $out_arch"
}

launch_gui() {
    local arch="${1:-}"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        if [ -n "$arch" ] && [ -f "$arch" ]; then
            local action
            action="$(yad --list --title="Gestore Archivi OSify" \
                --text="<b>Archivio:</b> $(basename "$arch")\nSeleziona l'azione desiderata:" \
                --window-icon="/usr/share/pixmaps/osify-files.png" \
                --width=420 --height=220 --center \
                --column="Azione" --column="Dettagli" \
                "Estrai in Nuova Cartella" "Estrai nella cartella dedicata col nome dell'archivio" \
                "Estrai Qui" "Estrai tutti i file direttamente nella cartella corrente" \
                --button="Estrai:0" --button="Annulla:1" 2>/dev/null || echo "")"
            
            local sel
            sel="$(echo "$action" | cut -d'|' -f1)"
            if [ "$sel" = "Estrai in Nuova Cartella" ]; then
                extract_archive "$arch" ""
            elif [ "$sel" = "Estrai Qui" ]; then
                extract_archive "$arch" "$(dirname "$arch")"
            fi
        else
            local choice
            choice="$(yad --form --title="Gestore Archivi OSify" \
                --text="<b>Compressione ed Estrazione File</b>" \
                --window-icon="/usr/share/pixmaps/osify-files.png" \
                --width=460 --center \
                --field="File/Cartella o Archivio:FL" "" \
                --field="Operazione:CB" "Estrai Archivio!Crea Archivio ZIP!Crea Archivio TAR.GZ" \
                --button="Procedi:0" --button="Annulla:1" 2>/dev/null || echo "")"
            
            local f_target op
            f_target="$(echo "$choice" | cut -d'|' -f1)"
            op="$(echo "$choice" | cut -d'|' -f2)"

            if [ -n "$f_target" ] && [ -e "$f_target" ]; then
                case "$op" in
                    *Estrai*) extract_archive "$f_target" "" ;;
                    *ZIP*) create_archive "$f_target" "${f_target}.zip" ;;
                    *TAR*) create_archive "$f_target" "${f_target}.tar.gz" ;;
                esac
            fi
        fi
    else
        if [ -n "$arch" ]; then
            extract_archive "$arch" ""
        else
            echo "Uso: $0 <file_archivio> [directory_destinazione]"
            echo "     $0 --create <origine> [archivio_destinazione]"
        fi
    fi
}

case "${1:-}" in
    --extract|-x)
        extract_archive "${2:-}" "${3:-}" ;;
    --create|-c)
        create_archive "${2:-}" "${3:-}" ;;
    "")
        launch_gui "" ;;
    *)
        if [ -f "$1" ]; then
            launch_gui "$1"
        else
            launch_gui ""
        fi ;;
esac
