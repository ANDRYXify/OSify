#!/usr/bin/env bash
# ==============================================================================
# OSify Universal WebAssembly Runner (WASI Standalone Engine)
# ==============================================================================
# Esegue moduli WebAssembly (.wasm) direttamente a livello di sistema operativo
# sfruttando il runtime Wasmtime / Wasmer o Node WASI ad alte prestazioni.
# ==============================================================================

set -euo pipefail

WASM_FILE="${1:-}"

if [[ -z "$WASM_FILE" || ! -f "$WASM_FILE" ]]; then
    echo "[ERRORE] File WebAssembly non valido: $WASM_FILE" >&2
    exit 1
fi

if command -v wasmtime >/dev/null 2>&1; then
    exec wasmtime run "$WASM_FILE" "$@"
elif command -v wasmer >/dev/null 2>&1; then
    exec wasmer run "$WASM_FILE" "$@"
elif command -v node >/dev/null 2>&1; then
    exec node --experimental-wasi-unstable-preview1 "$WASM_FILE" "$@"
else
    echo "[ERRORE] Nessun runtime WebAssembly WASI trovato (wasmtime/wasmer)." >&2
    exit 1
fi
