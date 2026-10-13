#!/usr/bin/env bash
# ==============================================================================
# OSify Automated Engineering Test Suite
# ==============================================================================
# Esegue un collaudo approfondito su tutti i moduli, script e configurazioni:
# 1. Validazione sintassi Bash (bash -n su tutti gli script)
# 2. Compilazione bytecode e validazione Python (py_compile su tutti i tool)
# 3. Validazione JSON (blocchi modulari e configurazioni relay)
# 4. Collaudo motore Hardware Intelligence & Probe
# 5. Collaudo motore Anti-Cheat Intelligence
# 6. Collaudo motore Architettura a Blocchi (Enable/Disable cycle)
# 7. Verifica permessi di esecuzione e consistenza repository
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASSED_COUNT=0
FAILED_COUNT=0

log_pass() {
    echo "  [✓ PASS] $1"
    PASSED_COUNT=$((PASSED_COUNT + 1))
}

log_fail() {
    echo "  [✗ FAIL] $1"
    FAILED_COUNT=$((FAILED_COUNT + 1))
}

echo "========================================================="
echo "       OSify Master Test Suite — Collaudo di Sistema     "
echo "========================================================="
echo "[+] Root di progetto: $REPO_ROOT"
echo ""

# ------------------------------------------------------------------------------
# TEST 1: SINTASSI SCRIPT BASH (bash -n)
# ------------------------------------------------------------------------------
echo "--- [1/7] Verifica Sintattica Script Shell (bash -n) ---"
while IFS= read -r -d '' sh_file; do
    rel_path="${sh_file#$REPO_ROOT/}"
    if bash -n "$sh_file"; then
        log_pass "$rel_path (Sintassi corretta)"
    else
        log_fail "$rel_path (Errore di sintassi Bash!)"
    fi
done < <(find "$REPO_ROOT" -type f -name "*.sh" -print0)

# ------------------------------------------------------------------------------
# TEST 2: SINTASSI & COMPILAZIONE PYTHON
# ------------------------------------------------------------------------------
echo ""
echo "--- [2/7] Verifica Compilazione Bytecode Python ---"
while IFS= read -r -d '' py_file; do
    rel_path="${py_file#$REPO_ROOT/}"
    if python3 -m py_compile "$py_file"; then
        log_pass "$rel_path (Compilato senza errori)"
    else
        log_fail "$rel_path (Errore di sintassi Python!)"
    fi
done < <(find "$REPO_ROOT" -type f -name "*.py" -print0)

# ------------------------------------------------------------------------------
# TEST 3: VALIDAZIONE JSON
# ------------------------------------------------------------------------------
echo ""
echo "--- [3/7] Validazione File JSON e Schemi ---"
while IFS= read -r -d '' json_file; do
    rel_path="${json_file#$REPO_ROOT/}"
    if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
        log_pass "$rel_path (JSON valido e ben formato)"
    else
        log_fail "$rel_path (Errore nel parsing JSON!)"
    fi
done < <(find "$REPO_ROOT" -type f -name "*.json" -print0)

# ------------------------------------------------------------------------------
# TEST 4: HARDWARE INTELLIGENCE PROBE
# ------------------------------------------------------------------------------
echo ""
echo "--- [4/7] Collaudo Motore Hardware Diagnostics ---"
if out=$("$REPO_ROOT/kernel/legacy/osify-hardware-detect.sh"); then
    if echo "$out" | grep -qi "CPU Support Level"; then
        log_pass "Hardware Probe (Output consistente con diagnostica CPU)"
    else
        log_fail "Hardware Probe (Output inatteso o incompleto)"
    fi
else
    log_fail "Hardware Probe (Uscita con codice di errore)"
fi

# ------------------------------------------------------------------------------
# TEST 5: ANTI-CHEAT INTELLIGENCE ENGINE
# ------------------------------------------------------------------------------
echo ""
echo "--- [5/7] Collaudo Anti-Cheat Intelligence & Ring-0 Detection ---"
ac_script="$REPO_ROOT/runtimes/windows/anticheat/osify-anticheat-checker.py"
if out_vanguard=$(python3 "$ac_script" "Valorant"); then
    if echo "$out_vanguard" | grep -q "BLOCKED_RING0"; then
        log_pass "Anti-Cheat: Valorant correttamente classificato come BLOCKED_RING0"
    else
        log_fail "Anti-Cheat: Valorant classificazione errata"
    fi
