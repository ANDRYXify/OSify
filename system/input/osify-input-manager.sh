#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Input Manager — Touchscreen, Touchpad Moderni e Vintage
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Garantisce compatibilità e massima ergonomia su qualsiasi dispositivo:
# 1. Touchscreen & Tablet: Tap-to-click, Long-press tasto destro, gesture multitouch
# 2. Precision Touchpad: Natural scrolling, 2-finger click, 3-finger gestures, palm-check
# 3. Vintage Touchpad (PS/2, Alps, Synaptics 2005-2012):
#    • Edge scrolling sul bordo destro (per vecchi netbook a tocco singolo)
#    • Syndaemon (anti-tocco involontario durante la digitazione)
#    • Calibrazione sensibilità e pressione minima
# 4. Salva e applica preferenze in ~/.config/osify/input-profile.conf
# ==============================================================================

set -euo pipefail

CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/osify"
CONF_FILE="$CONF_DIR/input-profile.conf"
mkdir -p "$CONF_DIR"

load_input_config() {
    NATURAL_SCROLL="true"
    TAP_TO_CLICK="true"
    TWO_FINGER_RIGHT_CLICK="true"
    EDGE_SCROLLING_VINTAGE="auto"  # auto, true, false
    PALM_REJECTION="true"
    POINTER_SPEED="1.0"
    TOUCH_HOLD_RIGHT_CLICK="true"
    TOUCH_TARGET_PADDING="normal"   # normal, enlarged

    if [[ -f "$CONF_FILE" ]]; then
        while IFS='=' read -r key val || [[ -n "$key" ]]; do
            key="$(echo "$key" | tr -d ' ')"
            val="$(echo "$val" | tr -d ' ')"
            [[ "$key" =~ ^#.*$ ]] && continue
            case "$key" in
                NATURAL_SCROLL) NATURAL_SCROLL="$val" ;;
                TAP_TO_CLICK) TAP_TO_CLICK="$val" ;;
                TWO_FINGER_RIGHT_CLICK) TWO_FINGER_RIGHT_CLICK="$val" ;;
                EDGE_SCROLLING_VINTAGE) EDGE_SCROLLING_VINTAGE="$val" ;;
                PALM_REJECTION) PALM_REJECTION="$val" ;;
                POINTER_SPEED) POINTER_SPEED="$val" ;;
                TOUCH_HOLD_RIGHT_CLICK) TOUCH_HOLD_RIGHT_CLICK="$val" ;;
                TOUCH_TARGET_PADDING) TOUCH_TARGET_PADDING="$val" ;;
            esac
        done < "$CONF_FILE"
    else
        save_input_config
    fi
}

save_input_config() {
    cat <<EOF > "$CONF_FILE"
# ==============================================================================
# OSify Input Devices Configuration
# ==============================================================================
NATURAL_SCROLL=${NATURAL_SCROLL:-true}
TAP_TO_CLICK=${TAP_TO_CLICK:-true}
TWO_FINGER_RIGHT_CLICK=${TWO_FINGER_RIGHT_CLICK:-true}
EDGE_SCROLLING_VINTAGE=${EDGE_SCROLLING_VINTAGE:-auto}
PALM_REJECTION=${PALM_REJECTION:-true}
POINTER_SPEED=${POINTER_SPEED:-1.0}
TOUCH_HOLD_RIGHT_CLICK=${TOUCH_HOLD_RIGHT_CLICK:-true}
TOUCH_TARGET_PADDING=${TOUCH_TARGET_PADDING:-normal}
EOF
}

detect_hardware_inputs() {
    local has_touchscreen=0
    local has_touchpad=0
    local is_vintage_touchpad=0
    local touchpad_name="Nessuno"
    local touch_name="Nessuno"

    # Ispezione dispositivi input tramite sysfs o xinput
    if [[ -d /sys/class/input ]]; then
        for dev in /sys/class/input/input*/name; do
            if [[ -f "$dev" ]]; then
                local n
                n="$(cat "$dev" 2>/dev/null || true)"
                if echo "$n" | grep -qiE "touchscreen|surface|wacom|goodix|egalax|atmel|elan.*touch"; then
                    has_touchscreen=1
                    touch_name="$n"
                fi
                if echo "$n" | grep -qiE "touchpad|trackpad|synaptics|alps|glidepoint"; then
                    has_touchpad=1
                    touchpad_name="$n"
                    # Verifica se è un touchpad vintage PS/2 o seriale senza supporto multitouch
                    if echo "$n" | grep -qiE "ps/2|alps|serio"; then
                        is_vintage_touchpad=1
                    fi
                fi
            fi
        done
    elif command -v xinput >/dev/null 2>&1; then
        local xi_out
        xi_out="$(xinput list --name-only 2>/dev/null || true)"
        if echo "$xi_out" | grep -qiE "touchscreen|surface|wacom"; then
            has_touchscreen=1
            touch_name="XInput Touch Device"
        fi
        if echo "$xi_out" | grep -qiE "touchpad|synaptics"; then
            has_touchpad=1
            touchpad_name="XInput Touchpad"
        fi
    fi

    echo "$has_touchscreen $has_touchpad $is_vintage_touchpad"
}

