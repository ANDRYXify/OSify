#!/bin/sh
# ==============================================================================
# OSify Profile & Multi-User Setup Wizard (OOBE - Out Of Box Experience)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Si avvia automaticamente sia in Live che su sistema installato al primo avvio
# per consentire all'utente di definire la propria identità, permessi,
# credenziali crittografate, avatar, tema e preferenze hardware.
# ==============================================================================

CONFIG_DIR="${HOME:-/home/osify}/.config/osify"
FLAG_FILE="$CONFIG_DIR/profile_configured"
PROFILE_DATA="$CONFIG_DIR/profile.json"
mkdir -p "$CONFIG_DIR"

# Verifica se forzare la riconfigurazione (--reconfig / --force)
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force|--reconfig|-f) FORCE=1 ;;
    esac
done

if [ $FORCE -eq 0 ] && [ -f "$FLAG_FILE" ]; then
    exit 0
fi

# Auto-lancio in finestra grafica (Sakura/Xterm) se YAD non e' presente e non siamo in un terminale interattivo
if [ -n "$DISPLAY" ] && [ ! -t 0 ] && ! command -v yad >/dev/null 2>&1; then
    if command -v sakura >/dev/null 2>&1; then
        exec sakura -T "OSify — Configurazione Profilo Iniziale" -e "$0" "$@"
    elif command -v xterm >/dev/null 2>&1; then
        exec xterm -geometry 80x25 -T "OSify — Configurazione Profilo Iniziale" -e "$0" "$@"
    fi
fi

# Rilevamento ambiente e risoluzione
IS_LIVE=0
if grep -q "boot=live\|isolinux\|slitaz" /proc/cmdline 2>/dev/null || [ -d "/home/osify" ] || [ "$(whoami)" = "osify" ]; then
    IS_LIVE=1
fi

RES_INFO=$(xrandr 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1 || echo "1024x600")
IS_NETBOOK=0
if echo "$RES_INFO" | grep -qE "1024x600|1024x576|800x480"; then
    IS_NETBOOK=1
fi

# Icone e Avatar
DEFAULT_AVATARS_DIR="/usr/share/pixmaps"
USER_AVATAR="/usr/share/pixmaps/osify-avatar-cyber.png"
[ ! -f "$USER_AVATAR" ] && USER_AVATAR="/usr/share/pixmaps/osify-hub.png"

