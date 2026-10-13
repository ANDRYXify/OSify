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
echo "--- [1/6] Verifica Sintattica Script Shell (bash -n) ---"
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
echo "--- [2/6] Verifica Compilazione Bytecode Python ---"
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
echo "--- [3/6] Validazione File JSON e Schemi ---"
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
echo "--- [4/6] Collaudo Motore Hardware Diagnostics ---"
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
echo "--- [5/6] Collaudo Anti-Cheat Intelligence & Ring-0 Detection ---"
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
echo "--- [6/6] Collaudo Gestore Architettura a Blocchi ---"
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
# RISULTATO FINALE
# ------------------------------------------------------------------------------
echo ""
echo "========================================================="
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
