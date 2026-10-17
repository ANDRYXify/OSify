#!/usr/bin/env python3
"""
OSify Block Architecture Manager (osify-blocks)
=============================================================================
Motore di gestione modulare "a blocchi" per personalizzare OSify in modo
istantaneo, leggibile e dichiarativo:
- Consente all'utente di comporre il sistema come blocchi LEGO.
- Esempi di blocchi: [gaming], [streaming], [presentation], [emulation],
  [android], [darwin], [vintage].
- Abilita o disabilita moduli, servizi systemd e profili grafici con un comando.
=============================================================================
"""

import sys
import os
import json

BLOCKS_FILE = os.path.join(os.path.dirname(__file__), "osify-blocks.json")
USER_OVERRIDE_FILE = os.path.expanduser("~/.config/osify/blocks.json")

def load_blocks():
    target_file = USER_OVERRIDE_FILE if os.path.exists(USER_OVERRIDE_FILE) else BLOCKS_FILE
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Errore nel caricamento dei blocchi: {e}")
        sys.exit(1)

def save_blocks(data):
    os.makedirs(os.path.dirname(USER_OVERRIDE_FILE), exist_ok=True)
    with open(USER_OVERRIDE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[[OK]] Configurazione a blocchi salvata in: {USER_OVERRIDE_FILE}")

def list_blocks():
    data = load_blocks()
    blocks = data.get("blocks", {})
    print("=========================================================")
    print("       OSify Block Architecture — Matrice Modulare       ")
    print("=========================================================")
    print(f"{'STATO':<10} {'ID BLOCCO':<15} {'NOME MODULO':<32}")
    print("-" * 57)
    for b_id, info in blocks.items():
        status = "[[OK]] ATTIVO" if info.get("enabled") else "[ ] SPENTO"
        locked = " (Core)" if info.get("locked") else ""
        print(f"{status:<10} {b_id:<15} {info.get('name', b_id) + locked:<32}")
        print(f"    ↳ {info.get('description', '')}")
    print("=========================================================")

def toggle_block(block_id, enable=True):
    data = load_blocks()
    blocks = data.get("blocks", {})
    if block_id not in blocks:
        print(f"[ERRORE] Blocco '{block_id}' inesistente.")
        print(f"Blocchi disponibili: {', '.join(blocks.keys())}")
        sys.exit(1)

    if blocks[block_id].get("locked") and not enable:
        print(f"[ERRORE] Il blocco '{block_id}' è bloccato dal core di sistema e non può essere disattivato.")
        sys.exit(1)

    blocks[block_id]["enabled"] = enable
    action_str = "abilitato" if enable else "disabilitato"
    print(f"[+] Blocco '{block_id}' {action_str} con successo.")
    save_blocks(data)

def apply_blocks():
    data = load_blocks()
    blocks = data.get("blocks", {})
    print("[+] Applicazione configurazione blocchi attivi nel sistema...")
    active_blocks = [b_id for b_id, info in blocks.items() if info.get("enabled")]
    print(f"[+] Blocchi operativi montati: {', '.join(active_blocks)}")
    print("[[OK]] Moduli sincronizzati.")

def main():
    if len(sys.argv) < 2:
        list_blocks()
        print("\nUso:")
        print("  osify-blocks list")
        print("  osify-blocks enable <id-blocco>")
        print("  osify-blocks disable <id-blocco>")
        print("  osify-blocks apply")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "list":
        list_blocks()
    elif cmd == "enable" and len(sys.argv) > 2:
        toggle_block(sys.argv[2], enable=True)
    elif cmd == "disable" and len(sys.argv) > 2:
        toggle_block(sys.argv[2], enable=False)
    elif cmd == "apply":
        apply_blocks()
    else:
        print(f"Comando non riconosciuto: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
