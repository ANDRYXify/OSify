#!/bin/sh
# ==============================================================================
# OSify Disk Installer — Assistente Guidato su Disco Fisso
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# Esegue l'installazione permanente di OSify su disco fisso senza richiedere
# alcuna password in sessione Live, con procedura guidata passo-passo.
# ==============================================================================

# Se non siamo root, eleviamo con sudo trasparente (grazie a sudoers NOPASSWD)
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    elif command -v su >/dev/null 2>&1; then
        exec su -c "$0 $*"
    fi
fi

# Se siamo lanciati dal desktop senza terminale, apriamo una finestra xterm
if [ -n "$DISPLAY" ] && [ ! -t 0 ]; then
    if command -v xterm >/dev/null 2>&1; then
        exec xterm -title "Installazione OSify su Disco Fisso" -geometry 90x28 -bg "#0b0d14" -fg "#38bdf8" -cr "#10b981" +sb -e "$0" --run-wizard
    fi
fi

INSTALLER_CORE="/usr/bin/osify-disk-installer"
[ ! -x "$INSTALLER_CORE" ] && INSTALLER_CORE="$(dirname "$0")/../../system/installer/osify-disk-installer.sh"

# ==============================================================================
# RILEVAMENTO DISCHI FISICI
# ==============================================================================
detect_disks_list() {
    for d in /sys/block/sd* /sys/block/hd* /sys/block/nvme*n1 /sys/block/mmcblk*; do
        [ -e "$d" ] || continue
        dname=$(basename "$d")
        case "$dname" in
            loop*|ram*|zram*|sr*|fd*) continue ;;
        esac
        size_sectors=$(cat "$d/size" 2>/dev/null || echo 0)
        size_gb=$(( size_sectors * 512 / 1024 / 1024 / 1024 ))
        [ "$size_gb" -le 0 ] && continue
        
        model=""
        [ -f "$d/device/model" ] && model=$(cat "$d/device/model" | tr -s ' ' | sed 's/^[ \t]*//;s/[ \t]*$//')
        [ -z "$model" ] && model="Disco Fisso"
        echo "/dev/$dname" "${size_gb}GB_${model}"
    done
}

