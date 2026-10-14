#!/usr/bin/env bash
# ==============================================================================
# OSify Virtual Keyboard — Tastiera a Schermo di Emergenza & Accessibilita
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Indispensabile per netbook con tasti rotti, touch screen o accessibilita.
# ==============================================================================

set -euo pipefail

# 1. Prova strumenti X11 nativi
for k in xvkbd onboard florence matchbox-keyboard; do
    if command -v "$k" >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        exec "$k"
    fi
done

# 2. Tastiera virtuale integrata Python Tkinter a costo zero
if command -v python3 >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    python3 -c "
import tkinter as tk
import subprocess

root = tk.Tk()
root.title('Tastiera a Schermo OSify')
root.attributes('-topmost', True)
root.geometry('580x190')
root.configure(bg='#0b0d14')

keys = [
    ['1','2','3','4','5','6','7','8','9','0','-','+','Bksp'],
    ['q','w','e','r','t','y','u','i','o','p'],
    ['a','s','d','f','g','h','j','k','l',';','Invio'],
    ['z','x','c','v','b','n','m',',','.','/','Spazio']
]

def press(k):
    if k == 'Bksp':
        subprocess.run(['xdotool', 'key', 'BackSpace'], capture_output=True)
    elif k == 'Invio':
        subprocess.run(['xdotool', 'key', 'Return'], capture_output=True)
    elif k == 'Spazio':
        subprocess.run(['xdotool', 'key', 'space'], capture_output=True)
    else:
        subprocess.run(['xdotool', 'type', k], capture_output=True)

for r_idx, row in enumerate(keys):
    f = tk.Frame(root, bg='#0b0d14')
    f.pack(fill='x', expand=True, padx=4, pady=2)
    for k in row:
        btn = tk.Button(f, text=k, font=('sans-serif', 10, 'bold'),
                        bg='#1e293b', fg='#38bdf8', activebackground='#0ea5e9', activeforeground='#ffffff',
                        relief='flat', padx=6, pady=4, command=lambda key=k: press(key))
        btn.pack(side='left', fill='both', expand=True, padx=2)

root.mainloop()
" 2>/dev/null && exit 0
fi

echo "[!] Impossibile avviare la tastiera a schermo."
