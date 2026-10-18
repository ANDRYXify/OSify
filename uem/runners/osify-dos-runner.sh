#!/usr/bin/env bash
# ==============================================================================
# OSify Universal DOS Runner — Transparent 16-bit MS-DOS Executable Handler
# ==============================================================================
# Consente l'esecuzione trasparente di binari MS-DOS storici (.com e .exe MZ)
# su architetture moderne a 64-bit e 32-bit, aggirando la perdita del supporto
# VDM (Virtual DOS Machine) nei sistemi operativi moderni.
# Supporta: dosbox-staging, dosbox o dosemu2 con montaggio automatico della cartella.
# ==============================================================================

set -euo pipefail

DOS_FILE="${1:-}"

if [[ -z "$DOS_FILE" || ! -f "$DOS_FILE" ]]; then
    echo "[ERRORE] File MS-DOS non valido: $DOS_FILE" >&2
    exit 1
fi
shift

DOS_DIR="$(cd "$(dirname "$DOS_FILE")" && pwd)"
DOS_NAME="$(basename "$DOS_FILE")"

# Verifica header MZ vs PE: se all'offset 0x3C c'è un puntatore a "PE\0\0", e' un eseguibile Windows!
if command -v od >/dev/null 2>&1; then
    PE_OFFSET=$(od -An -j 60 -N 4 -t u4 "$DOS_FILE" 2>/dev/null | tr -d ' ' || echo "0")
    if [[ "$PE_OFFSET" =~ ^[0-9]+$ ]] && [[ "$PE_OFFSET" -ge 64 ]]; then
        SIGNATURE=$(dd if="$DOS_FILE" bs=1 skip="$PE_OFFSET" count=2 2>/dev/null || echo "")
        if [[ "$SIGNATURE" == "PE" ]]; then
            # E' un file PE Windows mascherato da MZ: inoltra al runner PE
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            exec "$SCRIPT_DIR/osify-pe-runner.sh" "$DOS_FILE" "$@"
        fi
    fi
fi

# Esecuzione trasparente in ambiente MS-DOS
if command -v dosbox-staging >/dev/null 2>&1; then
    exec dosbox-staging -c "mount c \"$DOS_DIR\"" -c "c:" -c "$DOS_NAME" -c "exit" -exit
elif command -v dosbox >/dev/null 2>&1; then
    exec dosbox -c "mount c \"$DOS_DIR\"" -c "c:" -c "$DOS_NAME" -c "exit" -exit
elif command -v dosemu >/dev/null 2>&1; then
    exec dosemu -dumb -E "$DOS_NAME"
else
    echo "[ERRORE] Nessun runtime MS-DOS trovato (dosbox-staging o dosemu2)." >&2
    echo "         Installa il modulo MS-DOS tramite il Centro OSify." >&2
    exit 1
fi
