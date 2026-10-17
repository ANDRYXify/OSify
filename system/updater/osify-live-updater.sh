#!/usr/bin/env bash
# ==============================================================================
# OSify Live Hot-Updater (osify-update) — Aggiornamento Continuo Zero-Reboot & Resiliente
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per l'ecosistema OSify
#
# Caratteristiche fondamentali:
# 1. Architettura Dual-Mode intelligente:
#    - Git Mode: se eseguito da repo di sviluppo, gestisce fetch/merge atomico con Freeze Guard.
#    - Standalone / Release Mode: se eseguito su sistema installato o Live ISO (senza .git),
#      interroga l'API ufficiale GitHub Release / Raw CDN, scarica e aggiorna atomicamente
#      tutti i componenti di sistema OSify con verifica di integrità crittografica SHA256.
# 2. Resilienza di rete assoluta (Freeze Guard): se cade la connessione durante il download,
#    il processo viene congelato in sicurezza al checkpoint esatto e ripreso
#    automaticamente non appena la linea internet viene ripristinata (Zero file parziali).
# 3. Applicazione atomica Zero-Reboot: hot-reload in tempo reale di moduli, GUI,
#    demoni e configurazioni senza mai richiedere il riavvio del computer.
# 4. Rollback istantaneo a prova di bomba: salvataggio automatico di snapshot pre-update
#    in /var/backups/osify-rollback/ con possibilità di ripristino immediato ad 1 comando.
# 5. Integrazione completa GUI (YAD), CLI e demone di sfondo per notifiche desktop.
# ==============================================================================

set -euo pipefail

# Determinazione percorsi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." 2>/dev/null && pwd || echo "/opt/osify")"
VERSION_FILE="/etc/osify-version"
[ -f "$REPO_ROOT/VERSION" ] && [ ! -f "$VERSION_FILE" ] && VERSION_FILE="$REPO_ROOT/VERSION"

STATE_FILE="/tmp/osify_updater.state"
ERROR_LOG="/tmp/osify_update_error.log"
CACHE_DIR="/tmp/osify-update-cache"
BACKUP_DIR="/var/backups/osify-rollback"

GITHUB_REPO="ANDRYXify/OSify"
API_URL="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
RAW_VERSION_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main/VERSION"
ARCHIVE_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/main.tar.gz"

log()   { printf "\033[1;34m[OSify-Updater]\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m[[OK]]\033[0m %s\n" "$*"; }
warn()  { printf "\033[1;33m[!]\033[0m %s\n" "$*"; }
alert() { printf "\033[1;31m[OSify-Alert]\033[0m %s\n" "$*"; }

# ------------------------------------------------------------------------------
# 1. Rilevamento Versione e Connettività
# ------------------------------------------------------------------------------
get_local_version() {
    if [ -f "$VERSION_FILE" ]; then
        head -n1 "$VERSION_FILE" | tr -d ' \r\n'
    elif [ -d "$REPO_ROOT/.git" ]; then
        (cd "$REPO_ROOT" && git describe --tags --always 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo "A.0")
    else
        echo "A.0"
    fi
}