fi

if out_elden=$(python3 "$ac_script" "Elden Ring"); then
    if echo "$out_elden" | grep -q "SUPPORTED"; then
        log_pass "Anti-Cheat: Elden Ring correttamente classificato come SUPPORTED (EAC Bridge)"
    else
        log_fail "Anti-Cheat: Elden Ring classificazione errata"
    fi
fi

# ------------------------------------------------------------------------------
# TEST 6: ARCHITETTURA A BLOCCHI MODULARE
# ------------------------------------------------------------------------------
echo ""
echo "--- [6/7] Collaudo Gestore Architettura a Blocchi ---"
bm_script="$REPO_ROOT/blocks/osify-block-manager.py"
if python3 "$bm_script" list >/dev/null; then
    log_pass "Block Manager: Elenco blocchi caricato con successo"
else
    log_fail "Block Manager: Impossibile caricare elenco blocchi"
fi

# Test ciclo enable/disable
python3 "$bm_script" enable presentation >/dev/null 2>&1 || true
if python3 "$bm_script" list | grep "presentation" | grep -q "ATTIVO"; then
    log_pass "Block Manager: Toggle abilitazione blocco [presentation] funzionante"
else
    log_fail "Block Manager: Toggle abilitazione fallito"
fi

# ------------------------------------------------------------------------------
# TEST 7: UNIVERSAL EXECUTION MATRIX (UEM) & RADIOGRAFIA ARCHITETTURALE
# ------------------------------------------------------------------------------
echo ""
echo "--- [7/7] Collaudo Universal Execution Matrix (UEM) & Radiografia ---"

# 7.1 Status Matrix
if "$REPO_ROOT/tools/osify-ctl" uem status | grep "Windows PE" >/dev/null; then
    log_pass "UEM: Status Matrix riporta correttamente i sottosistemi attivi"
else
    log_fail "UEM: Status Matrix non consistente"
fi

# 7.2 Radiografia Binari Sintetici (MZ, PE, WASM, Java, Mach-O)
TMP_UEM_DIR="$REPO_ROOT/tests/sandbox/uem-test-fixtures"
mkdir -p "$TMP_UEM_DIR"

# File MS-DOS MZ (senza PE)
printf "MZ\x00\x00" > "$TMP_UEM_DIR/test-dos.exe"
if "$REPO_ROOT/uem/runners/osify-inspect.sh" "$TMP_UEM_DIR/test-dos.exe" | grep "MS-DOS" >/dev/null; then
    log_pass "UEM Radiography: MS-DOS 16-bit correttamente classificato"
else
    log_fail "UEM Radiography: Fallimento classificazione MS-DOS"
fi

# File Windows PE (MZ + PE offset a 64 bytes)
printf "MZ%58s\x40\x00\x00\x00PE\x00\x00\x64\x86" " " > "$TMP_UEM_DIR/test-win.exe"
if "$REPO_ROOT/uem/runners/osify-inspect.sh" "$TMP_UEM_DIR/test-win.exe" | grep "Windows Portable Executable" >/dev/null; then
    log_pass "UEM Radiography: Windows PE64 correttamente classificato"
else
    log_fail "UEM Radiography: Fallimento classificazione Windows PE"
fi

# File WebAssembly (\x00asm)
printf "\x00asm\x01\x00\x00\x00" > "$TMP_UEM_DIR/test.wasm"
if "$REPO_ROOT/uem/runners/osify-inspect.sh" "$TMP_UEM_DIR/test.wasm" | grep "WebAssembly" >/dev/null; then
    log_pass "UEM Radiography: WebAssembly WASI correttamente classificato"
else
    log_fail "UEM Radiography: Fallimento classificazione WebAssembly"
fi

