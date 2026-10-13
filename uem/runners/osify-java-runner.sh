#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Java Runner — Transparent JVM Bytecode & JAR Handler
# ==============================================================================
# Consente l'esecuzione nativa e trasparente di bytecode compilato (.class)
# e pacchetti archiviati (.jar) al doppio click o da riga di comando.
# ==============================================================================

set -euo pipefail

JAVA_FILE="${1:-}"

if [[ -z "$JAVA_FILE" || ! -f "$JAVA_FILE" ]]; then
    echo "[ERRORE] File Java/JAR non valido: $JAVA_FILE" >&2
    exit 1
fi

if ! command -v java >/dev/null 2>&1; then
    echo "[ERRORE] Java Runtime Environment (JRE) non installato nel sistema." >&2
    echo "         Installa OpenJDK con: pacman -S jre-openjdk-headless" >&2
    exit 1
fi

JAVA_DIR="$(cd "$(dirname "$JAVA_FILE")" && pwd)"
JAVA_BASENAME="$(basename "$JAVA_FILE")"

# Controllo se e' un archivio JAR o un file .class singolo
if [[ "$JAVA_FILE" =~ \.jar$ ]] || file -b "$JAVA_FILE" 2>/dev/null | grep -qi "zip\|jar"; then
    exec java -jar "$JAVA_FILE" "${@:2}"
elif [[ "$JAVA_FILE" =~ \.class$ ]]; then
    CLASS_NAME="${JAVA_BASENAME%.class}"
    cd "$JAVA_DIR"
    exec java "$CLASS_NAME" "${@:2}"
else
    # Fallback su tentativo di esecuzione diretta JAR
    exec java -jar "$JAVA_FILE" "${@:2}"
fi
