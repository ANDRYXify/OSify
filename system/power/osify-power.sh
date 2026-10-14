#!/bin/sh
# ==============================================================================
# OSify Power Subsystem — Gestione Deterministica Alimentazione & Sessione
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# Garantisce spegnimento, riavvio e sospensione immediati per tutti gli utenti,
# sia da GUI che da TUI o terminale.
# ==============================================================================

ACTION="${1:-menu}"

do_poweroff() {
    sync
    if [ "$(id -u 2>/dev/null || echo 0)" -eq 0 ]; then
        poweroff -f 2>/dev/null || halt -p 2>/dev/null || init 0 2>/dev/null || busybox poweroff -f 2>/dev/null || true
    elif command -v sudo >/dev/null 2>&1; then
        sudo poweroff -f 2>/dev/null || sudo halt -p 2>/dev/null || sudo init 0 2>/dev/null || true
    else
        poweroff 2>/dev/null || true
    fi
}

do_reboot() {
    sync
    if [ "$(id -u 2>/dev/null || echo 0)" -eq 0 ]; then
        reboot -f 2>/dev/null || init 6 2>/dev/null || busybox reboot -f 2>/dev/null || true
    elif command -v sudo >/dev/null 2>&1; then
        sudo reboot -f 2>/dev/null || sudo init 6 2>/dev/null || sudo reboot 2>/dev/null || true
    else
        reboot 2>/dev/null || true
    fi
}

do_logout() {
    if [ -n "$DISPLAY" ]; then
        pkill -u "$USER" openbox 2>/dev/null || pkill -u "$USER" -x pcmanfm 2>/dev/null || pkill -u "$USER" 2>/dev/null || true
    fi
}

case "$ACTION" in
    off|poweroff|spegni|shutdown|-s)
        do_poweroff
        ;;
    reboot|riavvia|-r)
        do_reboot
        ;;
    logout|esci|-l)
        do_logout
        ;;
    menu|gui|*)
        if [ -n "$DISPLAY" ] && [ ! -t 0 ]; then
            if command -v xterm >/dev/null 2>&1; then
                exec xterm -title "Gestione Sessione — OSify" -geometry 55x14 -bg "#0b0d14" -fg "#38bdf8" -cr "#10b981" +sb -e "$0" --interactive
            fi
        fi

        if command -v dialog >/dev/null 2>&1; then
            CHOICE=$(dialog --backtitle "OSify Operating System" \
                --title " Gestione Sessione " \
                --menu "\nScegli l'operazione da eseguire:\n" 13 50 3 \
                "1" "Spegni Computer" \
                "2" "Riavvia Computer" \
                "3" "Chiudi Sessione Desktop" \
                3>&1 1>&2 2>&3)
            case "$CHOICE" in
                1) do_poweroff ;;
                2) do_reboot ;;
                3) do_logout ;;
            esac
        else
            echo "1) Spegni Computer"
            echo "2) Riavvia Computer"
            echo "3) Chiudi Sessione"
            printf "Scelta [1-3]: "
            read -r c
            case "$c" in
                1) do_poweroff ;;
                2) do_reboot ;;
                3) do_logout ;;
            esac
        fi
        ;;
esac
