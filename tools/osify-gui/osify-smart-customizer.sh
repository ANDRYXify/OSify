#!/bin/sh
# ==============================================================================
# OSify Smart Customizer — Personalizzazione Grafica Completa & Automatica
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestisce autonomamente sfondi, avatar, risoluzione netbook, temi e navbar
# sollevando l'utente da qualsiasi calcolo di proporzioni o formati.
# ==============================================================================

LOGO_IMG="/usr/share/pixmaps/osify-appearance.png"
[ ! -f "$LOGO_IMG" ] && LOGO_IMG="/usr/share/pixmaps/osify-hub.png"

CONFIG_DIR="${HOME:-/home/osify}/.config/osify"
mkdir -p "$CONFIG_DIR"

APPLY_WALLPAPER() {
    _src="$1"
    _mode="${2:-smart_blur}"
    [ ! -f "$_src" ] && return

    TARGET_JPG="$CONFIG_DIR/current-wallpaper.jpg"
    SYS_JPG="/usr/share/images/osify-wallpaper.jpg"

    # Elaborazione automatica proporzioni e risoluzione
    if [ -x /usr/bin/osify-media-processor ]; then
        /usr/bin/osify-media-processor --wallpaper "$_src" "$TARGET_JPG" "$_mode"
    else
        cp -f "$_src" "$TARGET_JPG"
    fi

    # Copia di sistema se siamo root
    if [ -w /usr/share/images ]; then
        cp -f "$TARGET_JPG" "$SYS_JPG" 2>/dev/null || true
    fi

    # Applicazione istantanea a PCManFM
    if command -v pcmanfm >/dev/null 2>&1; then
        pcmanfm --set-wallpaper="$TARGET_JPG" --wallpaper-mode=stretch 2>/dev/null || true
    fi

    # Applicazione a Openbox / feh
    if command -v feh >/dev/null 2>&1; then
        feh --bg-fill "$TARGET_JPG" 2>/dev/null || true
    fi
}

APPLY_AVATAR() {
    _src="$1"
    [ ! -f "$_src" ] && return

    TARGET_FACE="${HOME:-/home/osify}/.face"
    if [ -x /usr/bin/osify-media-processor ]; then
        /usr/bin/osify-media-processor --avatar "$_src" "$TARGET_FACE"
    else
        cp -f "$_src" "$TARGET_FACE"
    fi
}