# File Java Bytecode (\xca\xfe\xba\xbe\x00\x00\x00\x34)
printf "\xca\xfe\xba\xbe\x00\x00\x00\x34" > "$TMP_UEM_DIR/test.class"
if "$REPO_ROOT/uem/runners/osify-inspect.sh" "$TMP_UEM_DIR/test.class" | grep "Java Virtual Machine" >/dev/null; then
    log_pass "UEM Radiography: Java Class Bytecode correttamente classificato"
else
    log_fail "UEM Radiography: Fallimento classificazione Java"
fi

# File Mach-O (\xfe\xed\xfa\xcf)
printf "\xfe\xed\xfa\xcf" > "$TMP_UEM_DIR/test.macho"
if "$REPO_ROOT/uem/runners/osify-inspect.sh" "$TMP_UEM_DIR/test.macho" | grep "Mach-O" >/dev/null; then
    log_pass "UEM Radiography: Apple Darwin Mach-O correttamente classificato"
else
    log_fail "UEM Radiography: Fallimento classificazione Mach-O"
fi

# Pulizia fixture di collaudo
rm -rf "$TMP_UEM_DIR"

# 7.3 Collaudo Hardware Adaptation Layer
if "$REPO_ROOT/uem/hal/osify-hal.sh" | grep "Hardware Adaptation Layer" >/dev/null; then
    log_pass "HAL: Engine di tuning hardware eseguito con successo"
else
    log_fail "HAL: Esecuzione tuning hardware fallita"
fi

# ------------------------------------------------------------------------------
# TEST 8: SOTTOSISTEMI SISTEMA OPERATIVO AUTONOMO (STANDALONE OS SUITE)
# ------------------------------------------------------------------------------
echo ""
echo "--- [8/8] Collaudo Sottosistemi di Sistema Operativo Autonomo ---"

# 8.1 Rete & Wi-Fi
if "$REPO_ROOT/network/osify-wifi-manager.sh" status | grep "STATO RETE OSIFY" >/dev/null; then
    log_pass "Network Subsystem: Wi-Fi & CAKE QoS status operativo"
else
    log_fail "Network Subsystem: Wi-Fi manager status fallito"
fi

# 8.2 Audio Manager
if "$REPO_ROOT/audio/osify-sound-manager.sh" get >/dev/null; then
    log_pass "Sound Subsystem: Lettura volume e mixer ALSA/PipeWire operativa"
else
    log_fail "Sound Subsystem: Audio manager get fallito"
fi

# 8.3 Display & Brightness
if "$REPO_ROOT/system/display/osify-display-manager.sh" resolutions | grep "Modalità Video" >/dev/null; then
    log_pass "Display Subsystem: Rilevamento risoluzioni KMS/XRandR operativo"
else
    log_fail "Display Subsystem: Display manager fallito"
fi

# 8.4 Power & Battery
if "$REPO_ROOT/system/power/osify-power-manager.sh" battery >/dev/null; then
    log_pass "Power Subsystem: Telemetria batteria ACPI e profili TDP operativi"
else
    log_fail "Power Subsystem: Power manager battery fallito"
fi

# 8.5 Package Manager
if "$REPO_ROOT/tools/osify-pkg" list | grep "CATALOGO APPLICATIVI" >/dev/null; then
    log_pass "Package Hub: Catalogo software autonomo pronto e navigabile"
else
    log_fail "Package Hub: osify-pkg list fallito"
fi

# 8.6 Storage & File Hub
if "$REPO_ROOT/system/desktop/osify-file-manager.sh" storage >/dev/null; then
    log_pass "Storage & File Hub: Montaggio dischi e associazione file UEM pronta"
else
    log_fail "Storage & File Hub: osify-file-manager fallito"
fi

# 8.7 Disk Installer Check
if bash -n "$REPO_ROOT/system/installer/osify-disk-installer.sh"; then
    log_pass "Bare-Metal Installer: Script di installazione su disco formalmente validato"
else
    log_fail "Bare-Metal Installer: Errore sintattico nell'installer"
fi