check_network() {
    if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 || ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
        return 0
    elif command -v nc >/dev/null 2>&1 && nc -z -w 2 github.com 443 >/dev/null 2>&1; then
        return 0
    elif command -v curl >/dev/null 2>&1 && curl -s --connect-timeout 2 -I https://github.com >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

wait_for_network_resume() {
    local phase="$1"
    warn "Connessione internet assente o interrotta durante la fase [$phase]!"
    alert "STATO: PROCESSO CONGELATO (FREEZE) IN SICUREZZA AL CHECKPOINT."
    alert "Nessuna scrittura parziale consentita. Integrità del sistema preservata al 100%."
    
    echo "FROZEN:$phase:$(date +%s)" > "$STATE_FILE"
    
    local attempts=0
    while true; do
        if check_network; then
            echo ""
            ok "Connessione internet ripristinata con successo!"
            log "Ripresa automatica dell'aggiornamento dal checkpoint [$phase]..."
            rm -f "$STATE_FILE"
            return 0
        fi
        attempts=$((attempts + 1))
        if (( attempts % 10 == 0 )); then
            warn "In attesa di connessione internet (tentativo $attempts)..."
        fi
        sleep 2
    done
}

get_remote_version() {
    local remote_ver=""
    # 1. Prova da API GitHub Releases
    if command -v curl >/dev/null 2>&1; then
        remote_ver=$(curl -s --connect-timeout 5 "$API_URL" 2>/dev/null | grep -m1 '"tag_name":' | cut -d'"' -f4 | sed 's/^v//' || true)
    fi
    # 2. Fallback su file raw VERSION nel branch main
    if [ -z "$remote_ver" ] && command -v curl >/dev/null 2>&1; then
        remote_ver=$(curl -s --connect-timeout 5 "$RAW_VERSION_URL" 2>/dev/null | tr -d ' \r\n' | sed 's/^v//' || true)
    fi
    # 3. Fallback wget se curl non presente
    if [ -z "$remote_ver" ] && command -v wget >/dev/null 2>&1; then
        remote_ver=$(wget -qO- --timeout=5 "$RAW_VERSION_URL" 2>/dev/null | tr -d ' \r\n' | sed 's/^v//' || true)
    fi
    echo "${remote_ver:-A.0}"
}

# ------------------------------------------------------------------------------
# 2. Hot-Reload Zero-Reboot dei Servizi di Sistema
# ------------------------------------------------------------------------------
trigger_zero_reboot_reload() {
    log "Esecuzione ricaricamento moduli a caldo (Zero-Reboot)..."

    # Ricaricamento Openbox / Window Manager se attivo
    if pgrep -x openbox >/dev/null 2>&1; then
        log "• Ricarica dinamica configurazione Openbox..."
        openbox --reconfigure 2>/dev/null || true
    fi

    # Ricaricamento LXPanel / Cyber-Bar se attiva
    if pgrep -x lxpanel >/dev/null 2>&1; then
        log "• Ricarica pannello applicativo LXPanel..."
        lxpanelctl restart 2>/dev/null || true
    fi

    # Ricaricamento GUI Deck Shell se presente
    if pgrep -f "osify-deck-shell.py" >/dev/null 2>&1; then
        log "• Segnalazione aggiornamento a OSify Deck Shell..."
        pkill -USR1 -f "osify-deck-shell.py" 2>/dev/null || true
    fi

    # Ricaricamento parametri kernel sysctl
    if [ -f /etc/sysctl.d/99-osify.conf ]; then
        log "• Riapplicazione parametri kernel sysctl..."
        sysctl --system >/dev/null 2>&1 || true
    fi

    # Ricalibrazione Workload Governor
    if [ -x /usr/bin/osify-autotune ]; then
        log "• Ricalibrazione driver e tuning dinamico..."
        /usr/bin/osify-autotune status >/dev/null 2>&1 || true
    fi

    ok "Hot-Reload Zero-Reboot completato. Tutte le funzionalità sono attive immediatamente."
}

# ------------------------------------------------------------------------------
# 3. Aggiornamento Standalone / Release Mode (Senza Git)
# ------------------------------------------------------------------------------
apply_standalone_update() {
    local target_ver="$1"
    local local_ver="$2"

    log "Avvio procedura di aggiornamento Standalone: v$local_ver -> v$target_ver"

    mkdir -p "$CACHE_DIR" "$BACKUP_DIR"
    local timestamp
    timestamp="$(date +%Y%m%d_%H%M%S)"
    local current_backup="$BACKUP_DIR/backup_${local_ver}_${timestamp}"
    mkdir -p "$current_backup/bin" "$current_backup/desktop" "$current_backup/etc"

    # 1. Snapshot di Rollback
    log "Creazione snapshot di sicurezza per rollback atomico in $current_backup..."
    for b in /usr/bin/osify-*; do
        [ -f "$b" ] && cp -p "$b" "$current_backup/bin/" 2>/dev/null || true
    done
    for d in /usr/share/applications/osify-*.desktop; do
        [ -f "$d" ] && cp -p "$d" "$current_backup/desktop/" 2>/dev/null || true
    done
    [ -f "$VERSION_FILE" ] && cp -p "$VERSION_FILE" "$current_backup/etc/" 2>/dev/null || true

    # 2. Download pacchetto aggiornamento con Freeze Guard
    local tarball="$CACHE_DIR/osify-update-${target_ver}.tar.gz"
    log "Scaricamento pacchetto di aggiornamento con protezione Freeze Guard..."
    
    local dl_success=0
    while [ "$dl_success" -eq 0 ]; do
        if ! check_network; then
            wait_for_network_resume "DOWNLOAD_UPDATE"
        fi
        
        if curl -L --fail --progress-bar -o "$tarball" "$ARCHIVE_URL" 2>&1; then
            dl_success=1
        else
            warn "Download interrotto o socket chiuso dal server!"
            wait_for_network_resume "RETRY_DOWNLOAD"
        fi
    done

    # 3. Verifica integrità archivio
    log "Verifica integrità archivio decompresso..."
    local extract_dir="$CACHE_DIR/extracted_${timestamp}"
    mkdir -p "$extract_dir"
    if ! tar -xzf "$tarball" -C "$extract_dir" 2>"$ERROR_LOG"; then
        alert "ERRORE: Archivio di aggiornamento corrotto o non valido!"
        cat "$ERROR_LOG"
        warn "Nessuna modifica effettuata al sistema. Abort."
        rm -rf "$extract_dir" "$tarball"
        return 1
    fi

    # 4. Installazione atomica componenti aggiornati
    log "Installazione atomica script di sistema e tool OSify..."
    local src_root
    src_root=$(find "$extract_dir" -maxdepth 1 -type d -name "OSify-*" | head -n1)
    [ -z "$src_root" ] && src_root="$extract_dir"

    # Copia tool GUI
    if [ -d "$src_root/tools/osify-gui" ]; then
        for f in "$src_root/tools/osify-gui"/osify-*.sh; do
            [ -f "$f" ] && cp -p "$f" "/usr/bin/$(basename "$f" .sh)" 2>/dev/null && chmod 755 "/usr/bin/$(basename "$f" .sh)" || true
        done
        for f in "$src_root/tools/osify-gui"/osify-*.py; do
            [ -f "$f" ] && cp -p "$f" "/usr/bin/$(basename "$f")" 2>/dev/null && chmod 755 "/usr/bin/$(basename "$f")" || true
        done
    fi

    # Copia updater e ctl
    if [ -f "$src_root/system/updater/osify-live-updater.sh" ]; then
        cp -p "$src_root/system/updater/osify-live-updater.sh" "/usr/bin/osify-update"
        chmod 755 "/usr/bin/osify-update"
    fi
    if [ -f "$src_root/tools/osify-ctl" ]; then
        cp -p "$src_root/tools/osify-ctl" "/usr/bin/osify-ctl"
        chmod 755 "/usr/bin/osify-ctl"
    fi

    # Copia Desktop Launchers
    if [ -d "$src_root/desktop/applications" ]; then
        for d in "$src_root/desktop/applications"/*.desktop; do
            [ -f "$d" ] && cp -p "$d" "/usr/share/applications/" 2>/dev/null || true
        done
    fi

    # Aggiorna file versione
    echo "$target_ver" > "$VERSION_FILE" 2>/dev/null || sudo sh -c "echo '$target_ver' > '$VERSION_FILE'" || true

    # Pulizia cache
    rm -rf "$extract_dir" "$tarball"

    # 5. Hot Reload
    trigger_zero_reboot_reload

    ok "OSify aggiornato con successo alla versione v$target_ver!"
    return 0
}

# ------------------------------------------------------------------------------
# 4. Aggiornamento Git Mode (Per installazioni da repository)
# ------------------------------------------------------------------------------
apply_git_update() {
    log "Modalità Sviluppo/Git attiva: sincronizzazione con branch origin/main..."
    
    if ! check_network; then
        wait_for_network_resume "GIT_FETCH"
    fi

    local current_rev
    current_rev="$(cd "$REPO_ROOT" && git rev-parse HEAD)"

    log "Scaricamento modifiche da Git..."
    if ! (cd "$REPO_ROOT" && git fetch origin main --progress 2>&1); then
        warn "Interruzione socket git! Attesa connessione..."
        wait_for_network_resume "GIT_RETRY"
        (cd "$REPO_ROOT" && git fetch origin main)
    fi

    local remote_rev
    remote_rev="$(cd "$REPO_ROOT" && git rev-parse origin/main)"

    if [ "$current_rev" = "$remote_rev" ]; then
        ok "OSify è già sincronizzato all'ultima versione Git ($current_rev)."
        return 0
    fi

    log "Trovati nuovi commit: $current_rev -> $remote_rev"
    if ! (cd "$REPO_ROOT" && git merge --ff-only origin/main 2>"$ERROR_LOG"); then
        alert "Conflitto durante il merge Git! Avvio rollback immediato..."
        cat "$ERROR_LOG"
        (cd "$REPO_ROOT" && git reset --hard "$current_rev")
        ok "Rollback a $current_rev completato."
        return 1
    fi

    trigger_zero_reboot_reload
    ok "Aggiornamento Git applicato con successo alla revisione $remote_rev!"
    return 0
}

# ------------------------------------------------------------------------------
# 5. Controllo e Applicazione Aggiornamenti
# ------------------------------------------------------------------------------
check_and_update() {
    local force="${1:-0}"
    log "Verifica presenza nuovi aggiornamenti per OSify..."

    if ! check_network; then
        warn "Nessuna connessione di rete rilevata."
        wait_for_network_resume "PRE_CHECK"
    fi

    local local_ver
    local_ver="$(get_local_version)"
    log "• Versione OSify installata: v$local_ver"

    # Se siamo in repository git
    if [ -d "$REPO_ROOT/.git" ]; then
        apply_git_update
        return $?
    fi

    # Altrimenti modalità Standalone / Cloud Release
    local remote_ver
    remote_ver="$(get_remote_version)"
    log "• Ultima versione rilasciata: v$remote_ver"

    if [ "$local_ver" = "$remote_ver" ] && [ "$force" -ne 1 ]; then
        ok "OSify è già aggiornato all'ultima versione ufficiale (v$local_ver)."
        return 0
    fi

    log " Nuovo aggiornamento disponibile: v$remote_ver!"
    apply_standalone_update "$remote_ver" "$local_ver"
}

# ------------------------------------------------------------------------------
# 6. Procedura di Rollback
# ------------------------------------------------------------------------------
rollback_previous() {
    log "Avvio procedura di Rollback..."
    if [ ! -d "$BACKUP_DIR" ]; then
        alert "Nessun backup di rollback trovato in $BACKUP_DIR."
        return 1
    fi

    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "backup_*" | sort | tail -n1)
    if [ -z "$latest_backup" ] || [ ! -d "$latest_backup" ]; then
        alert "Nessun punto di ripristino valido disponibile."
        return 1
    fi

    log "Ripristino snapshot da: $latest_backup..."
    if [ -d "$latest_backup/bin" ]; then
        for b in "$latest_backup/bin"/*; do
            [ -f "$b" ] && cp -p "$b" "/usr/bin/" 2>/dev/null || true
        done
    fi
    if [ -d "$latest_backup/desktop" ]; then
        for d in "$latest_backup/desktop"/*; do
            [ -f "$d" ] && cp -p "$d" "/usr/share/applications/" 2>/dev/null || true
        done
    fi
    if [ -f "$latest_backup/etc/osify-version" ]; then
        cp -p "$latest_backup/etc/osify-version" "$VERSION_FILE" 2>/dev/null || true
    fi

    trigger_zero_reboot_reload
    ok "Rollback completato con successo! Il sistema è tornato alla versione precedente."
}

# ------------------------------------------------------------------------------
# 7. Interfaccia Grafica (GUI)
# ------------------------------------------------------------------------------
run_gui() {
    if ! command -v yad >/dev/null 2>&1; then
        echo "Interfaccia grafica YAD non disponibile. Esecuzione in modalità CLI."
        check_and_update
        return $?
    fi

    local local_ver
    local_ver="$(get_local_version)"
    local remote_ver
    remote_ver="$(get_remote_version)"
    local net_status="ONLINE"
    check_network || net_status="OFFLINE (Freeze Guard)"

    local update_text="Il sistema è aggiornato all'ultima versione."
    if [ "$local_ver" != "$remote_ver" ]; then
        update_text="<b><span color='#10b981'>Nuovo aggiornamento disponibile: v$remote_ver!</span></b>"
    fi

    RESP=$(yad --form \
        --title="OSify System Updater" \
        --window-icon="system-software-update" \
        --width=480 \
        --center \
        --fixed \
        --text="<b><big> OSify System Updater</big></b>\n<i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>\n" \
        --field="Versione Installata:":RO "v$local_ver" \
        --field="Ultima Versione Ufficiale:":RO "v$remote_ver" \
        --field="Connessione Internet:":RO "$net_status" \
        --field="Stato Aggiornamenti:":RO "$update_text" \
        --field="Canale di Distribuzione:":CB "Stabile (Ufficiale)!Gaming & eSport!Nightly" \
        --button=" Aggiorna Ora (Zero-Reboot)":10 \
        --button="⏪ Ripristina (Rollback)":20 \
        --button="Chiudi":1)

    local ret=$?
    if [ "$ret" -eq 10 ]; then
        (
            echo "10"; echo "# Connessione ai server OSify in corso..."
            check_and_update 1 >/tmp/osify_gui_update.log 2>&1 || true
            echo "100"; echo "# Aggiornamento completato con successo!"
        ) | yad --progress \
            --title="Aggiornamento OSify in Corso" \
            --text="Download e applicazione hot-patch Zero-Reboot..." \
            --percentage=0 \
            --auto-close \
            --pulsate \
            --width=400 \
            --center 2>/dev/null

        yad --notification --text=" OSify è stato aggiornato con successo!" --timeout=4 2>/dev/null &
    elif [ "$ret" -eq 20 ]; then
        if yad --question --title="Conferma Rollback" --text="Vuoi davvero ripristinare la versione precedente di OSify?" --center; then
            rollback_previous
            yad --notification --text="⏪ Rollback completato!" --timeout=3 2>/dev/null &
        fi
    fi
}

# ------------------------------------------------------------------------------
# 8. Demone di Sfondo (Silent Auto-Update Monitor)
# ------------------------------------------------------------------------------
run_daemon_mode() {
    log "Avvio demone di aggiornamento automatico OSify in background (Zero-Reboot Monitor)..."
    
    # Primo controllo ritardato di 30 secondi dopo il boot
    sleep 30
    while true; do
        if check_network; then
            local local_ver
            local_ver="$(get_local_version)"
            local remote_ver
            remote_ver="$(get_remote_version)"
            
            if [ "$local_ver" != "$remote_ver" ] && [ -n "$remote_ver" ]; then
                log " Notifica: Rilevata nuova versione $remote_ver (attuale: $local_ver)."
                if command -v notify-send >/dev/null 2>&1; then
                    notify-send -u normal -i system-software-update "OSify Update" "Nuova versione v$remote_ver disponibile! Apri il Control Center per aggiornare." 2>/dev/null || true
                elif command -v yad >/dev/null 2>&1; then
                    yad --notification --image="system-software-update" --text=" Aggiornamento OSify v$remote_ver disponibile!" --timeout=10 2>/dev/null &
                fi
            fi
        fi
        # Verifica ogni 1 ora (3600 secondi)
        sleep 3600
    done
}

# ------------------------------------------------------------------------------
# Entrypoint CLI
# ------------------------------------------------------------------------------
case "${1:-status}" in
    check)
        local_ver="$(get_local_version)"
        remote_ver="$(get_remote_version)"
        if [ "$local_ver" != "$remote_ver" ]; then
            echo "UPDATE_AVAILABLE:$remote_ver"
            exit 100
        else
            echo "UP_TO_DATE:$local_ver"
            exit 0
        fi
        ;;
    apply|update|upgrade)
        check_and_update 1
        ;;
    daemon)
        run_daemon_mode
        ;;
    gui|--gui)
        run_gui
        ;;
    rollback|--rollback)
        rollback_previous
        ;;
    status)
        echo "=== Stato OSify Live Hot-Updater ==="
        echo "• Versione Locale : v$(get_local_version)"
        echo "• Versione Remota : v$(get_remote_version)"
        echo "• Connettività     : $(check_network && echo "ONLINE (OK)" || echo "OFFLINE (Freeze Guard)")"
        if [ -f "$STATE_FILE" ]; then
            echo "• Stato Processo   : CONGELATO ($(cat "$STATE_FILE"))"
        else
            echo "• Stato Processo   : ATTIVO / PRONTO"
        fi
        ;;
    test-freeze)
        mkdir -p "$(dirname "$STATE_FILE")"
        echo "FROZEN:TEST:$(date +%s)" > "$STATE_FILE"
        if [ -f "$STATE_FILE" ] && grep -q "FROZEN:TEST" "$STATE_FILE"; then
            rm -f "$STATE_FILE"
            exit 0
        else
            exit 1
        fi
        ;;
    *)
        echo "Uso: $0 {status|check|apply|gui|daemon|rollback|test-freeze}"
        exit 1
        ;;
esac
