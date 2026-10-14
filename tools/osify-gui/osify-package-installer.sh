#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Package & App Installer — Installatore Grafico Pacchetti
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestore universale a doppio click per file di installazione:
# - .tazpkg (SliTaz Native)
# - .deb (Debian/Ubuntu Archive)
# - .AppImage (Applicazioni portabili Linux)
# - .sh / .run / .bin (Script ed eseguibili)
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-install.png"
TARGET_FILE="${1:-}"

if [ -z "$TARGET_FILE" ]; then
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        TARGET_FILE="$(yad --file-selection \
            --title="OSify — Seleziona Pacchetto da Installare" \
            --file-filter="Tutti i Pacchetti (*.tazpkg, *.deb, *.AppImage)|*.tazpkg *.deb *.AppImage *.run *.bin" \
            --window-icon="$LOGO_IMG" --center 2>/dev/null || echo "")"
    fi
fi

if [ -z "$TARGET_FILE" ] || [ ! -f "$TARGET_FILE" ]; then
    echo "Uso: $0 <percorso-pacchetto>"
    exit 1
fi

EXT="${TARGET_FILE##*.}"
FNAME="$(basename "$TARGET_FILE")"
FSIZE="$(du -h "$TARGET_FILE" | awk '{print $1}')"

install_tazpkg() {
    local pkg="$1"
    if command -v tazpkg >/dev/null 2>&1; then
        (
            echo "10"; echo "# Inizializzazione installazione tazpkg..."
            if [ "$(id -u)" -eq 0 ]; then
                tazpkg install "$pkg" --forced 2>&1
            else
                sudo tazpkg install "$pkg" --forced 2>&1
            fi
            echo "100"; echo "# Installazione completata!"
        ) | yad --progress --title="Installazione $FNAME" --text="Installazione in corso..." --auto-close --center 2>/dev/null || true
    else
        # Fallback estrazione cpio
        local tmp_d="/tmp/osify_tazpkg_inst"
        mkdir -p "$tmp_d"
        (cd "$tmp_d" && cpio -idmv < "$pkg" >/dev/null 2>&1)
        if [ -f "$tmp_d/fs.cpio.lzma" ]; then
            python3 -c "import lzma, sys; sys.stdout.buffer.write(lzma.decompress(open('$tmp_d/fs.cpio.lzma', 'rb').read()))" > "$tmp_d/fs.cpio"
            (cd / && sudo cpio -idmv < "$tmp_d/fs.cpio" >/dev/null 2>&1)
        fi
        rm -rf "$tmp_d"
    fi
}

install_deb() {
    local deb="$1"
    (
        echo "20"; echo "# Estrazione pacchetto Debian..."
        local tmp_deb="/tmp/osify_deb_extract"
        mkdir -p "$tmp_deb"
        ar x "$deb" --output "$tmp_deb" 2>/dev/null || (cd "$tmp_deb" && 7z x "$deb" >/dev/null 2>&1)
        
        echo "60"; echo "# Integrazione filesystem..."
        if [ -f "$tmp_deb/data.tar.xz" ]; then
            sudo tar -xJf "$tmp_deb/data.tar.xz" -C / 2>/dev/null || true
        elif [ -f "$tmp_deb/data.tar.gz" ]; then
            sudo tar -xzf "$tmp_deb/data.tar.gz" -C / 2>/dev/null || true
        fi
        rm -rf "$tmp_deb"
        echo "100"; echo "# Pacchetto installato con successo!"
    ) | yad --progress --title="Installazione $FNAME" --text="Estrazione pacchetto DEB..." --auto-close --center 2>/dev/null || true
}

launch_appimage() {
    local app="$1"
    chmod +x "$app"
    
    # Chiede se integrare nel menu o eseguire soltanto
    local act
    act="$(yad --question \
        --title="OSify — AppImage Rilevata" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Applicazione Portabile AppImage</b></big>\n\nFile: <b>$FNAME</b> ($FSIZE)\n\nVuoi integrarla nel menu di sistema e sul Desktop o avviarla subito?" \
        --button="Integra nel Sistema:0" \
        --button="Esegui Soltanto:2" \
        --button="Annulla:1" --center 2>/dev/null || echo "1")"
    local ret=$?

    if [ $ret -eq 0 ]; then
        # Integrazione in ~/.local/bin e .desktop
        local dest_bin="${HOME:-/root}/.local/bin"
        mkdir -p "$dest_bin" "${HOME:-/root}/.local/share/applications"
        local base_no_ext="${FNAME%.AppImage}"
        local target_bin="$dest_bin/$FNAME"
        cp "$app" "$target_bin"
        chmod +x "$target_bin"

        # Crea desktop entry
        local dt="${HOME:-/root}/.local/share/applications/${base_no_ext}.desktop"
        cat <<EOF > "$dt"
[Desktop Entry]
Type=Application
Name=${base_no_ext}
Exec=${target_bin}
Icon=osify-hub
Terminal=false
Categories=Utility;
EOF
        chmod +x "$dt"
        cp "$dt" "${HOME:-/root}/Desktop/" 2>/dev/null || true
        
        yad --info --title="Integrazione Completata" \
            --text="<big><b>Applicazione Integrata!</b></big>\n\nIcona aggiunta al desktop e al menu applicazioni." \
            --center 2>/dev/null || true
        "$target_bin" &
    elif [ $ret -eq 2 ]; then
        "$app" &
    fi
}

case "$EXT" in
    tazpkg)
        if yad --question --title="Installa Pacchetto Tazpkg" \
            --text="<big><b>Installazione Pacchetto Tazpkg</b></big>\n\nVuoi installare <b>$FNAME</b> ($FSIZE) nel sistema OSify?" \
            --window-icon="$LOGO_IMG" --image="$LOGO_IMG" --center 2>/dev/null; then
            install_tazpkg "$TARGET_FILE"
            yad --info --title="Completato" --text="Pacchetto $FNAME installato correttamente." --center 2>/dev/null || true
        fi
        ;;
    deb)
        if yad --question --title="Installa Pacchetto Debian (.deb)" \
            --text="<big><b>Installazione Pacchetto DEB</b></big>\n\nVuoi estrarre e integrare <b>$FNAME</b> ($FSIZE) nel sistema?" \
            --window-icon="$LOGO_IMG" --image="$LOGO_IMG" --center 2>/dev/null; then
            install_deb "$TARGET_FILE"
            yad --info --title="Completato" --text="Pacchetto $FNAME installato." --center 2>/dev/null || true
        fi
        ;;
    AppImage|appimage)
        launch_appimage "$TARGET_FILE"
        ;;
    sh|run|bin)
        chmod +x "$TARGET_FILE"
        if yad --question --title="Esegui Script / Installer" \
            --text="<big><b>Programma Eseguibile</b></big>\n\nVuoi eseguire il programma <b>$FNAME</b> nel terminale?" \
            --window-icon="$LOGO_IMG" --center 2>/dev/null; then
            if command -v terminal >/dev/null 2>&1; then
                terminal -e "$TARGET_FILE" &
            else
                xterm -e "$TARGET_FILE" &
            fi
        fi
        ;;
    *)
        yad --error --title="Formato Non Riconosciuto" \
            --text="Formato file non supportato dall'installatore rapido: .$EXT" --center 2>/dev/null || true
        ;;
esac
