#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Polyglot Dispatcher — The Architecture-Breaking Execution Core
# ==============================================================================
# Analizza qualsiasi file binario o script tramite Magic Number Sniffing e
# instrada deterministica l'esecuzione al runner specializzato:
# - Windows PE (32/64-bit) -> osify-pe-runner.sh
# - MS-DOS 16-bit (MZ/COM) -> osify-dos-runner.sh
# - Apple Darwin Mach-O    -> osify-macho-runner.sh
# - Android APK / AAB      -> osify-apk-runner.sh
# - WebAssembly (WASI)     -> osify-wasm-runner.sh
# - Java Bytecode / JAR    -> osify-java-runner.sh
# - Cross-ISA ELF          -> osify-cross-runner.sh
# - Script polyglot        -> Interprete di sistema associato
# ==============================================================================

set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" || (! -f "$TARGET" && ! -d "$TARGET") ]]; then
    echo "========================================================="
    echo "       OSify Universal Polyglot Dispatcher               "
    echo "========================================================="
    echo "Uso: osify-exec <qualsiasi-file-o-programma> [argomenti...]"
    echo ""
    echo "Esempi:"
    echo "  osify-exec setup.exe           (Esegue con Compatibilità.ify Windows)"
    echo "  osify-exec app.apk             (Esegue con Compatibilità.ify Mobile)"
    echo "  osify-exec game.ipa            (Esegue con Compatibilità.ify iOS)"
    echo "  osify-exec app.app             (Esegue con Compatibilità.ify macOS)"
    echo "  osify-exec programma.ify       (Esegue con GestorePacchetti.ify)"
    echo "  osify-exec binary_arm64        (Esegue con Compatibilità.ify Cross-Arch)"
    echo "  osify-exec turbo_pascal.exe    (Esegue con Compatibilità.ify DOS)"
    echo "  osify-exec module.wasm         (Esegue con Compatibilità.ify WASM)"
    echo "  osify-exec app.jar             (Esegue con Compatibilità.ify Java)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Funzione universale per individuare ed eseguire i moduli runner di compatibilità OSify
run_uem_module() {
    local runner_name="$1"
    shift
    for cand in \
        "$SCRIPT_DIR/${runner_name}.sh" \
        "$SCRIPT_DIR/${runner_name}" \
        "/usr/local/bin/${runner_name}.sh" \
        "/usr/local/bin/${runner_name}" \
        "/usr/bin/${runner_name}.sh" \
        "/usr/bin/${runner_name}" \
        "/Sistema/Servizi/Compatibilita/${runner_name}.sh" \
        "/Sistema/Servizi/Compatibilita/${runner_name}" \
        "/Sistema/Servizi/UEM/${runner_name}.sh" \
        "/Sistema/Servizi/UEM/${runner_name}" \
        "/Sistema/Servizi/${runner_name}" \
        "/opt/osify/uem/runners/${runner_name}.sh" \
        "/opt/osify/uem/runners/${runner_name}"; do
        if [[ -x "$cand" && ! -d "$cand" ]]; then
            exec "$cand" "$@"
        fi
    done

    # Fallback con interprete bash se il file esiste ma manca il bit eseguibile
    for cand in \
        "$SCRIPT_DIR/${runner_name}.sh" \
        "$SCRIPT_DIR/${runner_name}" \
        "/usr/local/bin/${runner_name}.sh" \
        "/usr/local/bin/${runner_name}" \
        "/usr/bin/${runner_name}.sh" \
        "/usr/bin/${runner_name}"; do
        if [[ -f "$cand" && ! -d "$cand" ]]; then
            exec bash "$cand" "$@"
        fi
    done

    echo "[OSify UEM] Errore: modulo di compatibilità '${runner_name}' non trovato nel sistema." >&2
    exit 127
}

# Se e' un pacchetto o bundle nativo OSify (.ify)
if [[ "$TARGET" =~ \.ify/?$ ]]; then
    if [ -x "/Sistema/Servizi/GestorePacchetti.ify" ]; then
        exec "/Sistema/Servizi/GestorePacchetti.ify" "$TARGET" "${@:2}"
    elif [ -x "$SCRIPT_DIR/../../sistema/servizi/GestorePacchetti.ify" ]; then
        exec "$SCRIPT_DIR/../../sistema/servizi/GestorePacchetti.ify" "$TARGET" "${@:2}"
    else
        run_uem_module "GestorePacchetti.ify" "$TARGET" "${@:2}"
    fi