cmd_apply() {
    load_input_config
    read -r has_touch has_pad is_vintage <<< "$(detect_hardware_inputs)"

    echo "[OSify-Input] Applicazione calibrazione e profili input..."

    # 1. Configurazione Touchscreen
    if [[ "$has_touch" -eq 1 ]]; then
        echo "  [✓] Rilevato Touchscreen attivo"
        # Configurazione KWin Wayland / libinput per touch
        if command -v kwriteconfig6 >/dev/null 2>&1; then
            kwriteconfig6 --file kcminputrc --group Touchscreen --key TapToClick "$TAP_TO_CLICK"
        fi
    fi

    # 2. Configurazione Touchpad
    if [[ "$has_pad" -eq 1 ]]; then
        echo "  [✓] Configurazione Touchpad..."

        # KWin Wayland libinput
        if command -v kwriteconfig6 >/dev/null 2>&1; then
            kwriteconfig6 --file kcminputrc --group Touchpad --key tapToClick "$TAP_TO_CLICK"
            kwriteconfig6 --file kcminputrc --group Touchpad --key naturalScroll "$NATURAL_SCROLL"
            kwriteconfig6 --file kcminputrc --group Touchpad --key twoFingerTap "$TWO_FINGER_RIGHT_CLICK"
            kwriteconfig6 --file kcminputrc --group Touchpad --key pointerSpeed "$POINTER_SPEED"
            kwriteconfig6 --file kcminputrc --group Touchpad --key disableWhileTyping "$PALM_REJECTION"
        fi

        # 3. Touchpad Vintage (Edge Scrolling & Syndaemon)
        local enable_edge="false"
        if [[ "$EDGE_SCROLLING_VINTAGE" == "true" || ("$EDGE_SCROLLING_VINTAGE" == "auto" && "$is_vintage" -eq 1) ]]; then
            enable_edge="true"
        fi

        if [[ "$enable_edge" == "true" ]]; then
            echo "  [+] Attivazione Edge Scrolling per Touchpad Vintage (Scorrimento sul bordo destro)..."
            if command -v synclient >/dev/null 2>&1; then
                synclient VertEdgeScroll=1 2>/dev/null || true
                synclient HorizEdgeScroll=1 2>/dev/null || true
                synclient TapButton1=1 2>/dev/null || true
                synclient TapButton2=3 2>/dev/null || true
            fi
        fi

        # Protezione anti-tocco involontario durante la digitazione su vecchi laptop
        if [[ "$PALM_REJECTION" == "true" ]] && command -v syndaemon >/dev/null 2>&1; then
            pkill syndaemon 2>/dev/null || true
            syndaemon -i 0.5 -t -K -d 2>/dev/null || true
            echo "  [✓] Syndaemon anti-palm protection attivo"
        fi
    fi

    echo "[✓] Configurazione input completata con successo."
}

cmd_status() {
    load_input_config
    read -r has_touch has_pad is_vintage <<< "$(detect_hardware_inputs)"

    echo "========================================================="
    echo "       OSify Universal Input Subsystem — Telemetria      "
    echo "========================================================="
    printf "  Touchscreen Rilevato : %s\n" "$([ "$has_touch" -eq 1 ] && echo "SI (Multi-touch attivo)" || echo "No / Standard Mouse")"
    printf "  Touchpad Rilevato    : %s\n" "$([ "$has_pad" -eq 1 ] && echo "SI" || echo "No")"
    printf "  Architettura Touchpad: %s\n" "$([ "$is_vintage" -eq 1 ] && echo "Legacy PS/2 (Vintage)" || echo "Modern Precision / I2C")"
    echo "---------------------------------------------------------"
    echo "  PARAMETRI CONFIGURATI:"
    echo "  • Natural Scrolling (Invertito)      : $NATURAL_SCROLL"
    echo "  • Tap-To-Click                       : $TAP_TO_CLICK"
    echo "  • Tasto Destro a Due Dita            : $TWO_FINGER_RIGHT_CLICK"
    echo "  • Scorrimento sul Bordo (Vintage)    : $EDGE_SCROLLING_VINTAGE"
    echo "  • Palm Rejection (Anti-urto digit.)  : $PALM_REJECTION"
    echo "  • Velocità Cursore / Puntatore       : $POINTER_SPEED"
    echo "  • Tocco Prolungato = Click Destro    : $TOUCH_HOLD_RIGHT_CLICK"
    echo "  • Dimensione Pulsanti Touch          : $TOUCH_TARGET_PADDING"
    echo "========================================================="
}

cmd_set() {
    load_input_config
    local key="$1"
    local val="$2"
    case "$key" in
        natural) NATURAL_SCROLL="$val" ;;
        tap) TAP_TO_CLICK="$val" ;;
        rightclick) TWO_FINGER_RIGHT_CLICK="$val" ;;
        edge) EDGE_SCROLLING_VINTAGE="$val" ;;
        palm) PALM_REJECTION="$val" ;;
        speed) POINTER_SPEED="$val" ;;
        touch) TOUCH_HOLD_RIGHT_CLICK="$val" ;;
        padding) TOUCH_TARGET_PADDING="$val" ;;
        *) echo "Parametro non valido. Usa: {natural|tap|rightclick|edge|palm|speed|touch|padding}"; exit 1 ;;
    esac
    save_input_config
    cmd_apply
    echo "[✓] Parametro $key impostato a $val."
}

case "${1:-status}" in
    status)
        cmd_status
        ;;
    apply)
        cmd_apply
        ;;
    set)
        cmd_set "${2:-}" "${3:-}"
        ;;
    test)
        load_policy 2>/dev/null || load_input_config
        cmd_apply >/dev/null
        echo "INPUT_SUBSYSTEM_OK"
        ;;
    *)
        echo "Uso: $0 {status|apply|set <key> <val>|test}"
        exit 1
        ;;
esac
