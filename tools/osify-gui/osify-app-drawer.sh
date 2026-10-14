#!/bin/sh
# ==============================================================================
# OSify App Drawer — Tutte le Applicazioni e Launchpad di Sistema
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# ==============================================================================

if [ -n "$DISPLAY" ] && [ ! -t 0 ]; then
    if command -v xterm >/dev/null 2>&1; then
        exec xterm -title "Tutte le Applicazioni — OSify" -geometry 80x25 -bg "#0b0d14" -fg "#38bdf8" -cr "#10b981" +sb -e "$0" --run-tui
    fi
fi

if command -v dialog >/dev/null 2>&1; then
    while true; do
        APP=$(dialog --backtitle "OSify Operating System" \
            --title " Tutte le Applicazioni " \
            --menu "\nSeleziona l'applicazione da avviare:\n" 19 65 11 \
            "1" "Navigatore Web (Dillo / Falkon)" \
            "2" "Gestione File (PCManFM)" \
            "3" "Terminale di Sistema" \
            "4" "Connessione Wi-Fi" \
            "5" "Gestione Attivita e Processi (Task Manager)" \
            "6" "Centro di Controllo e Risoluzioni" \
            "7" "Installa OSify su Disco Fisso" \
            "8" "Profilo Utente e Multiutenza" \
            "9" "Gaming Hub ed Emulazione" \
            "10" "Acquisizione Video HDMI e Console" \
            "11" "Mirroring Smartphone USB" \
            3>&1 1>&2 2>&3)
        [ $? -ne 0 ] && break

        case "$APP" in
            1) /usr/bin/osify-browser & break ;;
            2) pcmanfm & break ;;
            3) /usr/bin/terminal & break ;;
            4) /usr/bin/terminal -geometry 75x20 -T "Connessione Wi-Fi" -e /usr/bin/osify-wifi & break ;;
            5) /usr/bin/osify-taskmanager & break ;;
            6) /usr/bin/osify-settings & break ;;
            7) /usr/bin/osify-install & break ;;
            8) /usr/bin/osify-profile-setup --force & break ;;
            9) /usr/bin/terminal -geometry 75x20 -T "Gaming Hub" -e /usr/bin/osify-games & break ;;
            10) /usr/bin/osify-capture & break ;;
            11) /usr/bin/osify-phone-companion & break ;;
        esac
    done
    exit 0
fi

if [ -x /usr/bin/osify ]; then
    exec /usr/bin/osify app
fi
