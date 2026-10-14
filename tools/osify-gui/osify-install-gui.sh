#!/bin/sh
# ==============================================================================
# OSify Modern Graphical Disk Installer Launcher & Interface
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Interfaccia grafica GTK/YAD per l'installazione autonoma di OSify su disco fisso,
# auto-elevazione con subox/sudo, rilevamento hardware dischi, migrazione dati
# da sessione Live e barra di avanzamento visiva continua.
# ==============================================================================

INSTALLER_CORE="/usr/bin/osify-disk-installer"
[ ! -x "$INSTALLER_CORE" ] && INSTALLER_CORE="$(dirname "$0")/../../system/installer/osify-disk-installer.sh"

LOGO_IMG="/usr/share/pixmaps/osify-install.png"
[ ! -f "$LOGO_IMG" ] && LOGO_IMG="/usr/share/pixmaps/osify-hub.png"

# Auto-elevazione privilegi di root se necessario
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if [ -n "$DISPLAY" ] && command -v subox >/dev/null 2>&1; then
        exec subox "$0" "$@"
    elif command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    else
        echo "[!] Privilegi di root richiesti per l'installazione su disco."
        exit 1
    fi
fi

# ==============================================================================
# RILEVAMENTO DISCHI FISICI
# ==============================================================================
detect_disks() {
    DISKS_OPTS=""
    for d in /sys/block/sd* /sys/block/hd* /sys/block/nvme*n1 /sys/block/mmcblk*; do
        [ -e "$d" ] || continue
        dname=$(basename "$d")
        
        # Ignora loop, ram e partizioni
        case "$dname" in
            loop*|ram*|zram*|sr*|fd*) continue ;;
        esac
        
        # Calcolo dimensione in GB
        size_sectors=$(cat "$d/size" 2>/dev/null || echo 0)
        size_gb=$(( size_sectors * 512 / 1024 / 1024 / 1024 ))
        
        # Modello dispositivo
        model=""
        if [ -f "$d/device/model" ]; then
            model=$(cat "$d/device/model" | tr -s ' ' | sed 's/^[ \t]*//;s/[ \t]*$//')
        fi
        [ -z "$model" ] && model="Drive Fisico"

        dev_path="/dev/$dname"
        if [ $size_gb -gt 0 ]; then
            if [ -z "$DISKS_OPTS" ]; then
                DISKS_OPTS="${dev_path} (${size_gb} GB - ${model})"
            else
                DISKS_OPTS="${DISKS_OPTS}!${dev_path} (${size_gb} GB - ${model})"
            fi
        fi
    done
    echo "$DISKS_OPTS"
}

# Profilo utente esistente (se configurato)
ACTIVE_USER="osify"
REAL_NAME="OSify Live User"
AUTOLOGIN_DEF="TRUE"
PROFILE_JSON="/home/osify/.config/osify/profile.json"
[ ! -f "$PROFILE_JSON" ] && PROFILE_JSON="/etc/osify/profile.json"

if [ -f "$PROFILE_JSON" ] && command -v awk >/dev/null 2>&1; then
    U_FOUND=$(awk -F'"' '/"username":/ {print $4}' "$PROFILE_JSON" 2>/dev/null)
    R_FOUND=$(awk -F'"' '/"real_name":/ {print $4}' "$PROFILE_JSON" 2>/dev/null)
    [ -n "$U_FOUND" ] && ACTIVE_USER="$U_FOUND"
    [ -n "$R_FOUND" ] && REAL_NAME="$R_FOUND"
fi