# ==============================================================================
# FUNZIONI DI APPLICAZIONE DEL PROFILO
# ==============================================================================
apply_profile() {
    _realname="$1"
    _username="$2"
    _password="$3"
    _is_admin="$4"
    _autologin="$5"
    _avatar_src="$6"
    _netbook_scaler="$7"
    _touchpad_opt="$8"
    _next_action="$9"

    [ -z "$_username" ] && _username="osify"
    [ -z "$_realname" ] && _realname="OSify User"

    # 1. Creazione o aggiornamento account utente
    if id "$_username" >/dev/null 2>&1; then
        # Utente già esistente: aggiorna GECOS e password
        if [ -n "$_password" ] && command -v chpasswd >/dev/null 2>&1; then
            echo "${_username}:${_password}" | chpasswd 2>/dev/null || true
        fi
    else
        # Nuovo utente: crea home e assegna gruppi
        if command -v adduser >/dev/null 2>&1; then
            adduser -D -s /bin/sh -g "$_realname" "$_username" 2>/dev/null || true
            if [ -n "$_password" ] && command -v chpasswd >/dev/null 2>&1; then
                echo "${_username}:${_password}" | chpasswd 2>/dev/null || true
            fi
        fi
    fi

    # 2. Gestione privilegi amministrativi (Sudoers / Wheel)
    if [ "$_is_admin" = "TRUE" ] || [ "$_is_admin" = "yes" ] || [ "$_is_admin" = "1" ]; then
        for grp in wheel sudo admin audio video disk storage input; do
            addgroup "$_username" "$grp" 2>/dev/null || true
        done
        if [ -w /etc/sudoers ]; then
            grep -q "^$_username " /etc/sudoers 2>/dev/null || echo "$_username ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
        fi
    fi

    # 3. Avatar Intelligente (Normalizzazione e copia automatica)
    TARGET_HOME=$(getent passwd "$_username" 2>/dev/null | cut -d: -f6)
    [ -z "$TARGET_HOME" ] && TARGET_HOME="/home/$_username"
    mkdir -p "$TARGET_HOME/.config/osify" "$TARGET_HOME/Desktop" "$TARGET_HOME/Documenti" "$TARGET_HOME/Download"

    if [ -n "$_avatar_src" ] && [ -f "$_avatar_src" ]; then
        if [ -x /usr/bin/osify-media-processor ]; then
            /usr/bin/osify-media-processor --avatar "$_avatar_src" "$TARGET_HOME/.face" 2>/dev/null || cp "$_avatar_src" "$TARGET_HOME/.face"
        else
            cp "$_avatar_src" "$TARGET_HOME/.face" 2>/dev/null || true
        fi
        cp "$TARGET_HOME/.face" "/usr/share/pixmaps/user-${_username}.png" 2>/dev/null || true
    fi

    # 4. Configurazione Autologin SLIM se richiesto
    if [ "$_autologin" = "TRUE" ] || [ "$_autologin" = "yes" ] || [ "$_autologin" = "1" ]; then
        if [ -f /etc/slim.conf ]; then
            sed -i "s/^default_user.*/default_user        $_username/" /etc/slim.conf 2>/dev/null || true
            sed -i "s/^auto_login.*/auto_login          yes/" /etc/slim.conf 2>/dev/null || true
        fi
    else
        if [ -f /etc/slim.conf ]; then
            sed -i "s/^auto_login.*/auto_login          no/" /etc/slim.conf 2>/dev/null || true
        fi
    fi

    # 5. Virtual Scaler Netbook se richiesto
    if [ "$_netbook_scaler" = "TRUE" ] || [ "$_netbook_scaler" = "yes" ] || [ "$_netbook_scaler" = "1" ]; then
        if [ -x /usr/bin/osify-hud ]; then
            /usr/bin/osify-hud --scale 2>/dev/null &
        elif command -v xrandr >/dev/null 2>&1; then
            OUTPUT_NAME=$(xrandr 2>/dev/null | grep ' connected' | awk '{print $1}' | head -n1 || echo "LVDS1")
            xrandr --output "$OUTPUT_NAME" --scale 1.25x1.28 --panning 1280x768 2>/dev/null || true
        fi
    fi

    # 6. Ottimizzazione Touchpad
    if [ "$_touchpad_opt" = "TRUE" ] || [ "$_touchpad_opt" = "yes" ] || [ "$_touchpad_opt" = "1" ]; then
        if [ -x /usr/bin/osify-input-setup ]; then
            /usr/bin/osify-input-setup 2>/dev/null &
        fi
    fi

    # 7. Salvataggio profilo JSON e flag di completamento
    cat << EOF > "$PROFILE_DATA"
{
  "real_name": "$_realname",
  "username": "$_username",
  "is_admin": "$_is_admin",
  "autologin": "$_autologin",
  "resolution": "$RES_INFO",
  "configured_at": "$(date '+%Y-%m-%d %H:%M:%S')"
}
EOF
    touch "$FLAG_FILE"
    [ -d "$TARGET_HOME" ] && cp "$FLAG_FILE" "$TARGET_HOME/.config/osify/" 2>/dev/null || true
    [ -d "$TARGET_HOME" ] && cp "$PROFILE_DATA" "$TARGET_HOME/.config/osify/" 2>/dev/null || true
    chown -R "$_username" "$TARGET_HOME" 2>/dev/null || true

    # 8. Azione successiva (Installazione su disco o avvio sessione)
    if [ "$_next_action" = "install" ]; then
        if [ -x /usr/bin/osify-install ]; then
            exec /usr/bin/osify-install
        fi
    fi
}