# ==============================================================================
# FRONTEND GRAFICO YAD (GTK)
# ==============================================================================
if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
    while true; do
        ACTION=$(yad --list \
            --title="OSify — Centro di Personalizzazione & Aspetto" \
            --window-icon="$LOGO_IMG" \
            --image="$LOGO_IMG" \
            --text="<big><b>Personalizzazione Grafica OSify</b></big>\nPersonalizza ogni elemento del sistema. Il motore interno adatta automaticamente formati e dimensioni." \
            --width=580 --height=340 --center \
            --column="ID" --column="Opzione" --column="Descrizione" \
            "1" "  Imposta Nuovo Sfondo" "Scegli qualsiasi immagine: il motore la adatta a zero distorsione" \
            "2" "  Cambia Avatar Utente" "Ritaglia e normalizza automaticamente una foto personale" \
            "3" "  Virtual Scaler Schermo" "Ingrandisci la scrivania a 1280x768 per Netbook 1024x600" \
            "4" "  Palette Cromatica" "Seleziona colore accento (Cyber Ciano, Viola, Menta, Ambra)" \
            "5" "  Touchpad & Puntatore" "Regola velocità, tap-to-click ed edge-scrolling" \
            --button="Seleziona:0" --button="gtk-close:1")

        EXIT_CODE=$?
        [ $EXIT_CODE -ne 0 ] && break

        OPT=$(echo "$ACTION" | awk -F'|' '{print $1}')

        case "$OPT" in
            1) # Sfondo
                WALL_FORM=$(yad --form \
                    --title="Imposta Sfondo Desktop" \
                    --window-icon="$LOGO_IMG" \
                    --text="Scegli qualsiasi file immagine dal computer o chiavetta USB:" \
                    --width=520 --center \
                    --field="File Immagine:FL" "" \
                    --field="Modalità Adattamento:CB" "Smart Bokeh (Zero distorsione + bordi sfocati)!Riempi Schermo (Smart Crop)!Stretch Diretto" \
                    --button="Applica Sfondo:0" --button="Annulla:1")
                if [ $? -eq 0 ]; then
                    IMG_FILE=$(echo "$WALL_FORM" | awk -F'|' '{print $1}')
                    M_CHOSEN=$(echo "$WALL_FORM" | awk -F'|' '{print $2}')
                    
                    MODE_PARAM="smart_blur"
                    echo "$M_CHOSEN" | grep -q "Crop" && MODE_PARAM="crop"
                    echo "$M_CHOSEN" | grep -q "Stretch" && MODE_PARAM="stretch"

                    if [ -f "$IMG_FILE" ]; then
                        APPLY_WALLPAPER "$IMG_FILE" "$MODE_PARAM"
                        yad --info --title="Completato" --text="Nuovo sfondo applicato con successo!" --center
                    fi
                fi
                ;;

            2) # Avatar
                AVATAR_FILE=$(yad --file \
                    --title="Seleziona la tua Foto Profilo" \
                    --window-icon="$LOGO_IMG" \
                    --text="Scegli una qualsiasi foto da convertire in avatar:" \
                    --width=500 --center)
                if [ -n "$AVATAR_FILE" ] && [ -f "$AVATAR_FILE" ]; then
                    APPLY_AVATAR "$AVATAR_FILE"
                    yad --info --title="Avatar Aggiornato" --text="La tua foto profilo è stata normalizzata e applicata!" --center
                fi
                ;;

            3) # Virtual Scaler
                if [ -x /usr/bin/osify-hud ]; then
                    /usr/bin/osify-hud --toggle-scale
                else
                    CUR_RES=$(xrandr 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1)
                    if echo "$CUR_RES" | grep -q "1024x600"; then
                        OUTPUT_NAME=$(xrandr 2>/dev/null | grep ' connected' | awk '{print $1}' | head -n1 || echo "LVDS1")
                        xrandr --output "$OUTPUT_NAME" --scale 1.25x1.28 --panning 1280x768 2>/dev/null || true
                        yad --info --title="Scaler Attivo" --text="Risoluzione virtuale estesa a 1280x768." --center
                    else
                        OUTPUT_NAME=$(xrandr 2>/dev/null | grep ' connected' | awk '{print $1}' | head -n1 || echo "LVDS1")
                        xrandr --output "$OUTPUT_NAME" --scale 1.0x1.0 --panning 0x0 2>/dev/null || true
                        yad --info --title="Risoluzione Nativa" --text="Ripristinata risoluzione nativa 1024x600." --center
                    fi
                fi
                ;;

            4) # Palette Cromatica
                COLOR_CHOSEN=$(yad --list \
                    --title="Seleziona Tema Cromatico" \
                    --window-icon="$LOGO_IMG" \
                    --column="Colore" --column="Codice" --column="Nome" \
                    "Ciano Neon" "#06b6d4" "Cyberpunk Original" \
                    "Viola Obsidian" "#8b5cf6" "Dark Glow" \
                    "Verde Smeraldo" "#10b981" "Matrix High-Tech" \
                    "Ambra Solare" "#f59e0b" "Warm Contrast" \
                    "OLED Puro" "#000000" "Zero Battery Dark" \
                    --width=420 --height=260 --center)
                if [ $? -eq 0 ]; then
                    C_HEX=$(echo "$COLOR_CHOSEN" | awk -F'|' '{print $2}')
                    echo "$C_HEX" > "$CONFIG_DIR/accent_color.txt"
                    yad --info --title="Colore Aggiornato" --text="Colore accento <b>$C_HEX</b> salvato." --center
                fi
                ;;

            5) # Touchpad
                if [ -x /usr/bin/osify-input ]; then
                    /usr/bin/osify-input
                elif [ -x /usr/bin/osify-input-setup ]; then
                    /usr/bin/osify-input-setup
                    yad --info --title="Input Ottimizzato" --text="Touchpad configurato con Edge-Scrolling e Tap." --center
                fi
                ;;
        esac
    done
    exit 0
fi

# Fallback CLI
echo "=== OSify Smart Customizer ==="
APPLY_WALLPAPER "/usr/share/images/osify-wallpaper.jpg" "smart_blur"
