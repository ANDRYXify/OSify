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

## 2026-10-16 — Eliminazione Menu Testuali Numerati, Preservazione Device Nodes e Risoluzione Kernel Panic
- **Area**: Bootloader Isolinux, initramfs rootfs4 CPIO e navigazione utente CLI/GUI
- **Errore**: Il sistema all'avvio mostrava un anacronistico menu numerato a testo anni '90 (`[1]`, `[2]`, ecc.) e su hardware reale (Toshiba NB200) andava in Kernel Panic con `find: not found`, `busybox: not found`, `exitcode=0x00000100`.
- **Causa radice**:
  1. Il remastering su macOS estraeva rootfs4 su disco scartando i 131 nodi di dispositivo hardware (`dev/console`, `dev/null`, `dev/zero`, `dev/loop*`, ecc.) e ricompattava con `bsdcpio`, privando il kernel Linux dei descrittori standard di I/O (fd 0, 1, 2) e causando il fallimento di tutte le redirezioni in `/init`.
  2. Lo script `/init` conteneva un controllo arbitrario di RAM libera al 100% che su macchine Atom a 1GB di RAM con rootfs residenti saltava il montaggio tmpfs, tentava di montare un'inesistente unità CD-ROM ottica e terminava PID 1 con codice di errore.
  3. Il bootloader utilizzava `vesamenu.c32` con etichette numerate esplicite anziché un avvio moderno silenzioso e pulito.
- **Regola**:
  1. L'utente non deve mai essere costretto a interagire con menu testuali numerati (`[1]`, `[2]`): l'avvio deve essere fluido e immediato in stile 2020+ (OLED Bootsplash pulito con `MENU HIDDEN`, timeout rapido, nessuna dicitura di timeout o tasti prompt, zero numeri nelle label) e nei terminali la navigazione deve avvenire esclusivamente tramite frecce direzionali e tasto Invio (o apertura automatica del Centro di Controllo GUI).
  2. La manipolazione di archivi CPIO initramfs deve avvenire sempre tramite motore nativo in memoria (`CpioArchive`) che preserva intatti tutti i device nodes con i rispettivi major/minor, permessi e ownership root:root.
  3. Il kernel deve essere sempre avviato con parametro `tmpram=0` e `/init` deve essere sempre patchato per garantire l'avvio diretto in memoria senza controlli restrittivi o fallback a lettori CD-ROM.

## 2026-10-16 — Sicurezza Autoadattiva, Privacy Vault e Zero-Trust OSify
- **Area**: Hardening del kernel, mitigazione minacce hardware/rete, telemetria zero e distruzione forense dati
- **Errore**: I sistemi operativi convenzionali lasciano attivi parametri kernel permissivi (ptrace non ristretto, ASLR debole, dmesg visibile a utenti non privilegiati, assenza di filtri anti-spoofing IP), trasmettono telemetria e query DNS in chiaro ai provider ISP, e sono vulnerabili a vettori hardware come BadUSB / Rubber Ducky su porte USB pubbliche.
- **Causa radice**: Mancanza di un demone di sicurezza contestuale autoadattivo e di un framework di privacy integrato a livello di sistema operativo.
- **Regola**:
  1. Il sistema deve applicare hardening restrittivo immediato al kernel (`randomize_va_space=2`, `kptr_restrict=2`, `dmesg_restrict=1`, `yama.ptrace_scope=2`, `protected_symlinks=1`, `protected_hardlinks=1`, `rp_filter=1`, `tcp_syncookies=1`).
  2. Sicurezza Autoadattiva in tempo reale: monitoraggio costante dell'ambiente di rete; se il sistema si connette a hotspot Wi-Fi pubblici (guest, airport, hotel, bar o reti aperte), il demone attiva automaticamente il profilo `ULTRA-STEALTH` (blocco porte, chiusura broadcast, MAC address randomization).
  3. Difesa BadUSB attiva: rilevamento immediato di dispositivi HID malevoli o tool di iniezione (Rubber Ducky, BadUSB, Flipper Zero, Teensy) con disabilitazione immediata dell'autorizzazione USB a livello sysfs (`authorized=0`).
  4. Privacy Vault & Zero-Telemetry: variabile globale `DO_NOT_TRACK=1`, blocco delle telemetrie di terze parti, instradamento DNS sicuro e crittografato su resolver zero-log (Quad9 `9.9.9.9` con DoH/TLS), cancellazione periodica del buffer appunti (`clipboard`), e Kill-Switch di emergenza per disconnessione radio e azzeramento sessione in un clic.
  5. Distruzione Forense dei Dati: eliminazione sicura con sovrascrittura crittografica multi-pass DoD 5220.22-M a tre stadi (dati casuali, azzeramento, troncamento) per impedire qualsiasi recupero forense.