# ==============================================================================
# FRONTEND 1: YAD (GTK Nativo ad alte prestazioni, se disponibile in X11)
# ==============================================================================
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    LOGO_IMG="/usr/share/pixmaps/osify-hub.png"
    [ ! -f "$LOGO_IMG" ] && LOGO_IMG="/usr/share/pixmaps/osify.png"

    NETBOOK_DEFAULT="FALSE"
    [ $IS_NETBOOK -eq 1 ] && NETBOOK_DEFAULT="TRUE"

    FORM_OUT=$(yad --form \
        --title="OSify — Configurazione Iniziale Profilo & Identità" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --image-on-top \
        --text="<big><b>Benvenuto in OSify</b></big>\nConfigura il tuo account personale, le credenziali e le preferenze del sistema." \
        --width=580 --center \
        --field="Nome e Cognome (Display Name):" "Utente OSify" \
        --field="Nome Utente di Sistema (Username):" "osify" \
        --field="Password di Accesso:":H "" \
        --field="Conferma Password:":H "" \
        --field="Ruolo Utente (Privilegi Sudo):CHK" TRUE \
        --field="Accesso Automatico all'avvio (Autologin):CHK" TRUE \
        --field="Immagine Profilo / Avatar (Scegli file...):FL" "$USER_AVATAR" \
        --field="Attiva Virtual Scaler 1280x768 per Netbook (risolve finestre tagliate):CHK" "$NETBOOK_DEFAULT" \
        --field="Attiva Touchpad Universale (Edge Scrolling & Tap):CHK" TRUE \
        --button=" Installa Direttamente su Disco:2" \
        --button=" Inizia Sessione con Questo Profilo:0" \
        --button="gtk-cancel:1")

    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 1 ]; then
        exit 0
    fi

    # Parsing output YAD (separato da pipe '|')
    R_NAME=$(echo "$FORM_OUT" | awk -F'|' '{print $1}')
    U_NAME=$(echo "$FORM_OUT" | awk -F'|' '{print $2}')
    U_PASS=$(echo "$FORM_OUT" | awk -F'|' '{print $3}')
    U_CONF=$(echo "$FORM_OUT" | awk -F'|' '{print $4}')
    I_ADMIN=$(echo "$FORM_OUT" | awk -F'|' '{print $5}')
    A_LOGIN=$(echo "$FORM_OUT" | awk -F'|' '{print $6}')
    A_AVATAR=$(echo "$FORM_OUT" | awk -F'|' '{print $7}')
    N_SCALE=$(echo "$FORM_OUT" | awk -F'|' '{print $8}')
    T_PAD=$(echo "$FORM_OUT" | awk -F'|' '{print $9}')

    if [ -n "$U_PASS" ] && [ "$U_PASS" != "$U_CONF" ]; then
        yad --error --title="Errore Password" --text="Le due password inserite non coincidono. Riprova." --center
        exec "$0" --force
    fi

    NEXT_ACT="session"
    [ $EXIT_CODE -eq 2 ] && NEXT_ACT="install"

    apply_profile "$R_NAME" "$U_NAME" "$U_PASS" "$I_ADMIN" "$A_LOGIN" "$A_AVATAR" "$N_SCALE" "$T_PAD" "$NEXT_ACT"
    exit 0
fi

# ==============================================================================
# FRONTEND 2: DIALOG (TUI Elegante per Console o Xorg senza YAD)
# ==============================================================================
if command -v dialog >/dev/null 2>&1; then
    TMP_ANS="/tmp/osify_profile_ans.$$"
    dialog --backtitle "OSify Operating System" \
        --title " Configurazione Iniziale Profilo Utente " \
        --form "\nInserisci i dati del tuo profilo personale:\n" 18 64 0 \
        "Nome Completo:"     1 1 "Utente OSify"     1 20 36 0 \
        "Username:"          2 1 "osify"            2 20 20 0 \
        "Password:"          3 1 ""                 3 20 20 0 \
        "Amministratore (s/n):" 4 1 "s"             4 20 5 0 \
        "Autologin (s/n):"      5 1 "s"             5 20 5 0 \
        2> "$TMP_ANS"

    RET=$?
    if [ $RET -ne 0 ]; then
        rm -f "$TMP_ANS"
        exit 0
    fi

    R_NAME=$(sed -n '1p' "$TMP_ANS")
    U_NAME=$(sed -n '2p' "$TMP_ANS")
    U_PASS=$(sed -n '3p' "$TMP_ANS")
    I_ADMIN=$(sed -n '4p' "$TMP_ANS")
    A_LOGIN=$(sed -n '5p' "$TMP_ANS")
    rm -f "$TMP_ANS"

    [ "$I_ADMIN" = "s" ] || [ "$I_ADMIN" = "S" ] && I_ADMIN="TRUE" || I_ADMIN="FALSE"
    [ "$A_LOGIN" = "s" ] || [ "$A_LOGIN" = "S" ] && A_LOGIN="TRUE" || A_LOGIN="FALSE"

    apply_profile "$R_NAME" "$U_NAME" "$U_PASS" "$I_ADMIN" "$A_LOGIN" "" "FALSE" "TRUE" "session"
    exit 0
fi

# ==============================================================================
# FRONTEND 3: CLI SEMPLICE FALLBACK
# ==============================================================================
printf "\033[1;36m=== OSify Profile Initial Setup ===\033[0m\n"
apply_profile "Utente OSify" "osify" "" "TRUE" "TRUE" "" "FALSE" "TRUE" "session"
exit 0
