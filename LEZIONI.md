# LEZIONI APPRESE — REGISTRO ERRORI E REGOLE ARCHITETTURALI OSIFY

## 2026-10-16 — Desktop Environment & macOS Experience
- **Area**: Desktop layout, branding ed estetica utente
- **Errore**: Il sistema presentava un'unica barra monolitica inferiore e un desktop ingombro, mancando dell'identità visiva distintiva macOS 2050 e del brand OSify.
- **Causa radice**: Configurazione standard a singolo pannello ereditata da template minimali Linux senza la separazione tra Menu Bar superiore e Dock fluttuante inferiore.
- **Regola**: Utilizzare sempre l'architettura dual-panel (Top Menu Bar a 26px con menu OSify Apple-style + Floating Dock centrata staccata dal fondo a 46px), ricerca universale Spotlight (Super+Spazio) e Scrivania ultra-pulita priva di icone ridondanti.

## 2026-10-16 — Bootloader Splash, First-Boot OOBE e Iconografia Squircle Brand OSify
- **Area**: Avvio di sistema, configuratore iniziale e brand design
- **Errore**: Assenza di una sequenza di boot professionale guidata (Bootsplash con logo luminescente e barra di progresso, setup wizard al primissimo avvio) e icone non coordinate con il brand OSify.
- **Causa radice**: Bootloader standard privo di splash screen dedicato e assenza di un supervisor di primo avvio universale a doppio engine (GTK2/YAD per sistemi vintage ultra-leggeri e Python3/Tkinter per sistemi moderni).
- **Regola**: Il bootloader deve sempre integrare il Bootsplash OLED con barra centrata sottile senza sovrapposizioni di testo del menu. Il primo avvio deve sempre presentare l'assistente OOBE Dark Glass per lingua, tastiera, Wi-Fi e account utente prima di sbloccare la Scrivania, con icone squircle macOS ad alta definizione (16px -> 512px) derivate dalla palette neon del logo OSify.
## 2026-10-16 — Sistema Operativo Autonomo a sé Stante (.ify & File System Italiano)
- **Area**: Architettura di sistema, pacchettizzazione nativa e identità autonoma
- **Errore**: Presenza di residui lessicali distro e componenti applicativi non incapsulati nel formato nativo .ify, con percorsi UNIX standard anziché l'albero nativo in lingua italiana.
- **Causa radice**: Eredità dei file di configurazione e script di remastering legati alla convenzione classica senza una standardizzazione formale del formato pacchetto proprietario .ify e dell'albero /Sistema, /Applicazioni, /Utenti.
- **Regola**: OSify è esclusivamente un sistema operativo autonomo a sé stante: tutte le app e servizi devono essere incapsulati nel formato .ify con manifesto.json e icona squircle, i percorsi visibili devono risiedere in /Sistema, /Applicazioni e /Utenti, nessun nome o terminologia di distribuzioni terze o emulatori deve comparire nell'interfaccia o nella documentazione, e non devono essere presenti emoji nel codice di sistema o nei menu.
