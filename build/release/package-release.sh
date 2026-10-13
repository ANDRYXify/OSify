#!/usr/bin/env bash
# ==============================================================================
# OSify Release Packaging Engine
# ==============================================================================
# Prepara e pacchettizza gli asset per la release ufficiale su GitHub:
# 1. OSify-NoUSB-Windows-Installer.zip (Pacchetto per installazione da Windows senza USB)
# 2. Verifica e calcolo checksum SHA256 per l'immagine ISO (OSify-x86_64-v3.iso)
# 3. Output finale organizzato nella directory build/out/release/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_RELEASE="$REPO_ROOT/build/out/release"
WIN_INSTALLER_DIR="$REPO_ROOT/tools/windows-installer"

mkdir -p "$OUT_RELEASE"

echo "========================================================="
echo "       OSify Release Packaging — Preparazione Asset       "
echo "========================================================="

# 1. Creazione Archivio ZIP per l'Installer Windows Senza USB
echo "[+] Creazione pacchetto 'OSify-NoUSB-Windows-Installer.zip'..."
ZIP_NAME="OSify-NoUSB-Windows-Installer.zip"
ZIP_PATH="$OUT_RELEASE/$ZIP_NAME"

rm -f "$ZIP_PATH"
(
    cd "$WIN_INSTALLER_DIR"
    zip -q -r "$ZIP_PATH" \
        "OSify-Setup.bat" \
        "OSify-NoUSB-Installer.ps1" \
        "ISTRUZIONI-INSTALLAZIONE.txt"
)
echo "[✓] Creato: $ZIP_PATH"

# 2. Verifica Immagine ISO e Calcolo Checksum
ISO_CANDIDATE=$(find "$REPO_ROOT/build/out" -maxdepth 1 -name "*.iso" | head -n1 || true)
CHECKSUM_FILE="$OUT_RELEASE/SHA256SUMS.txt"
rm -f "$CHECKSUM_FILE"

echo "[+] Generazione file di verifica integrità SHA256SUMS.txt..."
(
    cd "$OUT_RELEASE"
    shasum -a 256 "$ZIP_NAME" >> "$CHECKSUM_FILE"
)

if [[ -n "$ISO_CANDIDATE" && -f "$ISO_CANDIDATE" ]]; then
    echo "[+] Calcolo checksum per immagine ISO: $(basename "$ISO_CANDIDATE")..."
    (
        cd "$(dirname "$ISO_CANDIDATE")"
        shasum -a 256 "$(basename "$ISO_CANDIDATE")" >> "$CHECKSUM_FILE"
    )
    echo "[✓] ISO inclusa nel file checksum."
else
    echo "[i] Nessun file .iso trovato in build/out/ (la compilazione ISO puo' essere eseguita con build/docker/run-build.sh)."
fi

echo ""
echo "========================================================="
echo "       Asset di Release Pronti in: $OUT_RELEASE"
echo "========================================================="
ls -lh "$OUT_RELEASE"
