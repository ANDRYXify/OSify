#!/bin/sh
# ==============================================================================
# OSify Multi-User & Accounts Management Suite
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestione professionale multiutenza: creazione account, eliminazione sicura,
# gestione privilegi amministrativi (sudoers/wheel), modifica password e avatar.
# ==============================================================================

# Verifica privilegi di root / auto-elevazione
if [ "$(id -u 2>/dev/null || echo 0)" -ne 0 ]; then
    if command -v subox >/dev/null 2>&1; then
        exec subox "$0" "$@"
    elif command -v sudo >/dev/null 2>&1; then
        exec sudo "$0" "$@"
    else
        echo "[!] Privilegi di root richiesti per la gestione utenti."
        exit 1
    fi
fi

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"
[ ! -f "$LOGO_IMG" ] && LOGO_IMG="/usr/share/pixmaps/osify.png"

list_users() {
    awk -F: '$3 >= 1000 && $3 < 60000 {print $1, "(" $5 ")", "UID:" $3}' /etc/passwd 2>/dev/null || echo "osify (OSify User) UID:1000"
}

# ==============================================================================
# FRONTEND YAD (GTK Grafico)
# ==============================================================================
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    while true; do
        USERS_LIST=$(awk -F: '$3 >= 1000 && $3 < 60000 {
            admin = "No";
            cmd = "id -Gn " $1 " 2>/dev/null";
            cmd | getline grps;
            close(cmd);
            if (grps ~ /(wheel|sudo|admin)/) admin = "Sì (Admin)";
            printf "%s!%s!%s!%s!", $1, ($5 ? $5 : $1), $3, admin
        }' /etc/passwd)

        CHOICE=$(yad --list \
            --title="OSify — Gestore Multiutenza & Account di Sistema" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Gestore Multiutenza OSify</b></big>\nGestisci gli account utenti, le password e i permessi di amministrazione." \
            --width=620 --height=380 --center \
            --column="Username" --column="Nome Completo" --column="UID" --column="Privilegi" \
            $(echo "$USERS_LIST" | tr '!' '\n') \
            --button="➕ Nuovo Utente:2" \
            --button="🔑 Cambia Password:3" \
            --button="🛡️ Toggle Privilegi Admin:4" \
            --button="🗑️ Elimina Utente:5" \
            --button="gtk-close:0")

        EXIT_CODE=$?
        [ $EXIT_CODE -eq 0 ] && break

        SELECTED_USER=$(echo "$CHOICE" | awk -F'|' '{print $1}')

        case $EXIT_CODE in
            2) # Nuovo Utente
                NEW_DATA=$(yad --form \
                    --title="Crea Nuovo Account Utente" \
                    --window-icon="$LOGO_IMG" \
                    --text="Inserisci i dettagli del nuovo utente:" \
                    --width=420 --center \
                    --field="Username:":TEXT "" \
                    --field="Nome Completo:":TEXT "" \
                    --field="Password:":H "" \
                    --field="Conferma Password:":H "" \
                    --field="Privilegi Amministratore (Sudo):CHK" TRUE \
                    --button="Crea:0" --button="Annulla:1")
                if [ $? -eq 0 ]; then
                    N_USER=$(echo "$NEW_DATA" | awk -F'|' '{print $1}' | tr -d ' ')
                    N_REAL=$(echo "$NEW_DATA" | awk -F'|' '{print $2}')
                    N_PASS=$(echo "$NEW_DATA" | awk -F'|' '{print $3}')
                    N_CONF=$(echo "$NEW_DATA" | awk -F'|' '{print $4}')
                    N_ADMIN=$(echo "$NEW_DATA" | awk -F'|' '{print $5}')

                    if [ -z "$N_USER" ]; then
                        yad --error --title="Errore" --text="Lo username non può essere vuoto." --center
                        continue
                    fi
                    if [ "$N_PASS" != "$N_CONF" ]; then
                        yad --error --title="Errore" --text="Le password non coincidono." --center
                        continue
                    fi

                    adduser -D -s /bin/sh -g "$N_REAL" "$N_USER" 2>/dev/null || adduser -m -s /bin/sh -c "$N_REAL" "$N_USER" 2>/dev/null || true
                    if [ -n "$N_PASS" ] && command -v chpasswd >/dev/null 2>&1; then
                        echo "${N_USER}:${N_PASS}" | chpasswd 2>/dev/null || true
                    fi

                    if [ "$N_ADMIN" = "TRUE" ]; then
                        for g in wheel sudo admin audio video disk storage input; do
                            addgroup "$N_USER" "$g" 2>/dev/null || true
                        done
                        echo "$N_USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers 2>/dev/null || true
                    fi

                    yad --info --title="Completato" --text="Utente <b>$N_USER</b> creato con successo!" --center
                fi
                ;;

            3) # Cambia Password
                if [ -z "$SELECTED_USER" ]; then
                    yad --warning --title="Attenzione" --text="Seleziona un utente dalla lista prima di procedere." --center
                    continue
                fi
                PASS_DATA=$(yad --form \
                    --title="Cambia Password per $SELECTED_USER" \
                    --window-icon="$LOGO_IMG" \
                    --text="Inserisci la nuova password per <b>$SELECTED_USER</b>:" \
                    --width=380 --center \
                    --field="Nuova Password:":H "" \
                    --field="Conferma Password:":H "" \
                    --button="Aggiorna:0" --button="Annulla:1")
                if [ $? -eq 0 ]; then
                    P1=$(echo "$PASS_DATA" | awk -F'|' '{print $1}')
                    P2=$(echo "$PASS_DATA" | awk -F'|' '{print $2}')
                    if [ "$P1" != "$P2" ]; then
                        yad --error --title="Errore" --text="Le password non coincidono." --center
                        continue
                    fi
                    if [ -n "$P1" ] && command -v chpasswd >/dev/null 2>&1; then
                        echo "${SELECTED_USER}:${P1}" | chpasswd 2>/dev/null || true
                        yad --info --title="Completato" --text="Password per <b>$SELECTED_USER</b> aggiornata!" --center
                    fi
                fi
                ;;

            4) # Toggle Privilegi Admin
                if [ -z "$SELECTED_USER" ]; then
                    yad --warning --title="Attenzione" --text="Seleziona un utente dalla lista." --center
                    continue
                fi
                if id -Gn "$SELECTED_USER" 2>/dev/null | grep -qE "wheel|sudo|admin"; then
                    # Rimuovi privilegi
                    delgroup "$SELECTED_USER" wheel 2>/dev/null || gpasswd -d "$SELECTED_USER" wheel 2>/dev/null || true
                    delgroup "$SELECTED_USER" sudo 2>/dev/null || gpasswd -d "$SELECTED_USER" sudo 2>/dev/null || true
                    sed -i "/^$SELECTED_USER /d" /etc/sudoers 2>/dev/null || true
                    yad --info --title="Privilegi Aggiornati" --text="L'utente <b>$SELECTED_USER</b> ora ha privilegi di <b>Utente Standard</b>." --center
                else
                    # Aggiungi privilegi
                    for g in wheel sudo admin audio video disk storage input; do
                        addgroup "$SELECTED_USER" "$g" 2>/dev/null || true
                    done
                    grep -q "^$SELECTED_USER " /etc/sudoers 2>/dev/null || echo "$SELECTED_USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers 2>/dev/null || true
                    yad --info --title="Privilegi Aggiornati" --text="L'utente <b>$SELECTED_USER</b> ora è un <b>Amministratore di Sistema</b>." --center
                fi
                ;;

            5) # Elimina Utente
                if [ -z "$SELECTED_USER" ]; then
                    yad --warning --title="Attenzione" --text="Seleziona un utente da eliminare." --center
                    continue
                fi
                if [ "$SELECTED_USER" = "root" ] || [ "$SELECTED_USER" = "$(whoami)" ]; then
                    yad --error --title="Operazione Negata" --text="Non puoi eliminare l'utente attualmente in uso ($SELECTED_USER)." --center
                    continue
                fi
                yad --question \
                    --title="Conferma Eliminazione" \
                    --text="Sei sicuro di voler eliminare l'account <b>$SELECTED_USER</b>?\nI suoi dati personali verranno rimossi." \
                    --center
                if [ $? -eq 0 ]; then
                    deluser --remove-home "$SELECTED_USER" 2>/dev/null || deluser "$SELECTED_USER" 2>/dev/null || userdel -r "$SELECTED_USER" 2>/dev/null || true
                    sed -i "/^$SELECTED_USER /d" /etc/sudoers 2>/dev/null || true
                    yad --info --title="Eliminato" --text="L'utente <b>$SELECTED_USER</b> è stato rimosso." --center
                fi
                ;;
        esac
    done
    exit 0
fi

# Fallback CLI/TTY
echo "=== Gestore Multiutenza OSify ==="
list_users