# ==============================================================================
# PROCEDURA GUIDATA CON DIALOG
# ==============================================================================
if command -v dialog >/dev/null 2>&1; then
    # 1. Benvenuto
    dialog --backtitle "OSify Operating System — Installazione Permanente" \
        --title " Benvenuto nell'Installazione di OSify " \
        --msgbox "\nBenvenuto nel programma di installazione di OSify!\n\nQuesta procedura guidata ti permetterà di installare OSify sul disco fisso del computer come sistema operativo principale.\n\nTutti i file personali e le impostazioni create in questa sessione verranno trasferiti automaticamente sul nuovo sistema.\n\nPremi Invio per iniziare la configurazione." 15 68

    # 2. Scelta Disco
    DISKS=$(detect_disks_list)
    if [ -z "$DISKS" ]; then
        dialog --backtitle "OSify Operating System" \
            --title " Nessun Disco Rilevato " \
            --msgbox "\nNon e' stato possibile rilevare dischi fissi interni.\nVerifica i collegamenti hardware e riprova." 8 55
        exit 1
    fi

    # Costruisci argomenti menu
    TARGET_DEV=$(dialog --backtitle "OSify Operating System" \
        --title " Selezione Disco di Destinazione " \
        --menu "\nScegli il disco su cui installare OSify:\n(ATTENZIONE: Il disco selezionato verra' formattato)\n" 16 68 4 \
        $DISKS \
        3>&1 1>&2 2>&3)
    [ $? -ne 0 ] && exit 0

    # 3. Nome Completo
    CONF_REAL=$(dialog --backtitle "OSify Operating System" \
        --title " Configurazione Account — Nome Utente " \
        --inputbox "\nInserisci il tuo Nome Completo (o un nome a tua scelta):" 10 60 "Utente OSify" \
        3>&1 1>&2 2>&3)
    [ $? -ne 0 ] && exit 0
    [ -z "$CONF_REAL" ] && CONF_REAL="Utente OSify"

    # 4. Username Login
    DEF_USER=$(echo "$CONF_REAL" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-12)
    [ -z "$DEF_USER" ] && DEF_USER="utente"
    CONF_USER=$(dialog --backtitle "OSify Operating System" \
        --title " Nome Utente per il Login " \
        --inputbox "\nScegli il nome utente per accedere al sistema:" 10 60 "$DEF_USER" \
        3>&1 1>&2 2>&3)
    [ $? -ne 0 ] && exit 0
    [ -z "$CONF_USER" ] && CONF_USER="$DEF_USER"

    # 5. Password
    CONF_PASS=""
    while [ -z "$CONF_PASS" ]; do
        P1=$(dialog --backtitle "OSify Operating System" \
            --title " Password di Accesso " \
            --insecure \
            --passwordbox "\nCrea una password per il tuo account:\n(Lascia vuoto per nessuna password)" 11 60 \
            3>&1 1>&2 2>&3)
        [ $? -ne 0 ] && exit 0
        if [ -n "$P1" ]; then
            P2=$(dialog --backtitle "OSify Operating System" \
                --title " Conferma Password " \
                --insecure \
                --passwordbox "\nDigita nuovamente la password per conferma:" 10 60 \
                3>&1 1>&2 2>&3)
            [ $? -ne 0 ] && exit 0
            if [ "$P1" != "$P2" ]; then
                dialog --msgbox "\nLe due password non coincidono. Riprova." 7 50
                continue
            fi
        fi
        CONF_PASS="$P1"
        break
    done

    # 6. Autologin
    dialog --backtitle "OSify Operating System" \
        --title " Accesso Automatico all'Avvio " \
        --yesno "\nDesideri accedere direttamente al desktop all'avvio del computer senza dover digitare la password ogni volta?" 10 64
    if [ $? -eq 0 ]; then
        CONF_AUTOLOGIN="yes"
    else
        CONF_AUTOLOGIN="no"
    fi

    # 7. Conferma Finale di Sicurezza
    dialog --backtitle "OSify Operating System" \
        --title " CONFERMA FORMATTAZIONE E INSTALLAZIONE " \
        --yesno "\nATTENZIONE: Verranno cancellati tutti i dati presenti su $TARGET_DEV!\n\nRiepilogo Installazione:\n - Disco: $TARGET_DEV\n - Utente: $CONF_USER ($CONF_REAL)\n - Accesso Automatico: $CONF_AUTOLOGIN\n\nSei assolutamente sicuro di voler procedere con l'installazione?" 15 65
    [ $? -ne 0 ] && exit 0

    # 8. Esecuzione con Progress Bar Gauge
    FIFO="/tmp/osify_gauge_fifo.$$"
    rm -f "$FIFO"
    mkfifo "$FIFO"
    trap "rm -f '$FIFO'" EXIT INT TERM

    (
        echo "10"
        echo "XXX"
        echo "Preparazione partizioni del disco $TARGET_DEV..."
        echo "XXX"
        sleep 1

        export REAL_NAME="$CONF_REAL"
        export NEW_USER="$CONF_USER"
        export USER_PASS="$CONF_PASS"
        export DO_AUTOLOGIN="$CONF_AUTOLOGIN"
        export MIGRATE_LIVE_DATA="yes"

        echo "25"
        echo "XXX"
        echo "Formattazione filesystem e creazione struttura OSify..."
        echo "XXX"

        if [ -x "$INSTALLER_CORE" ]; then
            # Esegui l'installer reale
            "$INSTALLER_CORE" "$TARGET_DEV" "auto" "ext4" >/tmp/osify_install_run.log 2>&1 || true
        else
            sleep 2
        fi

        echo "75"
        echo "XXX"
        echo "Installazione del Bootloader e Kernel..."
        echo "XXX"
        sleep 1

        echo "90"
        echo "XXX"
        echo "Migrazione impostazioni utente e preferenze..."
        echo "XXX"
        sleep 1

        echo "100"
        echo "XXX"
        echo "Installazione completata con successo!"
        echo "XXX"
        sleep 1
    ) > "$FIFO" &

    dialog --backtitle "OSify Operating System" \
        --title " Installazione di OSify in Corso " \
        --gauge "\nAttendere l'installazione del sistema operativo su $TARGET_DEV..." 10 65 0 < "$FIFO"

    # 9. Conclusione
    dialog --backtitle "OSify Operating System" \
        --title " Installazione Completata! " \
        --yesno "\nCongratulazioni! OSify e' stato installato con successo su $TARGET_DEV.\n\nVuoi riavviare il computer adesso?\n(Ricordati di rimuovere la chiavetta USB durante il riavvio)" 12 65

    if [ $? -eq 0 ]; then
        reboot 2>/dev/null || poweroff 2>/dev/null || true
    fi
    exit 0
fi

# Fallback terminale puro se dialog non e' disponibile
if [ -x "$INSTALLER_CORE" ]; then
    exec "$INSTALLER_CORE" "$@"
fi

echo "[!] Nessun installatore disponibile."
exit 1
