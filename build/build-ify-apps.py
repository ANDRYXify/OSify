#!/usr/bin/env python3
"""
==============================================================================
OSify Native .ify Application Suite Builder
==============================================================================
Ingegnerizzato per il Compagno Andrea Taliento (ANDRYXify)
Genera la suite completa di bundle applicativi nativi .ify con metadati
rigorosamente in italiano, manifesti, icone squircle e script di avvio.
==============================================================================
"""

import os
import json
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APPS_DIR = os.path.join(REPO_ROOT, "applicazioni")
ICONS_SRC = os.path.join(REPO_ROOT, "desktop/branding/icons/128")

SUITE = [
    {
        "id": "com.osify.centro",
        "cartella": "Centro OSify.ify",
        "nome": "Centro OSify",
        "versione": "2050.1.0",
        "descrizione": "Plancia di comando unificata, telemetria hardware, turbo boost e centro operativo",
        "categoria": "Sistema",
        "icona_src": "osify-hub.png",
        "comando": "/usr/bin/osify-hub"
    },
    {
        "id": "com.osify.navigatore",
        "cartella": "Navigatore.ify",
        "nome": "Navigatore",
        "versione": "2050.1.0",
        "descrizione": "Navigatore Web ultra-veloce con motore di rendering nativo e protezione tracciamento",
        "categoria": "Rete",
        "icona_src": "osify-browser.png",
        "comando": "/usr/bin/osify-browser"
    },
    {
        "id": "com.osify.esplora",
        "cartella": "Esplora.ify",
        "nome": "Esplora",
        "versione": "2050.1.0",
        "descrizione": "Gestione e navigazione visuale di dischi, partizioni e cartelle personali in italiano",
        "categoria": "Sistema",
        "icona_src": "osify-files.png",
        "comando": "pcmanfm"
    },
    {
        "id": "com.osify.reti",
        "cartella": "Reti.ify",
        "nome": "Reti",
        "versione": "2050.1.0",
        "descrizione": "Gestione connessioni senza fili Wi-Fi, Ethernet cablata, hotspot e sicurezza WPA2/WPA3",
        "categoria": "Rete",
        "icona_src": "osify-wifi.png",
        "comando": "/usr/bin/osify-wifi"
    },
    {
        "id": "com.osify.giochi",
        "cartella": "Giochi.ify",
        "nome": "Giochi",
        "versione": "2050.1.0",
        "descrizione": "Piattaforma gaming universale: titoli moderni, retrogaming DOS e ottimizzazione frame rate",
        "categoria": "Intrattenimento",
        "icona_src": "osify-games.png",
        "comando": "/usr/bin/osify-games"
    },
    {
        "id": "com.osify.sviluppo",
        "cartella": "Sviluppo.ify",
        "nome": "Sviluppo",
        "versione": "2050.1.0",
        "descrizione": "Ambiente integrato di ingegneria del software: Python, C, Git e strumenti di sviluppo",
        "categoria": "Sviluppo",
        "icona_src": "osify-developer.png",
        "comando": "/usr/bin/osify-developer"
    },
    {
        "id": "com.osify.aspetto",
        "cartella": "Aspetto.ify",
        "nome": "Aspetto",
        "versione": "2050.1.0",
        "descrizione": "Personalizzazione grafica del desktop, temi Dark Obsidian, sfondi ufficiali e Virtual Scaler",
        "categoria": "Impostazioni",
        "icona_src": "osify-appearance.png",
        "comando": "/usr/bin/osify-appearance"
    },
    {
        "id": "com.osify.monitor",
        "cartella": "Monitor.ify",
        "nome": "Monitor",
        "versione": "2050.1.0",
        "descrizione": "Monitoraggio in tempo reale di memoria RAM, carico del processore, temperature e processi attivi",
        "categoria": "Sistema",
        "icona_src": "osify-taskmanager.png",
        "comando": "/usr/bin/osify-taskmanager"
    },
    {
        "id": "com.osify.impostazioni",
        "cartella": "Impostazioni.ify",
        "nome": "Impostazioni",
        "versione": "2050.1.0",
        "descrizione": "Pannello di controllo centralizzato per periferiche, audio, schermo, account e sicurezza",
        "categoria": "Impostazioni",
        "icona_src": "osify-settings.png",
        "comando": "/usr/bin/osify-settings"
    },
    {
        "id": "com.osify.negozio",
        "cartella": "Negozio.ify",
        "nome": "Negozio",
        "versione": "2050.1.0",
        "descrizione": "Catalogo ufficiale per l'installazione e l'aggiornamento sicuro di pacchetti nativi .ify",
        "categoria": "Sistema",
        "icona_src": "osify-hub.png",
        "comando": "/usr/bin/osify-package-installer"
    },
    {
        "id": "com.osify.galleria",
        "cartella": "Galleria.ify",
        "nome": "Galleria",
        "versione": "2050.1.0",
        "descrizione": "Visualizzatore grafico di immagini, fotografie e illustrazioni ad alta risoluzione",
        "categoria": "Grafica",
        "icona_src": "osify-drawer.png",
        "comando": "/usr/bin/osify-image-viewer"
    },
    {
        "id": "com.osify.musica",
        "cartella": "Musica.ify",
        "nome": "Musica",
        "versione": "2050.1.0",
        "descrizione": "Riproduttore audio ad alta fedeltà con gestione canali e equalizzazione a bassa latenza",
        "categoria": "Audio",
        "icona_src": "osify-audio.png",
        "comando": "/usr/bin/osify-media-player"
    },
    {
        "id": "com.osify.video",
        "cartella": "Video.ify",
        "nome": "Video",
        "versione": "2050.1.0",
        "descrizione": "Centro multimediale di riproduzione video e acquisizione dello schermo ad alte prestazioni",
        "categoria": "Video",
        "icona_src": "osify-capture.png",
        "comando": "/usr/bin/osify-video-capture"
    },
    {
        "id": "com.osify.documenti",
        "cartella": "Documenti.ify",
        "nome": "Documenti",
        "versione": "2050.1.0",
        "descrizione": "Lettore di manuali, documenti PDF, schemi tecnici e testi digitali",
        "categoria": "Ufficio",
        "icona_src": "osify-notepad.png",
        "comando": "/usr/bin/osify-pdf-viewer"
    },
    {
        "id": "com.osify.archivi",
        "cartella": "Archivi.ify",
        "nome": "Archivi",
        "versione": "2050.1.0",
        "descrizione": "Gestore di compressione ed estrazione pacchetti e archivi universali",
        "categoria": "Utility",
        "icona_src": "osify-archive.png",
        "comando": "/usr/bin/osify-archive-manager"
    },
    {
        "id": "com.osify.cattura",
        "cartella": "Cattura.ify",
        "nome": "Cattura",
        "versione": "2050.1.0",
        "descrizione": "Strumento di cattura istantanea dello schermo a risoluzione nativa",
        "categoria": "Utility",
        "icona_src": "osify-capture.png",
        "comando": "/usr/bin/osify-screenshot"
    },
    {
        "id": "com.osify.calcolatrice",
        "cartella": "Calcolatrice.ify",
        "nome": "Calcolatrice",
        "versione": "2050.1.0",
        "descrizione": "Calcolatrice scientifica e di programmazione in tempo reale",
        "categoria": "Utility",
        "icona_src": "osify-calculator.png",
        "comando": "/usr/bin/osify-calculator"
    },
    {
        "id": "com.osify.note",
        "cartella": "Note.ify",
        "nome": "Note",
        "versione": "2050.1.0",
        "descrizione": "Taccuino rapido per appunti, documentazione e scrittura di testi",
        "categoria": "Ufficio",
        "icona_src": "osify-notepad.png",
        "comando": "/usr/bin/osify-notepad"
    },
    {
        "id": "com.osify.aggiornamenti",
        "cartella": "Aggiornamenti.ify",
        "nome": "Aggiornamenti",
        "versione": "2050.1.0",
        "descrizione": "Verifica e applicazione atomica di aggiornamenti di sistema e sicurezza per OSify",
        "categoria": "Sistema",
        "icona_src": "osify-update.png",
        "comando": "/usr/bin/osify-update"
    },
    {
        "id": "com.osify.installa",
        "cartella": "Installa OSify.ify",
        "nome": "Installa OSify",
        "versione": "2050.1.0",
        "descrizione": "Installatore guidato e autonomo per rendere permanente OSify sul disco fisso interno",
        "categoria": "Sistema",
        "icona_src": "osify-install.png",
        "comando": "/usr/bin/osify-install-gui"
    },
    {
        "id": "com.osify.dispositivi",
        "cartella": "Dispositivi.ify",
        "nome": "Dispositivi",
        "versione": "2050.1.0",
        "descrizione": "Gestione periferiche fisiche, porte USB, stampanti, scanner, controller e webcam",
        "categoria": "Sistema",
        "icona_src": "osify-usb.png",
        "comando": "/usr/bin/osify-settings"
    },
    {
        "id": "com.osify.accessibilita",
        "cartella": "Accessibilità.ify",
        "nome": "Accessibilità",
        "versione": "2050.1.0",
        "descrizione": "Ingranditore schermo ad alto contrasto, sintesi vocale e tastiera su schermo",
        "categoria": "Sistema",
        "icona_src": "osify-accessibility.png",
        "comando": "/usr/bin/osify-accessibility"
    },
    {
        "id": "com.osify.ripristino",
        "cartella": "Ripristino.ify",
        "nome": "Ripristino",
        "versione": "2050.1.0",
        "descrizione": "Salvataggio atomico e ripristino istantaneo di dati, profili e snapshot di sistema",
        "categoria": "Sistema",
        "icona_src": "osify-backup.png",
        "comando": "/usr/bin/osify-backup"
    },
    {
        "id": "com.osify.compatibilita",
        "cartella": "Compatibilità.ify",
        "nome": "Compatibilità",
        "versione": "2050.1.0",
        "descrizione": "Esecutore universale per formati PC (.exe), Mobili (.apk), Darwin (.app) e Anti-Cheat Guard",
        "categoria": "Sistema",
        "icona_src": "osify-hub.png",
        "comando": "/usr/bin/osify-controlcenter"
    }
]

