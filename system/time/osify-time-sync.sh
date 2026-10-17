#!/usr/bin/env bash
# ==============================================================================
# OSify Time & CMOS Battery Rescue — Sincronizzazione Atomica Orologio
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Risolve il problema critico delle batterie tampone CMOS scariche (comunissime su
# netbook Toshiba NB200 e PC vintage): quando l'ora si resetta al passato (2000-2009),
# tutti i certificati SSL/HTTPS falliscono. Questo tool riallinea la data via NTP
# o HTTP Date Header (se le porte UDP 123 sono filtrate) e aggiorna l'RTC hardware.
# ==============================================================================

set -euo pipefail

MIN_YEAR=2024

get_current_year() {
    date +%Y
}

sync_time_ntp() {
    echo "[+] Tentativo sincronizzazione tramite server NTP (pool.ntp.org)..."
    if command -v ntpdate >/dev/null 2>&1; then
        sudo ntpdate -s pool.ntp.org 2>/dev/null && return 0
    elif command -v chronyd >/dev/null 2>&1; then
        sudo chronyd -q 'server pool.ntp.org iburst' 2>/dev/null && return 0
    elif command -v sntp >/dev/null 2>&1; then
        sudo sntp -s pool.ntp.org 2>/dev/null && return 0
    fi
    return 1
}

sync_time_http() {
    echo "[+] Tentativo sincronizzazione fallback tramite HTTP Date Header..."
    # Se NTP è bloccato dal router o firewall, estraiamo l'ora esatta dagli header HTTP di Google/Cloudflare
    local http_date
    http_date="$(curl -sI --connect-timeout 5 https://www.google.com 2>/dev/null | grep -i '^date:' | sed 's/^[Dd]ate:[ \t]*//' || echo "")"
    
    if [ -z "$http_date" ]; then
        http_date="$(curl -sI --connect-timeout 5 https://1.1.1.1 2>/dev/null | grep -i '^date:' | sed 's/^[Dd]ate:[ \t]*//' || echo "")"
    fi

    if [ -n "$http_date" ]; then
        echo "[+] Data estratta da rete HTTP: $http_date"
        sudo date -s "$http_date" >/dev/null 2>&1 || true
        return 0
    fi
    return 1
}

auto_check_and_fix() {
    local cur_year
    cur_year="$(get_current_year)"
    if [ "$cur_year" -lt "$MIN_YEAR" ]; then
        echo "[!] ALLERTA: Orologio di sistema non allineato (Anno $cur_year < $MIN_YEAR, probabile batteria CMOS scarica)."
        if sync_time_ntp || sync_time_http; then
            echo "[[OK]] Orologio sincronizzato con successo: $(date)"
            # Salva nell'RTC hardware per i successivi riavvii
            sudo hwclock --systohc 2>/dev/null || true
            if command -v notify-send >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
                notify-send "Orologio OSify Sincronizzato" "Data e ora corrette: $(date +'%d/%m/%Y %H:%M')" -i /usr/share/pixmaps/osify-settings.png || true
            fi
        else
            echo "[!] Impossibile sincronizzare l'orologio (rete non ancora disponibile)."
        fi
    else
        echo "[[OK]] Orologio di sistema valido (Anno $cur_year)."
    fi
}

set_manual_time() {
    local new_dt="$1"
    sudo date -s "$new_dt" 2>/dev/null || true
    sudo hwclock --systohc 2>/dev/null || true
    echo "[[OK]] Data impostata: $(date)"
}

launch_gui() {
    local cur_date
    cur_date="$(date +'%Y-%m-%d %H:%M:%S')"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local res
        res="$(yad --form --title="Data, Ora & Sincronizzazione OSify" \
            --text="<b>Gestione Orologio di Sistema & Protezione CMOS</b>\nData e Ora Attuali: <b>${cur_date}</b>" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=440 --center \
            --field="Imposta Data Manuale (AAAA-MM-GG):" "$(date +'%Y-%m-%d')" \
            --field="Imposta Ora Manuale (HH:MM:SS):" "$(date +'%H:%M:%S')" \
            --button="Sincronizza via Internet:2" \
            --button="Salva Manuale:0" \
            --button="Chiudi:1" 2>/dev/null || echo "")"
        local ret=$?

        if [ "$ret" -eq 2 ]; then
            if sync_time_ntp || sync_time_http; then
                sudo hwclock --systohc 2>/dev/null || true
                yad --info --title="Sincronizzazione Riuscita" --text="Orologio allineato:\n<b>$(date)</b>" --center || true
            else
                yad --error --title="Errore Sincronizzazione" --text="Verifica la connessione a Internet e riprova." --center || true
            fi
        elif [ "$ret" -eq 0 ] && [ -n "$res" ]; then
            local n_d n_t
            n_d="$(echo "$res" | cut -d'|' -f1)"
            n_t="$(echo "$res" | cut -d'|' -f2)"
            set_manual_time "${n_d} ${n_t}"
        fi
    else
        echo "Data attuale: $(date)"
        auto_check_and_fix
    fi
}

case "${1:-check}" in
    check|daemon) auto_check_and_fix ;;
    sync) sync_time_ntp || sync_time_http ;;
    gui|--gui) launch_gui ;;
    *) echo "Uso: $0 {check|sync|gui}" ;;
esac