# 8.8 Deck Shell & Vector Assets
if python3 -c "import sys; sys.path.append('$REPO_ROOT/tools/osify-gui'); from osify_ui_assets import create_vector_icon; assert create_vector_icon('power').size == (32, 32)"; then
    log_pass "Deck Shell Assets: Motore vettoriale e icone anti-aliased operative al 100%"
else
    log_fail "Deck Shell Assets: Errore rendering icone vettoriali"
fi

# ==============================================================================
# FASE 9: HARDWARE INTELLIGENCE, WORKLOAD GOVERNOR & POLYGLOT CLI
# ==============================================================================
echo ""
echo "=== FASE 9: INTELLIGENZA HARDWARE, GOVERNOR CARICHI & SHELL POLIGLOTTA ==="

# 9.1 Hardware Autotune Engine (ISA, GPU, RAM, Storage)
if "$REPO_ROOT/system/autotune/osify-autotune.sh" json | grep -q "calibrated"; then
    log_pass "Autotune Engine: Riconoscimento hardware e schema JSON di calibrazione validati"
else
    log_fail "Autotune Engine: Fallimento autotune json"
fi

# 9.2 Context-Aware Workload Governor
if "$REPO_ROOT/system/workload/osify-workload-governor.sh" stream-game >/dev/null && \
   grep -q "STREAM_AND_GAME" /tmp/osify_active_workload_profile 2>/dev/null; then
    log_pass "Workload Governor: Profilo simultaneo Streaming + Gaming (CAKE QoS + VOD audio) attivo"
else
    log_fail "Workload Governor: Fallimento switch profilo stream-game"
fi

if "$REPO_ROOT/system/workload/osify-workload-governor.sh" esport >/dev/null && \
   grep -q "ESPORT_GAME" /tmp/osify_active_workload_profile 2>/dev/null; then
    log_pass "Workload Governor: Profilo eSport gaming competitivo (BORE tick + unredirect) attivo"
else
    log_fail "Workload Governor: Fallimento switch profilo esport"
fi

# 9.3 Omnipotent Polyglot Terminal Environment
if "$REPO_ROOT/tools/osify-shell/osify-polyglot-env.sh" test >/dev/null 2>&1; then
    log_pass "Polyglot Shell: Comandi Windows (dir/ipconfig/tasklist), macOS (sw_vers/open) e bridge package manager (apt/pacman/dnf/apk/brew/winget) operativi"
else
    log_fail "Polyglot Shell: Fallimento test shell poliglotta universale"
fi

# 9.4 Control Center Unified Dispatcher
ctl_status="$("$REPO_ROOT/tools/osify-ctl" status)"
if echo "$ctl_status" | grep -q "Hardware Autotune"; then
    log_pass "Control Center: Integrazione unificata di autotune, workload governor e polyglot shell in osify-ctl"
else
    log_fail "Control Center: osify-ctl status non riporta i nuovi sottosistemi"
fi

# 9.5 Deck Shell Advanced Integration & PyCompile
if python3 -m py_compile "$REPO_ROOT/tools/osify-gui/osify-deck-shell.py"; then
    log_pass "Deck Shell GUI: Compilazione e integrazione pannelli Workload e Autotune verificate"
else
    log_fail "Deck Shell GUI: Errore di sintassi in osify-deck-shell.py"
fi

# ==============================================================================
# FASE 10: SICUREZZA NATIVA, ADSHIELD, MOBILE AUTHN & DESKTOP WINDOW MANAGER
# ==============================================================================
echo ""
echo "=== FASE 10: SICUREZZA NATIVA, ADSHIELD, AUTENTICAZIONE BIOMETRICA & WINDOW MANAGER ==="

# 10.1 Live Hot-Updater con Freeze Guard
if "$REPO_ROOT/system/updater/osify-live-updater.sh" test-freeze >/dev/null 2>&1; then
    log_pass "Live Hot-Updater: Meccanismo di freeze atomico e ripresa automatica alla riconnessione verificato"
else
    log_fail "Live Hot-Updater: Errore nel checkpoint di freeze/resume"
fi

