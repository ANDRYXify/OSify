#!/bin/sh
# ==============================================================================
# OSify — Inizializzatore del File System in Lingua Italiana
# ==============================================================================
# Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
# Struttura le directory native del sistema operativo in italiano:
# /Sistema, /Applicazioni, /Utenti/<nome>/Documenti, Scaricati, Progetti...
# ==============================================================================

# 1. Albero /Sistema
mkdir -p /Sistema/Driver /Sistema/Servizi /Sistema/Icone /Sistema/Dati

# Popola /Sistema/Icone se presente /usr/share/pixmaps
if [ -d /usr/share/pixmaps ]; then
    for ic in /usr/share/pixmaps/*; do
        [ -e "$ic" ] && ln -sf "$ic" /Sistema/Icone/ 2>/dev/null || true
    done
fi

# 2. Servizi di Sistema (.ify)
mkdir -p /Sistema/Servizi
if [ -d /opt/osify/sistema/servizi ]; then
    cp -r /opt/osify/sistema/servizi/* /Sistema/Servizi/ 2>/dev/null || true
    chmod -R 755 /Sistema/Servizi/ 2>/dev/null || true
fi

# 2.1 Driver di Sistema (.ify)
mkdir -p /Sistema/Driver
if [ -d /opt/osify/sistema/driver ]; then
    cp -r /opt/osify/sistema/driver/* /Sistema/Driver/ 2>/dev/null || true
    chmod -R 755 /Sistema/Driver/ 2>/dev/null || true
fi

# 3. Albero /Applicazioni
mkdir -p /Applicazioni
if [ -d /opt/osify/applicazioni ]; then
    for app in /opt/osify/applicazioni/*.ify; do
        if [ -d "$app" ]; then
            app_name=$(basename "$app")
            ln -sf "$app" "/Applicazioni/$app_name" 2>/dev/null || true
        fi
    done
fi

# 4. Albero /Utenti
mkdir -p /Utenti
CURRENT_USER="${USER:-osify}"
USER_HOME="${HOME:-/home/$CURRENT_USER}"

if [ -d "$USER_HOME" ]; then
    ln -sf "$USER_HOME" "/Utenti/$CURRENT_USER" 2>/dev/null || true
    
    # Creazione cartelle utente in lingua italiana pura
    for folder in Scrivania Documenti Scaricati Immagini Musica Video Progetti Applicazioni; do
        mkdir -p "$USER_HOME/$folder"
    done

    # Configurazione xdg-user-dirs se disponibile
    if [ -f "$USER_HOME/.config/user-dirs.dirs" ]; then
        cat << EOF > "$USER_HOME/.config/user-dirs.dirs"
XDG_DESKTOP_DIR="\$HOME/Scrivania"
XDG_DOWNLOAD_DIR="\$HOME/Scaricati"
XDG_TEMPLATES_DIR="\$HOME/Modelli"
XDG_PUBLICSHARE_DIR="\$HOME/Pubblici"
XDG_DOCUMENTS_DIR="\$HOME/Documenti"
XDG_MUSIC_DIR="\$HOME/Musica"
XDG_PICTURES_DIR="\$HOME/Immagini"
XDG_VIDEOS_DIR="\$HOME/Video"
EOF
    fi
fi

exit 0
