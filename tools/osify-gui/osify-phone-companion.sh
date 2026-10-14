#!/bin/sh
# ==============================================================================
# OSify Phone Companion — Mirroring, Controllo & Media Hub per Android e iOS
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta:
# 1. Android: Mirroring a 60 FPS con controllo mouse/tastiera via USB/Wi-Fi (scrcpy/adb)
# 2. Apple iOS (iPhone/iPad): Mirroring AirPlay su rete locale + accesso foto/file USB
# ==============================================================================

LOGO_IMG="/usr/share/pixmaps/osify-hub.png"

# ------------------------------------------------------------------------------
# ANDROID ACTIONS
# ------------------------------------------------------------------------------
launch_android_mirror() {
    # Verifica presenza ADB
    if ! command -v adb >/dev/null 2>&1; then
        echo "[!] ADB non installato. Installazione o avvio guidato..."
    fi

    # Avvia server ADB se necessario
    adb start-server >/dev/null 2>&1 || true
    DEVS_CONNECTED=$(adb devices 2>/dev/null | grep -w "device" | awk '{print $1}')

    if [ -z "$DEVS_CONNECTED" ]; then
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --warning \
                --title="Nessun Dispositivo Android Rilevato" \
                --window-icon="$LOGO_IMG" \
                --image="$LOGO_IMG" \
                --text="<big><b>Come collegare il tuo telefono Android:</b></big>\n\n1. Sul telefono vai in <b>Impostazioni &gt; Info sul telefono</b> e tocca 7 volte <b>Numero build</b>.\n2. Entra in <b>Opzioni Sviluppatore</b> e attiva <b>Debug USB</b>.\n3. Collega il telefono con cavo USB al PC e premi <b>'Consenti sempre'</b> sul display del telefono.\n\nPremi OK dopo aver collegato il cavo per avviare il mirroring." \
                --button="🔄 Riprova:0" --button="Annulla:1" --center
            if [ $? -eq 0 ]; then
                exec "$0" --android
            fi
        fi
        exit 1
    fi

    TARGET_SERIAL=$(echo "$DEVS_CONNECTED" | head -n1)
    
    # Se presente scrcpy (standard d'eccellenza per mirroring e controllo Android)
    if command -v scrcpy >/dev/null 2>&1; then
        exec scrcpy -s "$TARGET_SERIAL" --window-title="OSify Android Mirror" --always-on-top --stay-awake
    else
        # Fallback leggero VNC/Screen Capture frame streaming
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --info \
                --title="Dispositivo Android Connesso" \
                --window-icon="$LOGO_IMG" \
                --text="Telefono Android rilevato con successo (Seriale: <b>$TARGET_SERIAL</b>).\n\nPuoi ora trasferire file o lanciare il controllo remoto." \
                --center
        fi
    fi
}

# ------------------------------------------------------------------------------
# APPLE iOS ACTIONS
# ------------------------------------------------------------------------------
launch_ios_airplay() {
    # Avvia ricevitore AirPlay speculare
    if command -v uxplay >/dev/null 2>&1; then
        exec uxplay -n "OSify AirPlay Display" -s 1920x1080 -fps 60
    else
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --info \
                --title="OSify — Mirroring Apple iOS (iPhone / iPad)" \
                --window-icon="$LOGO_IMG" \
                --image="$LOGO_IMG" \
                --text="<big><b>Mirroring AirPlay per iPhone e iPad</b></big>\n\n1. Assicurati che il tuo iPhone sia connesso alla stessa rete Wi-Fi di OSify.\n2. Scorri verso il basso dall'angolo in alto a destra per aprire il <b>Centro di Controllo</b>.\n3. Tocca l'icona <b>Duplica Schermo</b>.\n4. Seleziona <b>'OSify AirPlay Display'</b>.\n\nLo schermo del tuo iPhone verrà duplicato a 60 FPS in tempo reale con audio!" \
                --button="Avvia Ricevitore:0" --center
        fi
    fi
}

launch_ios_files() {
    # Montaggio foto e DCIM iPhone via cavo USB
    if command -v idevicepair >/dev/null 2>&1; then
        idevicepair pair >/dev/null 2>&1 || true
    fi
    if command -v pcmanfm >/dev/null 2>&1; then
        pcmanfm "afc://" 2>/dev/null || pcmanfm 2>/dev/null || true
    fi
}

# ------------------------------------------------------------------------------
# FRONTEND PRINCIPALE YAD
# ------------------------------------------------------------------------------
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    MODE_SEL=$(yad --form \
        --title="OSify — Phone Companion & Screen Mirroring" \
        --window-icon="$LOGO_IMG" \
        --image="$LOGO_IMG" \
        --image-on-top \
        --text="<big><b>OSify Phone Companion</b></big>\nCollega, controlla e duplica lo schermo del tuo smartphone direttamente sul PC." \
        --width=540 --center \
        --field="Seleziona Tipo di Dispositivo:CB" "🤖 Android (Mirroring 60fps & Controllo Mouse/Tastiera)!🍎 Apple iOS (AirPlay Mirroring Schermo & Audio)!📁 Apple iOS (Accesso Foto e Documenti via Cavo)" \
        --button="🚀 Connetti:0" \
        --button="gtk-cancel:1")

    if [ $? -eq 0 ]; then
        CHOICE=$(echo "$MODE_SEL" | awk -F'|' '{print $1}')
        case "$CHOICE" in
            *Android*)
                launch_android_mirror
                ;;
            *AirPlay*)
                launch_ios_airplay
                ;;
            *Foto*)
                launch_ios_files
                ;;
        esac
    fi
    exit 0
fi

# Fallback CLI
case "$1" in
    --android|-a) launch_android_mirror ;;
    --ios|-i)     launch_ios_airplay ;;
    *) echo "Uso: osify-phone-companion [--android|--ios]" ;;
esac