fi

# Se e' una cartella .app di macOS
if [[ -d "$TARGET" && "$TARGET" =~ \.app/?$ ]]; then
    run_uem_module "osify-macho-runner" "$TARGET" "${@:2}"
fi

# Lettura primi 4 byte esadecimali (supporto multi-tool: od, hexdump o python3)
HEX_MAGIC=""
if command -v od >/dev/null 2>&1; then
    HEX_MAGIC=$(od -An -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' \n' || echo "")
elif command -v hexdump >/dev/null 2>&1; then
    HEX_MAGIC=$(hexdump -v -n 4 -e '1/1 "%02x"' "$TARGET" 2>/dev/null || echo "")
elif command -v python3 >/dev/null 2>&1; then
    HEX_MAGIC=$(python3 -c 'import sys; f=open(sys.argv[1],"rb"); print(f.read(4).hex())' "$TARGET" 2>/dev/null || echo "")
fi

# 1. Riconoscimento MS-DOS / Windows PE (Magic: 4d5a = "MZ")
if [[ "$HEX_MAGIC" =~ ^4d5a ]]; then
    PE_OFFSET=0
    if command -v od >/dev/null 2>&1; then
        PE_OFFSET=$(od -An -j 60 -N 4 -t u4 "$TARGET" 2>/dev/null | tr -d ' ' || echo "0")
    elif command -v hexdump >/dev/null 2>&1; then
        PE_OFFSET=$(hexdump -s 60 -n 4 -e '1/4 "%u"' "$TARGET" 2>/dev/null || echo "0")
    elif command -v python3 >/dev/null 2>&1; then
        PE_OFFSET=$(python3 -c 'import sys, struct; f=open(sys.argv[1],"rb"); f.seek(60); print(struct.unpack("<I", f.read(4))[0])' "$TARGET" 2>/dev/null || echo "0")
    fi
    if [[ "$PE_OFFSET" =~ ^[0-9]+$ ]] && [[ "$PE_OFFSET" -ge 64 ]]; then
        SIG=$(dd if="$TARGET" bs=1 skip="$PE_OFFSET" count=2 2>/dev/null || echo "")
        if [[ "$SIG" == "PE" ]]; then
            run_uem_module "osify-pe-runner" "$TARGET" "${@:2}"
        fi
    fi
    # Se non c'e' header PE, e' un binario MS-DOS a 16-bit
    run_uem_module "osify-dos-runner" "$TARGET" "${@:2}"
fi

# 2. Riconoscimento WebAssembly (Magic: 0061736d = "\x00asm")
if [[ "$HEX_MAGIC" =~ ^0061736d ]]; then
    run_uem_module "osify-wasm-runner" "$TARGET" "${@:2}"
fi

