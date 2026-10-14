#!/usr/bin/env bash
# ==============================================================================
# OSify Universal IPA Runner — Apple iOS Application Package Handler
# ==============================================================================
# Gestisce pacchetti applicativi iOS (.ipa):
# 1. Analisi del bundle Payload/*.app e metadati Info.plist
# 2. Rilevamento crittografia DRM Apple FairPlay (cryptid flag Mach-O)
# 3. Instradamento:
#    - iOS 32-bit Legacy (ARMv6/ARMv7) -> touchHLE Engine nativo
#    - iOS Simulator (x86_64 Mach-O)   -> Darling Darwin Translation Layer
#    - iOS 64-bit FairPlay Encrypted   -> Diagnostica & Fallback guidato APK Android
# ==============================================================================

set -euo pipefail

IPA_FILE="${1:-}"

if [[ -z "$IPA_FILE" || ! -f "$IPA_FILE" ]]; then
    echo "[ERRORE] File pacchetto iOS non valido: $IPA_FILE" >&2
    exit 1
fi

echo "========================================================="
echo "       OSify Universal iOS Package Handler               "
echo "========================================================="
echo "Pacchetto target: $(basename "$IPA_FILE")"

WORK_DIR="/tmp/osify_ipa_$(date +%s)_$$"
mkdir -p "$WORK_DIR"
trap 'rm -rf "$WORK_DIR"' EXIT

# 1. Verifica struttura interna ZIP
if ! unzip -q -t "$IPA_FILE" 2>/dev/null; then
    echo "[ERRORE] Il file specificato non e' un archivio ZIP/IPA valido." >&2
    exit 1
fi

echo "[+] Analisi struttura interna Payload..."
APP_BUNDLE=$(unzip -l "$IPA_FILE" 2>/dev/null | awk '{print $4}' | grep -E '^Payload/[^/]+\.app/$' | head -n 1 || true)

if [[ -z "$APP_BUNDLE" ]]; then
    # Fallback ricerca file .app interno
    APP_BUNDLE=$(unzip -l "$IPA_FILE" 2>/dev/null | awk '{print $4}' | grep -E 'Payload/[^/]+\.app/' | head -n 1 | sed 's|\(Payload/[^/]*\.app\)/.*|\1/|' || true)
fi

if [[ -z "$APP_BUNDLE" ]]; then
    echo "[ERRORE] Struttura IPA non conforme: cartella 'Payload/*.app' non trovata." >&2
    exit 1
fi

echo "[✓] Applicazione individuata: $APP_BUNDLE"

# 2. Estrazione Info.plist per identificazione nome e architettura
unzip -q -j "$IPA_FILE" "${APP_BUNDLE}Info.plist" -d "$WORK_DIR" 2>/dev/null || true
BUNDLE_NAME="$(basename "$APP_BUNDLE" .app)"

# 3. Estrazione dell'eseguibile principale Mach-O
unzip -q -j "$IPA_FILE" "${APP_BUNDLE}${BUNDLE_NAME}" -d "$WORK_DIR" 2>/dev/null || true
MAIN_BIN="$WORK_DIR/$BUNDLE_NAME"

if [[ ! -f "$MAIN_BIN" ]]; then
    # Cerca il primo file eseguibile Mach-O all'interno del bundle
    FIRST_FILE=$(unzip -l "$IPA_FILE" "${APP_BUNDLE}*" 2>/dev/null | awk '{print $4}' | grep -E "^${APP_BUNDLE}[^/]+$" | grep -v '\.' | head -n 1 || true)
    if [[ -n "$FIRST_FILE" ]]; then
        unzip -q -j "$IPA_FILE" "$FIRST_FILE" -d "$WORK_DIR" 2>/dev/null || true
        MAIN_BIN="$WORK_DIR/$(basename "$FIRST_FILE")"
    fi
fi

if [[ ! -f "$MAIN_BIN" ]]; then
    echo "[ERRORE] Impossibile estrarre il binario Mach-O dal pacchetto IPA." >&2
    exit 1
fi

# 4. Radiografia Mach-O (Magic Bytes & Encryption Info)
HEX_MAGIC=$(od -An -N 4 -t x1 "$MAIN_BIN" 2>/dev/null | tr -d ' \n' || echo "")
echo "[+] Magic Number binario: $HEX_MAGIC"

# Verifica se il binario e' crittografato con Apple FairPlay DRM (cryptid != 0)
IS_ENCRYPTED=0
if command -v otool >/dev/null 2>&1; then
    if otool -l "$MAIN_BIN" 2>/dev/null | grep -A 4 "LC_ENCRYPTION_INFO" | grep -q "cryptid 1"; then
        IS_ENCRYPTED=1
    fi
elif grep -q "cryptid" "$MAIN_BIN" 2>/dev/null; then
    # Controllo euristico in assenza di otool
    IS_ENCRYPTED=1
fi

# 5. Strategia di esecuzione deterministica
if [[ "$HEX_MAGIC" =~ ^(feedface|cefaedfe) ]]; then
    echo "[i] Architettura: iOS 32-bit Legacy (ARMv6 / ARMv7)"
    if command -v touchhle >/dev/null 2>&1; then
        echo "[+] Avvio tramite engine touchHLE ad accelerazione nativa..."
        exec touchhle "$IPA_FILE"
    else
        echo "[!] touchHLE non presente nel sistema host."
        echo "    Installabile via: osify-ctl runtime install-touchhle"
        exit 1
    fi
elif [[ "$IS_ENCRYPTED" -eq 1 ]]; then
    echo "========================================================="
    echo " [!] AVVISO DI PROTEZIONE APPLE FAIRPLAY DRM             "
    echo "========================================================="
    echo "Questo pacchetto .ipa e' protetto da crittografia FairPlay"
    echo "legata all'account Apple ID dell'autore originale."
    echo ""
    echo "Soluzioni supportate da OSify:"
    echo " 1. Utilizzare un pacchetto IPA decrittato (fatto con dump da"
    echo "    dispositivo jailbroken / TrollStore / Clutch)."
    echo " 2. (Consigliato) Utilizzare l'omologo Android (.apk):"
    echo "    OSify supporta nativamente gli APK tramite Waydroid LXC"
    echo "    con accelerazione 3D GPU Mesa ad altissime prestazioni."
    echo "========================================================="
    
    # Se in ambiente grafico X11, notifica tramite zenity se disponibile
    if [[ -n "${DISPLAY:-}" ]] && command -v zenity >/dev/null 2>&1; then
        zenity --warning --title="OSify UEM — Apple FairPlay DRM" \
            --text="L'app iOS '$(basename "$IPA_FILE")' e' crittografata con FairPlay DRM Apple.\n\nPer usarla su OSify:\n- Utilizza la versione .ipa decrittata, oppure\n- Scarica la controparte Android (.apk), supportata al 100% nativamente!" 2>/dev/null || true
    fi
    exit 2
else
    echo "[i] Pacchetto iOS non crittografato / Simulator build."
    if command -v darling >/dev/null 2>&1; then
        echo "[+] Tentativo di caricamento tramite Darling Darwin Bridge..."
        exec darling shell "$MAIN_BIN" "${@:2}"
    else
        echo "[!] Runtime Darling non trovato."
        echo "    Abilitalo con: osify-ctl block enable darwin"
        exit 1
    fi
fi