def main():
    os.makedirs(APPS_DIR, exist_ok=True)
    print(f"[*] Generazione suite applicativa nativa .ify in {APPS_DIR}...")

    for app in SUITE:
        bundle_path = os.path.join(APPS_DIR, app["cartella"])
        os.makedirs(bundle_path, exist_ok=True)

        # 1. Scrivi manifesto.json
        manifest = {
            "id": app["id"],
            "nome": app["nome"],
            "versione": app["versione"],
            "descrizione": app["descrizione"],
            "categoria": app["categoria"],
            "icona": "icona.png",
            "eseguibile": "avvia.sh",
            "permessi": ["grafica", "input", "disco", "audio"],
            "autore": "OSify Systems"
        }
        with open(os.path.join(bundle_path, "manifesto.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # 2. Copia icona squircle
        icon_src = os.path.join(ICONS_SRC, app["icona_src"])
        if not os.path.exists(icon_src):
            icon_src = os.path.join(REPO_ROOT, "desktop/branding/icons/48", app["icona_src"])
        if os.path.exists(icon_src):
            shutil.copy2(icon_src, os.path.join(bundle_path, "icona.png"))

        # 3. Scrivi avvia.sh
        avvia_sh = os.path.join(bundle_path, "avvia.sh")
        with open(avvia_sh, "w", encoding="utf-8") as f:
            f.write(f"""#!/bin/sh
# Avvio di {app["nome"]} per OSify
exec {app["comando"]} "$@"
""")
        os.chmod(avvia_sh, 0o755)

        print(f"[+] Generato bundle: {app['cartella']}")

    print(f"[[OK]] {len(SUITE)} applicazioni native .ify generate con successo!")

if __name__ == "__main__":
    main()