# 3. Riconoscimento Java / Mach-O Fat Binary (Magic: cafebabe)
if [[ "$HEX_MAGIC" =~ ^cafebabe ]]; then
    VER_BYTE=""
    if command -v od >/dev/null 2>&1; then
        VER_BYTE=$(od -An -j 4 -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    elif command -v hexdump >/dev/null 2>&1; then
        VER_BYTE=$(hexdump -s 4 -n 4 -e '1/1 "%02x"' "$TARGET" 2>/dev/null || echo "")
    fi
    if [[ "$VER_BYTE" =~ ^0000 ]]; then
        run_uem_module "osify-java-runner" "$TARGET" "${@:2}"
    else
        run_uem_module "osify-macho-runner" "$TARGET" "${@:2}"
    fi
fi

# 4. Riconoscimento Mach-O Darwin (Magic: feedface, feedfacf, cffaedfe, cefaedfe)
if [[ "$HEX_MAGIC" =~ ^(feedface|feedfacf|cffaedfe|cefaedfe) ]]; then
    run_uem_module "osify-macho-runner" "$TARGET" "${@:2}"
fi

# 5. Riconoscimento Archivi PKZIP (Magic: 504b0304 = "PK\x03\x04")
if [[ "$HEX_MAGIC" =~ ^504b0304 ]]; then
    if [[ "$TARGET" =~ \.apk$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "AndroidManifest.xml"); then
        run_uem_module "osify-apk-runner" "$TARGET" "${@:2}"
    elif [[ "$TARGET" =~ \.ipa$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -qE "Payload/[^/]+\.app"); then
        run_uem_module "osify-ipa-runner" "$TARGET" "${@:2}"
    elif [[ "$TARGET" =~ \.jar$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "META-INF/MANIFEST.MF"); then
        run_uem_module "osify-java-runner" "$TARGET" "${@:2}"
    fi
fi

# 6. Riconoscimento ELF Linux (Magic: 7f454c46 = "\x7fELF")
if [[ "$HEX_MAGIC" =~ ^7f454c46 ]]; then
    TARGET_MACHINE=""
    if command -v od >/dev/null 2>&1; then
        TARGET_MACHINE=$(od -An -j 18 -N 2 -t x2 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    elif command -v hexdump >/dev/null 2>&1; then
        TARGET_MACHINE=$(hexdump -s 18 -n 2 -e '1/2 "%04x"' "$TARGET" 2>/dev/null || echo "")
    fi
    HOST_ARCH="$(uname -m)"

    IS_NATIVE=0
    if [[ "$HOST_ARCH" == "x86_64" && "$TARGET_MACHINE" == "003e" ]]; then IS_NATIVE=1; fi
    if [[ "$HOST_ARCH" =~ ^(i686|i386)$ && "$TARGET_MACHINE" == "0003" ]]; then IS_NATIVE=1; fi
    if [[ "$HOST_ARCH" =~ ^(aarch64|arm64)$ && "$TARGET_MACHINE" == "00b7" ]]; then IS_NATIVE=1; fi

    if [[ "$IS_NATIVE" -eq 1 ]]; then
        chmod +x "$TARGET" 2>/dev/null || true
        exec "$TARGET" "${@:2}"
    else
        run_uem_module "osify-cross-runner" "$TARGET" "${@:2}"
    fi
fi

# 7. Script interpretati con Shebang (#!)
FIRST_TWO=$(dd if="$TARGET" bs=1 count=2 2>/dev/null || echo "")
if [[ "$FIRST_TWO" == "#!" ]]; then
    chmod +x "$TARGET" 2>/dev/null || true
    exec "$TARGET" "${@:2}"
fi

# 8. Mappatura deterministica basata su estensione (fallback infallibile)
case "$TARGET" in
    *.exe|*.EXE|*.msi|*.MSI|*.dll|*.DLL)
        run_uem_module "osify-pe-runner" "$TARGET" "${@:2}"
        ;;
    *.com|*.COM)
        run_uem_module "osify-dos-runner" "$TARGET" "${@:2}"
        ;;
    *.apk|*.APK|*.aab|*.AAB)
        run_uem_module "osify-apk-runner" "$TARGET" "${@:2}"
        ;;
    *.ipa|*.IPA)
        run_uem_module "osify-ipa-runner" "$TARGET" "${@:2}"
        ;;
    *.wasm|*.WASM)
        run_uem_module "osify-wasm-runner" "$TARGET" "${@:2}"
        ;;
    *.jar|*.JAR|*.class|*.CLASS)
        run_uem_module "osify-java-runner" "$TARGET" "${@:2}"
        ;;
    *.app|*.APP)
        run_uem_module "osify-macho-runner" "$TARGET" "${@:2}"
        ;;
    *.py)   exec python3 "$TARGET" "${@:2}" ;;
    *.js|*.mjs) exec node "$TARGET" "${@:2}" ;;
    *.sh|*.bash) exec bash "$TARGET" "${@:2}" ;;
    *.zsh)  exec zsh "$TARGET" "${@:2}" ;;
    *.lua)  exec lua "$TARGET" "${@:2}" ;;
    *.pl)   exec perl "$TARGET" "${@:2}" ;;
    *.rb)   exec ruby "$TARGET" "${@:2}" ;;
esac

# Fallback finale: tentativo di esecuzione diretta
chmod +x "$TARGET" 2>/dev/null || true
exec "$TARGET" "${@:2}"
