#!/bin/sh
# ==============================================================================
# OSify App Drawer 2050 — Launchpad e Centro Applicazioni Universale
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# 100% GUI: interfaccia grafica nativa senza terminale né finestre xterm.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"

# 1. Priorità: Drawer Grafico Python Nativo (Search live, griglia e categorie)
if [ -n "$DISPLAY" ] && command -v python3 >/dev/null 2>&1; then
    PY_DRAWER="$SCRIPT_DIR/osify-app-drawer.py"
    [ ! -f "$PY_DRAWER" ] && PY_DRAWER="/opt/osify/tools/osify-gui/osify-app-drawer.py"
    [ ! -f "$PY_DRAWER" ] && PY_DRAWER="/usr/bin/osify-app-drawer.py"
    if [ -f "$PY_DRAWER" ]; then
        exec python3 "$PY_DRAWER" "$@"
    fi
fi

# 2. Alternativa Grafica YAD (Cyber-Grid 2050)
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    APP_CHOSEN=$(yad --title="OSify Launchpad 2050" \
        --window-icon="/usr/share/pixmaps/osify-drawer.png" \
        --width=680 --height=460 --center \
        --list \
        --text="<b><big>OSify Universal Launchpad</big></b>\nSeleziona l'applicazione da avviare sul tuo computer:" \
        --column="Icona:IMG" --column="Applicazione" --column="Categoria" --column="Descrizione" \
        "/usr/share/pixmaps/osify-hub.png" "OSify Hub & Dashboard" "Sistema" "Centro di controllo e prestazioni a 360°" \
        "/usr/share/pixmaps/osify-browser.png" "Navigatore Web" "Internet" "Navigazione web ultra-leggera e veloce" \
        "/usr/share/pixmaps/osify-wifi.png" "Connessione Wi-Fi" "Rete" "Scansione e gestione reti wireless" \
        "/usr/share/pixmaps/osify-games.png" "Gaming & Retrogaming Hub" "Giochi" "Esecutore giochi Windows, DOS e ROM" \
        "/usr/share/pixmaps/osify-files.png" "Gestione File" "Sistema" "Esplora dischi, partizioni e cartelle utente" \
        "/usr/share/pixmaps/osify-terminal.png" "Terminale di Sistema" "Sviluppo" "Shell di comando interattiva" \
        "/usr/share/pixmaps/osify-developer.png" "Sviluppo & Codice" "Sviluppo" "Ambiente Python, C, Git e UEM" \
        "/usr/share/pixmaps/osify-appearance.png" "Cattura Schermo" "Grafica" "Screenshot immediato o con ritardo" \
        "/usr/share/pixmaps/osify-audio.png" "Lettore Multimediale" "Media" "Musica e video a bassa latenza" \
        "/usr/share/pixmaps/osify-notepad.png" "Blocco Note & Editor" "Ufficio" "Editor di testo essenziale" \
        "/usr/share/pixmaps/osify-calculator.png" "Calcolatrice" "Utilita" "Calcoli aritmetici e scientifici" \
        "/usr/share/pixmaps/osify-settings.png" "Personalizzazione & Aspetto" "Impostazioni" "Sfondo, risoluzioni display e tema" \
        "/usr/share/pixmaps/osify-install.png" "Installa OSify su Disco" "Sistema" "Installatore autonomo su memoria fissa" \
        "/usr/share/pixmaps/osify-settings.png" "Profilo Utente" "Sistema" "Configurazione identita e password" \
        --button="Chiudi!gtk-cancel:1" \
        --button="Avvia!gtk-ok:0") || exit 0

    APP_NAME=$(echo "$APP_CHOSEN" | cut -d'|' -f2)
    case "$APP_NAME" in
        *"Hub"*) /usr/bin/osify-hub & ;;
        *"Web"*) /usr/bin/osify-browser & ;;
        *"Wi-Fi"*) /usr/bin/osify-wifi & ;;
        *"Gaming"*) /usr/bin/osify-games & ;;
        *"File"*) pcmanfm & ;;
        *"Terminale"*) /usr/bin/terminal & ;;
        *"Sviluppo"*) /usr/bin/osify-developer & ;;
        *"Cattura"*) /usr/bin/osify-screenshot --gui & ;;
        *"Multimediale"*) /usr/bin/osify-media-player & ;;
        *"Blocco Note"*) /usr/bin/osify-notepad & ;;
        *"Calcolatrice"*) /usr/bin/osify-calculator & ;;
        *"Personalizzazione"*) /usr/bin/osify-appearance & ;;
        *"Installa"*) /usr/bin/osify-install & ;;
        *"Profilo"*) /usr/bin/osify-profile-setup --force & ;;
    esac
    exit 0
fi

# 3. Alternativa Grafica Zenity
if [ -n "$DISPLAY" ] && command -v zenity >/dev/null 2>&1; then
    APP_NAME=$(zenity --list --title="Tutte le Applicazioni" \
        --column="Applicazione" \
        "OSify Hub" "Navigatore Web" "Connessione Wi-Fi" "Gaming Hub" \
        "Gestione File" "Terminale" "Sviluppo" "Installa su Disco" \
        --width=400 --height=350) || exit 0
    case "$APP_NAME" in
        *"Hub"*) /usr/bin/osify-hub & ;;
        *"Web"*) /usr/bin/osify-browser & ;;
        *"Wi-Fi"*) /usr/bin/osify-wifi & ;;
        *"Gaming"*) /usr/bin/osify-games & ;;
        *"File"*) pcmanfm & ;;
        *"Terminale"*) /usr/bin/terminal & ;;
        *"Sviluppo"*) /usr/bin/osify-developer & ;;
        *"Installa"*) /usr/bin/osify-install & ;;
    esac
    exit 0
fi

exit 0