## 2026-10-16 — Bootsplash Framebuffer Nativo, Soppressione Console Kernel e Master Init OSify
- **Area**: Avvio di sistema, bootsplash grafico, soppressione log console e gestione PID 1
- **Errore**: All'avvio compariva uno splash statico con barra finta e testo grezzo, seguito da una schermata di scritte di log del kernel Linux e dal crash `/init: line 134: find: not found`, `line 349: busybox: not found`, `exitcode=0x00000100`.
- **Causa radice**:
  1. Lo script `/init` di SliTaz spostava i file da `/` a `/mnt` con `mv /$i /mnt`, distruggendo i percorsi standard `/bin` e `/sbin`, cercava un CD-ROM inesistente chiamando `find` e `busybox` spostati, e terminava con `exit` (provocando il Kernel Panic immediato poiché PID 1 non può mai uscire).
  2. Il bootloader utilizzava un'immagine JPEG con finta barra statica disegnata a mano e parametri kernel senza soppressione console, lasciando attivi `loglevel`, `dmesg` e `fbcon` sulla TTY1 visibile all'utente.
- **Regola**:
  1. Lo script `/init` in rootfs4 deve essere sempre il Master Init proprietario di OSify: monta i filesystem virtuali (`proc`, `sysfs`, `devtmpfs`, `devpts`, `run`), popola i device nodes con `mdev -s`, non sposta mai file distruttivamente, sopprime i log della console con `exec 1>/run/boot.log 2>&1` ed esegue definitivamente `/sbin/init` via `exec` (garantendo che PID 1 non esca mai).
  2. Il bootloader ISOLINUX/SYSLINUX deve utilizzare uno sfondo OLED nero minimale (`#07090e`) con il logo OSify squircle luminescente centrale in alta definizione, dicitura pulita del brand, zero barre finte statiche e parametri kernel `quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo fbcon=map:3 rd.systemd.show_status=false rd.udev.log_priority=0 udev.log_priority=0`.
  3. L'animazione di caricamento reale deve essere gestita da un binario statico nativo C a 32-bit (`osify-bootsplash`) renderizzato direttamente su `/dev/fb0` con alpha blending, barra dinamica in tempo reale a 30 FPS e shimmer neon, con handoff automatico al display manager prima dell'apertura del desktop.

## 2026-10-17 — Compatibilità UEFI Universale, Fallback EDK II e Script startup.nsh
- **Area**: Firmware UEFI, macchine virtuali macOS (UTM/QEMU) e immagini ISO 64-bit
- **Errore**: All'avvio della ISO standard a 64-bit su emulatore UEFI o firmware EDK II, il sistema non avviava il bootloader e cadeva nella "UEFI Interactive Shell v2.2".
- **Causa radice**: In assenza di una voce di boot registrata in NVRAM o su drive CD-ROM secondari (`CDROM(0x1)`), il firmware EDK II cerca per 1 secondo uno script `startup.nsh` nella radice del filesystem e, se non lo trova, interrompe la sequenza automatica aprendo la shell interattiva invece di scorrere le partizioni El Torito.
- **Regola**:
  1. Ogni immagine ISO con supporto UEFI deve includere obbligatoriamente un file `startup.nsh` (e `STARTUP.NSH`) nella radice del filesystem con comandi batch per mappare `fs0:`, `fs1:`, `fs2:` e lanciare automaticamente `\EFI\BOOT\BOOTX64.EFI`.
  2. Il file di configurazione GRUB deve essere replicato in tutte le posizioni standard (`boot/grub/grub.cfg`, `efi/boot/grub.cfg`, `EFI/BOOT/grub.cfg`) per supportare indistintamente firmware BIOS legacy, UEFI a 32-bit e UEFI a 64-bit.

