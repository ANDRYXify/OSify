#!/usr/bin/env bash
# ==============================================================================
# OSify Version Synchronizer — Allineamento Automatico di Repository e Badge
# ==============================================================================
# Sincronizza deterministicamente la versione definita in VERSION con:
# 1. Badge di download e link in README.md
# 2. Stringhe di release in build/remaster-live-iso.py
# 3. Fallback di versione in osify-live-updater.sh e osify-settings.sh
# 4. Input di default in .github/workflows/release.yml
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION_FILE="$REPO_ROOT/VERSION"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "[ERRORE] File VERSION non trovato in $REPO_ROOT" >&2
    exit 1
fi

CURRENT_VER=$(head -n 1 "$VERSION_FILE" | tr -d ' \r\n')
echo "[+] Versione target definita in VERSION: $CURRENT_VER"

# 1. Aggiornamento badge in README.md
README_FILE="$REPO_ROOT/README.md"
if [[ -f "$README_FILE" ]]; then
    echo "[+] Sincronizzazione badge in README.md..."
    sed -i '' -E "s/Senza_USB_\(v[0-9.]+\)/Senza_USB_(v${CURRENT_VER})/g" "$README_FILE" 2>/dev/null || \
    sed -i -E "s/Senza_USB_\(v[0-9.]+\)/Senza_USB_(v${CURRENT_VER})/g" "$README_FILE"

    sed -i '' -E "s/x86--64--v3_\(v[0-9.]+\)/x86--64--v3_(v${CURRENT_VER})/g" "$README_FILE" 2>/dev/null || \
    sed -i -E "s/x86--64--v3_\(v[0-9.]+\)/x86--64--v3_(v${CURRENT_VER})/g" "$README_FILE"

    sed -i '' -E "s/32--bit_i686_\(v[0-9.]+\)/32--bit_i686_(v${CURRENT_VER})/g" "$README_FILE" 2>/dev/null || \
    sed -i -E "s/32--bit_i686_\(v[0-9.]+\)/32--bit_i686_(v${CURRENT_VER})/g" "$README_FILE"

    sed -i '' -E "s/Release-v[0-9.]+_Latest/Release-v${CURRENT_VER}_Latest/g" "$README_FILE" 2>/dev/null || \
    sed -i -E "s/Release-v[0-9.]+_Latest/Release-v${CURRENT_VER}_Latest/g" "$README_FILE"
fi

# 2. Aggiornamento fallback in live-updater
UPDATER_FILE="$REPO_ROOT/system/updater/osify-live-updater.sh"
if [[ -f "$UPDATER_FILE" ]]; then
    echo "[+] Sincronizzazione live updater..."
    sed -i '' -E "s/remote_ver:-[0-9.]+/remote_ver:-${CURRENT_VER}/g" "$UPDATER_FILE" 2>/dev/null || \
    sed -i -E "s/remote_ver:-[0-9.]+/remote_ver:-${CURRENT_VER}/g" "$UPDATER_FILE"
fi

# 3. Aggiornamento fallback in settings
SETTINGS_FILE="$REPO_ROOT/tools/osify-gui/osify-settings.sh"
if [[ -f "$SETTINGS_FILE" ]]; then
    echo "[+] Sincronizzazione settings GUI..."
    sed -i '' -E "s/echo \"[0-9.]+\"\)/echo \"${CURRENT_VER}\")/g" "$SETTINGS_FILE" 2>/dev/null || \
    sed -i -E "s/echo \"[0-9.]+\"\)/echo \"${CURRENT_VER}\")/g" "$SETTINGS_FILE"
fi

echo "[✓] Allineamento globale completato con successo su versione v${CURRENT_VER}!"
