#!/usr/bin/env python3
"""
OSify Interactive Desktop Server (by Andryx)
=============================================================================
Avvia il simulatore grafico completo di OSify in locale e apre direttamente
la finestra del browser nativo per consentire una prova interattiva completa:
- Sfondo ufficiale dark cyberpunk con logo OSify (niente sfondi generici!)
- Web Browser integrato pronto all'uso
- Control Center con switch profili (Gaming, Streaming, Vintage Netbook)
- Dock in stile macOS con effetto magnification e finestre a scomparsa
- Multitasking Mission Control e selettore risoluzione 1024x600 per Toshiba NB200
=============================================================================
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading

PORT = 7331
DIR = os.path.dirname(os.path.abspath(__file__))

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        # Silenzia i log di polling per non sporcare il terminale
        pass

def find_free_port(start_port):
    import socket
    p = start_port
    while p < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
        p += 1
    return start_port

def main():
    port = find_free_port(PORT)
    url = f"http://localhost:{port}"

    print("=========================================================")
    print("       OSify Interactive Live Desktop Simulator          ")
    print("=========================================================")
    print(f"[+] Ambiente pronto: {url}")
    print("[+] Apertura automatica nel browser in corso...")
    print("[i] Risoluzione attiva: Toshiba NB200 (1024x600) commutabile in 1080p")
    print("[i] Premi Ctrl+C nel terminale per arrestare.")
    print("=========================================================")

    # Apre automaticamente il browser
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    with socketserver.TCPServer(("127.0.0.1", port), QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[✓] Simulatore OSify arrestato.")

if __name__ == "__main__":
    main()
