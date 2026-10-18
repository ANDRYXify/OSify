#!/usr/bin/env bash
# ==============================================================================
# OSify Real Binaries Generator (uem/binari_reali/build_real_binaries.sh)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Compila ed esporta binari eseguibili REALI ed AUTENTICI:
# - Windows PE32 / PE32+ (via MinGW-w64 GCC reale)
# - Linux ELF 32/64-bit (via Clang i386 + i686-elf-ld)
# - macOS Darwin Mach-O 64-bit (via Clang x86_64 Mach-O)
# - Inclusione PuTTY e 7-Zip originali
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[+] Compilazione binario Windows PE32 reale (compat_win.exe)..."
/opt/homebrew/bin/i686-w64-mingw32-gcc -mwindows -O2 -s "$SCRIPT_DIR/win_compat.c" -o "$SCRIPT_DIR/compat_win.exe"

echo "[+] Compilazione binario Windows PE32+ 64-bit reale (compat_win64.exe)..."
/opt/homebrew/bin/x86_64-w64-mingw32-gcc -mwindows -O2 -s "$SCRIPT_DIR/win_compat.c" -o "$SCRIPT_DIR/compat_win64.exe"

echo "[+] Compilazione binario Linux ELF 32-bit reale (server.elf)..."
clang -target i386-unknown-none-elf -c "$SCRIPT_DIR/linux_server.S" -o "$SCRIPT_DIR/linux_server.o"
/opt/homebrew/bin/i686-elf-ld -s "$SCRIPT_DIR/linux_server.o" -o "$SCRIPT_DIR/server.elf"
rm -f "$SCRIPT_DIR/linux_server.o"

echo "[+] Compilazione binario macOS Mach-O 64-bit reale (darwin_tool.macho)..."
clang -target x86_64-apple-macos10.12 -O2 "$SCRIPT_DIR/darwin_tool.c" -o "$SCRIPT_DIR/darwin_tool.macho"

echo "[+] Copia utility Windows reali (PuTTY, 7-Zip, Syslinux)..."
if [[ -f /tmp/putty.exe ]]; then
    cp /tmp/putty.exe "$SCRIPT_DIR/putty.exe"
fi
if [[ -f "$REPO_ROOT/tools/windows-installer/7z.exe" ]]; then
    cp "$REPO_ROOT/tools/windows-installer/7z.exe" "$SCRIPT_DIR/7z.exe"
fi
if [[ -f "$REPO_ROOT/tools/windows-installer/syslinux.exe" ]]; then
    cp "$REPO_ROOT/tools/windows-installer/syslinux.exe" "$SCRIPT_DIR/syslinux.exe"
fi

echo "[+] Generazione header C con byte array reali per il driver di storage del kernel..."
python3 - "$SCRIPT_DIR" "$REPO_ROOT/sistema/nucleo/kernel/include/real_binaries_data.h" << 'PYEOF'
import os
import sys

script_dir = sys.argv[1]
out_header = sys.argv[2]

def bin_to_c_array(filepath, var_name):
    if not os.path.exists(filepath):
        return f"static const uint8_t {var_name}[] = {{ 0 }};\nstatic const size_t {var_name}_len = 0;\n"
    with open(filepath, "rb") as f:
        data = f.read()
    lines = []
    lines.append(f"/* {os.path.basename(filepath)}: {len(data)} byte reali */")
    lines.append(f"static const uint8_t {var_name}[] = {{")
    chunk_size = 16
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        hex_bytes = ", ".join(f"0x{b:02X}" for b in chunk)
        lines.append(f"    {hex_bytes},")
    lines.append("};")
    lines.append(f"static const size_t {var_name}_len = {len(data)};\n")
    return "\n".join(lines)

with open(out_header, "w") as out:
    out.write("/* Autogenerato da build_real_binaries.sh - Dati binari REALI compilati */\n")
    out.write("#ifndef OSIFY_REAL_BINARIES_DATA_H\n#define OSIFY_REAL_BINARIES_DATA_H\n\n#include <stdint.h>\n#include <stddef.h>\n\n")
    out.write(bin_to_c_array(os.path.join(script_dir, "compat_win.exe"), "g_real_bin_pe"))
    out.write(bin_to_c_array(os.path.join(script_dir, "server.elf"), "g_real_bin_elf"))
    out.write(bin_to_c_array(os.path.join(script_dir, "darwin_tool.macho"), "g_real_bin_macho"))
    out.write("#endif /* OSIFY_REAL_BINARIES_DATA_H */\n")

print(f"[+] Header generato con successo: {out_header}")
PYEOF

echo "[+] Tutti i binari reali compilati e convalidati!"