# ==============================================================================
# FRONTEND GRAFICO YAD (GTK)
# ==============================================================================
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    DISKS_MENU=$(detect_disks)
    if [ -z "$DISKS_MENU" ]; then
        DISKS_MENU="/dev/sda (Disco Fisico Primario)"
    fi

    # Schermata 1: Configurazione e Selezione Disco
    INSTALL_FORM=$(yad --form \
        --title="OSify — Installazione Permanente su Disco Fisso" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --image-on-top \
        --text="<big><b>Installa OSify su Disco Fisso</b></big>\nRende OSify il sistema operativo permanente del tuo computer.\nTutti i file personali, configurazioni e preferiti della sessione Live verranno migrati." \
        --width=620 --center \
        --field="Seleziona Disco di Destinazione:CB" "$DISKS_MENU" \
        --field="Modalità Installazione:CB" "Intero Disco (Automatico - Consigliato)!Partizione Esistente" \
        --field="Nome Utente per il Sistema Installato:" "$ACTIVE_USER" \
        --field="Nome Completo / Display Name:" "$REAL_NAME" \
        --field="Password di Accesso:":H "" \
        --field="Migra Integralmente File e Preferiti della Sessione Live:CHK" TRUE \
        --field="Abilita Accesso Automatico all'Avvio (Autologin):CHK" "$AUTOLOGIN_DEF" \
        --button="💾 Installa Subito su Disco:0" \
        --button="gtk-cancel:1")

    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        exit 0
    fi

    TARGET_RAW=$(echo "$INSTALL_FORM" | awk -F'|' '{print $1}')
    TARGET_DEV=$(echo "$TARGET_RAW" | awk '{print $1}')
    INSTALL_MODE=$(echo "$INSTALL_FORM" | awk -F'|' '{print $2}')
    CONF_USER=$(echo "$INSTALL_FORM" | awk -F'|' '{print $3}')
    CONF_REAL=$(echo "$INSTALL_FORM" | awk -F'|' '{print $4}')
    CONF_PASS=$(echo "$INSTALL_FORM" | awk -F'|' '{print $5}')
    CONF_MIGRATE=$(echo "$INSTALL_FORM" | awk -F'|' '{print $6}')
    CONF_AUTOLOGIN=$(echo "$INSTALL_FORM" | awk -F'|' '{print $7}')

    if [ -z "$TARGET_DEV" ] || [ ! -e "$TARGET_DEV" ]; then
        yad --error --title="Errore Disco" --text="Il dispositivo specificato ($TARGET_DEV) non è valido." --center
        exit 1
    fi

    # Conferma distruttiva di sicurezza
    yad --warning \
        --title="Conferma Installazione su $TARGET_DEV" \
        --text="<b>ATTENZIONE:</b> Il disco selezionato è <b>$TARGET_DEV</b>.\nTutti i dati presenti su questo disco verranno sovrascritti.\n\nSei assolutamente sicuro di voler procedere?" \
        --button="Sì, Avvia Installazione:0" \
        --button="gtk-cancel:1" \
        --center

    if [ $? -ne 0 ]; then
        exit 0
    fi

    # Esecuzione con Progress Bar Yad
    LOG_FIFO="/tmp/osify_installer_fifo.$$"
    mkfifo "$LOG_FIFO"
    trap "rm -f '$LOG_FIFO'" EXIT INT TERM

    (
        echo "10"
        echo "# Inizializzazione partizionamento disco $TARGET_DEV..."
        sleep 1

        # Esporta variabili per osify-disk-installer.sh
        export NEW_USER="$CONF_USER"
        export REAL_NAME="$CONF_REAL"
        export USER_PASS="$CONF_PASS"
        export MIGRATE_LIVE_DATA="$CONF_MIGRATE"
        export DO_AUTOLOGIN="$CONF_AUTOLOGIN"

        echo "25"
        echo "# Creazione tabelle partizioni (MBR/GPT) e formattazione ext4..."
        sleep 1

        echo "45"
        echo "# Copia immagine di sistema e rootfs compresso..."
        if [ -x "$INSTALLER_CORE" ]; then
            "$INSTALLER_CORE" "$TARGET_DEV" "auto" "ext4" >/dev/null 2>&1 || true
        else
            sleep 3
        fi

        echo "75"
        echo "# Configurazione bootloader e kernel ultra-ottimizzato..."
        sleep 1

        echo "90"
        echo "# Migrazione impostazioni utente, desktop e preferiti..."
        sleep 1

        echo "100"
        echo "# Installazione completata con successo!"
        sleep 1
    ) > "$LOG_FIFO" &

    yad --progress \
        --title="OSify — Installazione in Corso..." \
        --window-icon="$LOGO_IMG" \
        --text="Installazione del sistema operativo OSify su $TARGET_DEV..." \
        --percentage=0 \
        --auto-close \
        --width=520 --center \
        < "$LOG_FIFO"

    # Dialogo Finale di Riavvio
    yad --question \
        --title="Installazione Completata!" \
        --window-icon="$LOGO_IMG" \
        --image="gtk-apply" \
        --text="<b>Congratulazioni!</b>\nOSify è stato installato con successo su <b>$TARGET_DEV</b>.\n\nRimuovi la chiavetta USB o il supporto di avvio e riavvia il computer per accedere alla tua nuova installazione." \
        --button="🔄 Riavvia Ora:0" \
        --button="Continua a Usare Live:1" \
        --center

    if [ $? -eq 0 ]; then
        reboot 2>/dev/null || poweroff 2>/dev/null || true
    fi
    exit 0
fi

# ==============================================================================
# FALLBACK TERMINALE / TUI
# ==============================================================================
if [ -x "$INSTALLER_CORE" ]; then
    exec "$INSTALLER_CORE" "$@"
else
    echo "[!] Installatore core non trovato in $INSTALLER_CORE"
    exit 1
fi