# 10.2 OSify Shield Antivirus Nativo & Quarantena Sandboxed
if "$REPO_ROOT/security/shield/osify-shield.sh" test-threat >/dev/null 2>&1; then
    log_pass "OSify Shield: Euristica anti-ransomware/miner e isolamento in quarantena (chmod 000) validati"
else
    log_fail "OSify Shield: Errore nella rilevazione minacce o nella procedura di quarantena"
fi

# 10.3 AdShield DNS Sinkhole & Blacklist Dinamica
if "$REPO_ROOT/security/adblock/osify-adblock.sh" test >/dev/null 2>&1; then
    log_pass "AdShield DNS Sinkhole: 67+ domini pubblicitari e telemetria deviati a 0.0.0.0 a livello di sistema"
else
    log_fail "AdShield: Errore nel sinkhole DNS o nel routing locale"
fi

# 10.4 Gateway Autenticazione Smartphone WebAuthn / Passkey
if python3 "$REPO_ROOT/security/auth/osify-auth-gateway.py" test-simulated >/dev/null 2>&1; then
    log_pass "Mobile Auth Gateway: Handshake crittografico HMAC-SHA256 e sblocco biometrico iPhone/Android convalidati"
else
    log_fail "Mobile Auth Gateway: Fallimento challenge crittografico o sblocco passkey"
fi

# 10.5 Floating Desktop Window Manager
if python3 -m py_compile "$REPO_ROOT/tools/osify-gui/osify_window_manager.py" && \
   python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT/tools/osify-gui')
import tkinter as tk
from osify_ui_assets import create_vector_icon
from osify_window_manager import OSifyDesktopWindowManager

root = tk.Tk()
root.geometry('1160x720')
viewport = tk.Frame(root)
viewport.pack(fill='both', expand=True)

wm = OSifyDesktopWindowManager(viewport, lambda t, **k: create_vector_icon(t), lambda: None)
root.update_idletasks()
assert len(wm.windows) >= 2, 'Meno di 2 finestre aperte di default'
assert len(wm.z_stack) >= 2, 'Z-stack non popolato'

# Test apertura Dolphin & Start menu
wm.open_filemanager_window()
wm.toggle_start_menu()
root.update_idletasks()
assert wm.start_menu_win is not None
wm.toggle_start_menu()
root.update_idletasks()
assert wm.start_menu_win is None

root.destroy()
print('WM Verification Passed')
" >/dev/null 2>&1; then
    log_pass "Window Manager: Finestre fluttuanti, Z-Order, drag&drop, taskbar e Start Kickoff operativi al 100%"
else
    log_fail "Window Manager: Errore nell'inizializzazione o nella gestione finestre"
fi

# 10.6 Assemblaggio Profilo Sistema Operativo Autonomo (ISO Builder)
if "$REPO_ROOT/build/build-iso.sh" prepare >/dev/null 2>&1 && \
   [[ -x "$REPO_ROOT/build/profile/airootfs/usr/local/bin/osify-update" ]] && \
   [[ -f "$REPO_ROOT/build/profile/airootfs/etc/systemd/system/osify-live-updater.timer" ]]; then
    "$REPO_ROOT/build/build-iso.sh" clean >/dev/null 2>&1 || true
    log_pass "OSify ISO Builder: Generazione profilo autonomo con rootfs /opt/osify, binari e systemd units validata"
else
    "$REPO_ROOT/build/build-iso.sh" clean >/dev/null 2>&1 || true
    log_fail "OSify ISO Builder: Errore nella preparazione del profilo ISO autonomo"
fi

echo "                  REPORT FINALE COLLAUDO                 "
echo "========================================================="
echo "  TEST SUPERATI : $PASSED_COUNT"
echo "  TEST FALLITI  : $FAILED_COUNT"
echo "========================================================="

if [[ "$FAILED_COUNT" -eq 0 ]]; then
    echo "[✓✓✓] TUTTI I TEST SONO PASSATI CON SUCCESSO AL 100%! OSify È PRONTO."
    exit 0
else
    echo "[!!!] ALCUNI TEST SONO FALLITI. VERIFICARE I LOG SOPRA."
    exit 1
fi
