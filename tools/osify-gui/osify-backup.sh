#!/usr/bin/env bash
# ==============================================================================
# OSify Backup & Restore Center — Salvataggio & Ripristino Dati Personali
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Consente il salvataggio immediato di documenti, preferiti del browser,
# immagini e profili di rete su chiavetta USB o disco esterno, con verifica
# di integrita crittografica SHA256 e ripristino guidato in un click.
# ==============================================================================

set -euo pipefail

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"
USER_HOME="${HOME:-/home/osify}"

create_backup() {
    local dest_dir="${1:-$USER_HOME}"
    local timestamp
    timestamp="$(date +%Y%m%d_%H%M%S)"
    local archive_name="OSify_Backup_${timestamp}.tar.gz"
    local target_path="${dest_dir}/${archive_name}"

    local include_list=()
    [ -d "$USER_HOME/Documenti" ] && include_list+=("Documenti")
    [ -d "$USER_HOME/Scaricati" ] && include_list+=("Scaricati")
    [ -d "$USER_HOME/Desktop" ] && include_list+=("Desktop")
    [ -d "$USER_HOME/Immagini" ] && include_list+=("Immagini")
    [ -d "$USER_HOME/Musica" ] && include_list+=("Musica")
    [ -d "$USER_HOME/.config" ] && include_list+=(".config")

    if [ ${#include_list[@]} -eq 0 ]; then
        echo "[!] Nessuna cartella utente trovata da salvare in $USER_HOME"
        return 1
    fi

    echo "==> Creazione backup in corso: $target_path"
    (
        cd "$USER_HOME"
        tar -czf "$target_path" "${include_list[@]}" 2>/dev/null
        sha256sum "$target_path" > "${target_path}.sha256"
    )

    echo "[OK] Backup completato con successo: $target_path"
    echo "$target_path"
}

restore_backup() {
    local archive_path="$1"
    if [ ! -f "$archive_path" ]; then
        echo "[!] Archivio non trovato: $archive_path"
        return 1
    fi

    # Verifica checksum se presente
    if [ -f "${archive_path}.sha256" ]; then
        echo "==> Verifica integrita crittografica SHA256..."
        (
            cd "$(dirname "$archive_path")"
            sha256sum -c "${archive_path}.sha256" || {
                echo "[!] Errore checksum! Archivio corrotto."
                return 1
            }
        )
    fi

    echo "==> Ripristino in corso nella home: $USER_HOME"
    tar -xzf "$archive_path" -C "$USER_HOME" 2>/dev/null
    echo "[OK] Ripristino completato con successo!"
}

launch_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Uso: $0 {create [dest_dir]|restore <archive.tar.gz>}"
        return 1
    fi

    local action
    action="$(yad --list \
        --title="OSify — Centro Backup & Ripristino" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --text="<big><b>Protezione e Salvataggio Dati Personali</b></big>\nSeleziona l'operazione da eseguire:" \
        --column="Azione" --column="Descrizione" \
        "Salva Backup" "Crea un archivio compresso di documenti, foto e configurazioni su USB o disco" \
        "Ripristina Backup" "Ripristina i tuoi dati personali e preferiti da un backup precedente" \
        --width=540 --height=220 --center 2>/dev/null || echo "")"

    local act_sel
    act_sel="$(echo "$action" | awk -F'|' '{print $1}')"

    case "$act_sel" in
        "Salva Backup")
            local dest
            dest="$(yad --file-selection --directory \
                --title="Seleziona la cartella di destinazione (es. Chiavetta USB)" \
                --center 2>/dev/null || echo "")"
            if [ -n "$dest" ]; then
                local res
                res="$(create_backup "$dest" | tail -n1)"
                yad --info --title="Backup Concluso" \
                    --text="<big><b>Salvataggio Completato!</b></big>\n\nArchivio creato con successo in:\n<b>$res</b>" \
                    --center 2>/dev/null || true
            fi
            ;;
        "Ripristina Backup")
            local src
            src="$(yad --file-selection \
                --title="Seleziona il file di backup (.tar.gz)" \
                --file-filter="Archivi Backup (*.tar.gz)|*.tar.gz" \
                --center 2>/dev/null || echo "")"
            if [ -n "$src" ]; then
                if restore_backup "$src"; then
                    yad --info --title="Ripristino Concluso" \
                        --text="<big><b>Dati Ripristinati con Successo!</b></big>\n\nI tuoi documenti, preferiti e impostazioni sono stati ripristinati nella cartella personale." \
                        --center 2>/dev/null || true
                else
                    yad --error --title="Errore Ripristino" \
                        --text="Impossibile completare il ripristino. Verifica l'integrita del file." \
                        --center 2>/dev/null || true
                fi
            fi
            ;;
    esac
}

case "${1:-gui}" in
    gui|--gui)
        if [ -n "${DISPLAY:-}" ]; then
            launch_gui
        else
            echo "Display X11 non rilevato."
        fi
        ;;
    create|backup)
        create_backup "${2:-$USER_HOME}"
        ;;
    restore)
        restore_backup "${2:-}"
        ;;
    *)
        echo "Uso: $0 {gui|create [dest]|restore <file.tar.gz>}"
        exit 1
        ;;
esac
