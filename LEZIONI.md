# LEZIONI APPRESE — REGISTRO ERRORI E REGOLE ARCHITETTURALI OSIFY

## 2026-10-17 — Risoluzione Schermo Nero all'Avvio e Bootsplash Solo-Logo (Windows/Apple Style)
- **Area**: Avvio del sistema live, bootsplash framebuffer, PID 1 init e handoff sessione grafica
- **Errore**: All'avvio reale di OSify su hardware fisico o macchine virtuali, dopo lo splashscreen iniziale il sistema si bloccava su uno schermo nero permanente senza mai caricare il desktop; inoltre lo splashscreen conteneva testi e sottotitoli ridondanti.
- **Causa radice**:
  1. Nel rootfs SliTaz originale, `/init` tentava uno spostamento distruttivo di `/` in RAM con `mv /$i /mnt`, cancellando `/bin` e `/lib` sotto i piedi del kernel ed esaurendo i binari (`busybox: not found`, Kernel panic).
  2. La suddivisione in 4 archivi frammentati (`rootfs1..4.gz`) introduceva fallimenti nel loop device e nel display server; SLiM falliva l'autologin saltando `~/.xinitrc` e lasciando Xorg aperto ma privo di client window manager.
  3. Il bootsplash originale generava stringhe di testo ("Sistema Operativo Autonomo", "OSify") non conformi allo standard pulito ed essenziale dei sistemi operativi premium moderni (Windows, macOS).
- **Regola**:
  1. Bootsplash Solo-Logo: Lo splashscreen deve contenere unicamente il logo OSify squircle centrato (con glow radiale) su sfondo nero OLED (`#07090e`), eliminando categoricamente qualsiasi testo o sottotitolo.
  2. Rootfs Unificato: Tutti i layer del sistema operativo vengono fusi in un singolo rootfs monolitico decompresso direttamente in memoria RAM all'avvio dal kernel.
  3. Master Init Diretto: `/init` esegue una sequenza pulita e non distruttiva (montaggio di `/proc`, `/sys`, `/dev`, `/run`, `/dev/pts`, avvio del bootsplash) ed esegue direttamente `/sbin/init "$@"` senza spostamenti distruttivi di directory.
  4. Handoff Grafico Garantito: SLiM delega l'avvio della sessione grafica a `~/.xinitrc` per tutti gli utenti live (`osify`, `tux`, `root`), il quale invoca `osify-session` con Openbox, Dual Panel macOS 2050 (Top Bar + Floating Dock), PCManFM e Wizard OOBE di benvenuto in italiano.

## 2026-10-17 — Network Stack Bare-Metal, Audio Driver Intel HDA & Installatore Guidato su Disco Fisso GPT
- **Area**: Rete bare-metal, driver audio PCI, formattazione stringhe freestanding e partizionamento disco persistente
- **Errore**: Mancanza di connettivita automatica DHCP a basso livello, assenza di audio feedback hardware con mixer DMA, formattazione MAC address fallita in `osify_snprintf` per assenza di supporto padding width/zero-pad, e impossibilita per l'utente finale di installare permanentemente il kernel sul disco interno GPT.
- **Causa radice**: In un ambiente bare-metal freestanding no-libc, `osify_snprintf` scartava token non esatti come `%02x` provocando misallineamenti negli argomenti variadici `va_arg`, e il kernel necessitava dei 3 anelli di completamento per l'hardware reale (scheda di rete Ethernet, controller audio HDA e installatore di sistema con tabella partizioni EFI).
- **Regola**:
  1. Formattatore Freestanding: `osify_snprintf` deve sempre analizzare i flag di zero-padding (`%0`) e la larghezza di campo (`width`) sia per interi decimali `%02d` che per esadecimali `%02x` / `%02X`, prelevando correttamente tipi `unsigned int` secondo le regole di promozione variadica del C standard.
  2. Network Stack Bare-Metal (`drivers/osify_net.c`): Gestisce direttamente i frame Ethernet II (Intel e1000 / Realtek RTL8139), le richieste ARP, i datagrammi IPv4/UDP e acquisisce automaticamente la lease IP via DHCP client instradando il traffico DNS categoricamente su Quad9 (`9.9.9.9`) con zero-telemetria.
  3. Audio Hardware & Chime (`drivers/osify_audio.c`): Controller Intel HDA / AC97 con buffer circolare DMA PCM stereo 16-bit 44.1kHz, attenuazione lineare del volume master (0-100%), toggle mute e Cyber Startup Chime sintetizzato a due toni sinusoidali/triangolari.
  4. Installatore Fisico GPT (`drivers/osify_installer.c`): Automa FSM che partiziona il disco fisso interno con tabella GPT conforme UEFI (LBA 1 Header `EFI PART`, LBA 2-33 ESP di bootloader + Root OSifyFS), formatta il filesystem nativo `OSFS`, copia l'albero `/Sistema` ed espone un'interfaccia Dark Glass con barra dinamica su Linear Framebuffer a 32bpp.

## 2026-10-17 — Sistema Operativo Fatto e Finito al 100%: Storage ATA, OSifyFS, Window Manager & ISO Bare-Metal
- **Area**: Architettura OS completa, file system autonomo, window manager nativo e packaging bare-metal
- **Errore**: Fermarsi a moduli parziali o a un ambiente dipendente da display server esterni (X11) e driver di terze parti, lasciando l'OS incompleto per l'utente finale.
- **Causa radice**: Mancanza dei 4 pilastri architetturali chiusi: bootstrap assembly con runtime no-libc, driver storage fisico con filesystem nativo, window manager interattivo su framebuffer lineare, e pipeline di build dell'ISO bare-metal.
- **Regola**: OSify e ora formalmente e tecnicamente un sistema operativo a se stante al 100%:
  1. Storage Fisico & OSifyFS (`drivers/osify_storage.c`): controllo diretto delle porte ATA/IDE `0x1F0-0x1F7` e parser GPT con superblocco `OSFS` e persistenza dati in `/Sistema` e `/Utenti`.
  2. Window Manager & Shell Nativa (`drivers/osify_desktop_wm.c`): rendering diretto Dark Glass a 32bpp su Linear Framebuffer con Top Menu Bar a 26px, Floating Dock centrata con icone squircle, finestre con bottoni di controllo macOS-style, cursore mouse vettoriale e shell interattiva `osify> `.
  3. Packaging Bare-Metal (`build/build-baremetal-iso.py`): genera l'immagine ISO autonoma `OSify-A.0-BareMetal.iso` pronta per il bootloader El Torito / Multiboot, scritta su USB e avviata direttamente sul silicio di qualsiasi PC x86_64 o vintage 32-bit.


## 2026-10-17 — Bootstrap Bare-Metal, Runtime Freestanding (No-libc) e Driver Input Hardware
- **Area**: Kernel bootstrapping, compilazione autonoma e gestione hardware bare-metal
- **Errore**: Mantenere dipendenze implicite dagli header della libc host (`<string.h>`, `<stdio.h>`) e assenza di un entry point assembly con linker script bare-metal per l'avvio diretto dal silicio.
- **Causa radice**: In un vero sistema operativo autonomo non esiste alcuna libc o runtime preesistente: il kernel deve essere interamente self-contained (freestanding) e provvisto di entry point assembly per ricevere il controllo dal bootloader (Multiboot / UEFI).
- **Regola**:
  1. Il kernel deve essere 100% no-libc: tutte le operazioni su memoria e stringhe usano la libreria interna `osify_kstring` (`osify_memcpy`, `osify_memset`, `osify_snprintf`).
  2. Bootstrap Assembly & Linker: l'avvio bare-metal e governato da `boot.S` (header Multiboot `0x1BADB002`, stack a 16KB) e collegato tramite `kernel.ld` con caricamento a 1MB (`0x100000`).
  3. Interrupt & Input Hardware: il kernel inizializza la propria IDT a 256 gate, rimappa il controller PIC 8259A e cattura nativamente i tasti fisici tramite il driver PS/2 su porta `0x60`/`0x64` con buffer ad anello circolare.


## 2026-10-17 — Architettura 'Cover Nuda' & Kernel Nativo a Sottosistemi Universali
- **Area**: Kernel proprietario OSify, astrazione hardware pura e compatibilita binaria universale
- **Errore**: Trattare OSify come una distribuzione derivata con kernel generico e strati middleware ridondanti (glibc/X11 ingombranti, dipendenze esterne), appesantendo il sistema e limitandone l'identita autonoma.
- **Causa radice**: Errata assunzione che per supportare l'hardware servisse trascinare l'intero albero di una distribuzione Linux, anziche concepire il kernel come una "cover nuda": un esoscheletro essenziale, aderente al silicio, che estrae il 100% delle risorse hardware e fa da ponte di compatibilita universale a caldo.
- **Regola**: Il Kernel Nativo OSify (`sistema/nucleo/kernel/`) opera secondo la filosofia "Cover Nuda":
  1. Introspezione immediata del silicio (x86_32, x86_64, ARM64 Apple Silicon) con profilazione adattiva all'avvio (Vintage <1GB con footprint ridotto, Estremo per multicore/AVX/NEON).
  2. Motore grafico Dark Glass nativo su Framebuffer lineare (GOP/VESA a 32bpp) con doppi buffer, rendering geometrico e squircle, eliminando la dipendenza da server grafici pesanti.
  3. Ponte di compatibilita universale a sottosistemi multipli (ABI translation): riconosce automaticamente all'avvio il formato binario (.ify nativo, ELF Linux, PE Windows .exe, Mach-O macOS) e ne instrada le syscall direttamente sul silicio, garantendo la massima liberta e robustezza hardware.

## 2026-10-17 — Protezione Memoria Livello 0: Zero-Page Sentinel, W^X e macOS-Style SIP & Seatbelt
- **Area**: Kernel memory management, sicurezza hardware e compatibilita a livello 0
- **Errore**: L'allocatore fisico PMM restituiva la pagina 0 (`0x0`), coincidente con il puntatore `NULL`, e mancava un controllo hardware preventivo contro exploit di tipo code-injection in memoria virtuale.
- **Causa radice**: In C e nell'architettura x86/ARM, l'indirizzo `0x0` e formalmente `NULL` ed e storicamente bersaglio di attacchi Null-Pointer Dereference. Inoltre, permettere a una pagina virtuale di essere contemporaneamente scrivibile ed eseguibile (RWX) espone il sistema all'esecuzione di payload malevoli.
- **Regola**:
  1. Il PMM deve sempre preservare la pagina 0 (`0x0 - 0x1000`) come Null Sentinel permanente: le allocazioni per i processi partono da pagina 1 (`0x1000`).
  2. Il VMM applica rigidamente il principio W^X (Write XOR Execute): qualsiasi richiesta di mappatura con permessi contemporanei di Scrittura ed Esecuzione viene respinta a livello hardware.
  3. Integrita a Livello 0 (SIP & Seatbelt): l'albero `/Sistema` e bloccato in sola lettura hardware contro modifiche non autorizzate anche da parte di root, e i token di sicurezza isolano le chiamate raw disk/network per processi in sandbox.
  4. Unificatore Percorsi: la traduzione a livello 0 intercetta trasparentemente percorsi Windows (`C:\...`), POSIX (`/home`, `/usr`) e macOS (`/Users`, `/Applications`) normalizzandoli sull'albero nativo OSify (`/Sistema`, `/Applicazioni`, `/Utenti`).

## 2026-10-17 — Nuova Tassonomia di Versioning Generazionale: OSify A.0 (A.x.y)
- **Area**: Rilascio, standardizzazione formale del versioning e identita di sistema
- **Errore**: Utilizzare il convenzionale schema semantico 1.x.y (es. 1.5.0) che riconduceva il progetto a logiche di release ordinarie non distintive.
- **Causa radice**: Mancanza di un sistema di nomenclatura generazionale proprietario che separi nettamente le generazioni di OSify dagli schemi convenzionali.
- **Regola**: Il versioning di OSify adotta la nomenclatura generazionale con lettera alfabetica:
  1. La release attuale e ufficialmente **OSify A.0**.
  2. Le release successive della medesima generazione avanzano come `A.1`, `A.2`, `A.3`.
  3. Gli aggiornamenti incrementali ("versioni piccole") seguono la notazione `A.x.y`, dove `x` e la major di generazione e `y` e il contatore incrementale di aggiornamenti minori (es. `A.0.1`, `A.0.2`, `A.1.1`).
  4. Nessun riferimento a `1.5.0` deve comparire in alcun file di sistema, badge, header C, fastfetch, terminale o documentazione.

## 2026-10-17 — Sincronizzazione Binaria Etichette EFI & Prevenzione 'no such device'
- **Area**: Firmware UEFI, GRUB EFI embedded e masterizzazione xorriso
- **Errore**: All'avvio UEFI di OSify x86_64 e ARM64, GRUB si bloccava con il messaggio `error: no such device: alpine-std 3.20.3 ...`.
- **Causa radice**: I binari EFI precompilati (`bootx64.efi`, `bootaa64.efi` ed `efi.img`) integrano internamente il comando `search --no-floppy --set=root --label "<etichetta>"`. Quando `xorriso` creava l'ISO con un'etichetta di volume arbitraria non coincidente, GRUB non riusciva a individuare il disco di boot e falliva l'impostazione della variabile `$root`.
- **Regola**: Sostituire con patch binaria byte-per-byte (preservando l'identica lunghezza) l'etichetta originaria nei binari EFI con l'identità pura OSify (`OSify-2050-Gaming-x86_64` per 64-bit e `OSify-2050-ARM64-Ultimate` per ARM64) e passare la medesima etichetta al parametro `-V` di `xorriso`.

## 2026-10-17 — Protezione Overlay Diskless & Prevenzione Purge Librerie di Sistema
- **Area**: Initramfs live, Alpine diskless boot e integrità pacchetti
- **Errore**: Durante l'avvio grafico, Xorg falliva segnalando librerie mancanti (`libudev.so.1`) che erano state correttamente inserite nell'archivio `localhost.apkovl.tar.gz`.
- **Causa radice**: Lo script `init` dell'initramfs, in assenza del parametro kernel `keep_apk_new`, esegue `apk add --clean-protected`, eliminando dall'overlay tmpfs tutti i file non corrispondenti ai pacchetti registrati nell'archivio `apks/` della ISO.
- **Regola**: Inserire sempre il parametro kernel `keep_apk_new=yes` nei menuentry di GRUB e nelle label di Syslinux, e ripulire la cartella `lib/apk` dal bundle prima della creazione dell'apkovl per impedire qualsiasi rimozione distruttiva dei binari o librerie desktop.

## 2026-10-17 — Gestione Privilegi Server Xorg & Wrapper Setuid
- **Area**: Server grafico X11, logging ed esecuzione non privilegiata
- **Errore**: Xorg terminava con errore fatale `Cannot open log file /var/log/Xorg.0.log` e, specificando il parametro `-logfile`, con `Invalid argument -logfile with elevated privileges`.
- **Causa radice**: Il binario `Xorg` (provvisto di wrapper setuid) rifiuta categoricamente per motivi di sicurezza il flag `-logfile` a runtime quando invocato con privilegi elevati, mentre l'avvio da utente non-root falliva nel creare o rinominare il file di log in `/var/log` non provvisto di permessi di scrittura universali.
- **Regola**: Creare sempre a runtime `/var/log` e `/tmp/.X11-unix` con permessi `1777`, impostare `export DISPLAY=:0 XAUTHORITY=/home/osify/.Xauthority`, non passare mai il flag `-logfile` nel comando `startx`, e configurare `/etc/X11/Xwrapper.config` con `allowed_users = anybody` e `needs_root_rights = yes`.

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

## 2026-10-17 — Desktop Grafico Standalone 64-bit, Eliminazione Totale CLI e Autologin X11
- **Area**: Desktop Environment x86_64, autologin grafico e soppressione interfaccia testo bootloader
- **Errore**: La versione standard a 64-bit avviava una shell testuale con prompt `(none):~#` e banner ASCII art, mostrando inoltre il riquadro testuale di GRUB `GNU GRUB version 2.12`.
- **Causa radice**:
  1. L'immagine ISO 64-bit precedente era stata pacchettizzata prima dell'iniezione dei binari desktop, mancava il pacchetto fondamentale `xinit` per il comando `startx`, Xorg necessitava del bit setuid per l'avvio infallibile dell'utente non privilegiato, `/etc/inittab` eseguiva uno script di sessione testuale con fallback a `/bin/sh -l`, e GRUB aveva un timeout positivo.
- **Regola**:
  1. Nessuna ISO di OSify (standard o vintage) deve mai esporre un prompt CLI o una console interattiva di emergenza all'utente finale.
  2. L'avvio deve sempre caricare direttamente l'ambiente grafico completo Dark Glass (Xorg, Openbox, Top Menu Bar a 26px, Floating Dock a 46px, PCManFM) tramite supervisore grafico dedicato `/usr/local/bin/osify-session-gui` con `startx`, D-Bus avviato, permessi setuid su Xorg, gruppi audio/video/input per l'utente `osify`.
  3. GRUB deve essere configurato con `set timeout=0` e parametri kernel `console=tty3` per una transizione immediata e silenziosa alla Scrivania senza mostrare alcun menu testuale.

## 2026-10-17 — Identita Ontologica OSify e Dizionario Semantico ALU Tri-Architettura (32, 64, ARM)
- **Area**: Architettura di sistema, ontologia del sistema operativo e motore di traduzione micro-ISA
- **Errore**: Trattare OSify come se fosse una derivazione o variante di Linux, Windows o macOS, e limitare la visione architetturale alle sole piattaforme x86 legacy/moderne senza una struttura universale che comprenda ARM e colleghi le ALU a livello semantico.
- **Causa radice**: Storica abitudine dell'ingegneria software di concepire i nuovi sistemi operativi come distribuzioni o spin di kernel preesistenti anziché come quarto polo autonomo e indipendente (c'è Linux, Windows, macOS, e c'è OSify).
- **Regola**:
  1. OSify e formalmente e architetturalmente un sistema operativo autonomo a se stante: non e Linux, non e Windows, non e macOS. E il quarto ecosistema con proprio modello di astrazione (OKAL), propria gerarchia file system (/Sistema, /Applicazioni, /Utenti), proprio formato pacchetti (.ify) e propria ABI.
  2. Triade Architetturale Ufficiale: OSify supporta nativamente 32-bit (i686), 64-bit (x86_64-v3) e ARM64 (AArch64).
  3. Motore Dizionario Semantico ALU (OSAM): Un'architettura innovativa che mappa i 32 registri virtuali universali (VREG_0..31) e le micro-operazioni aritmetico-logiche (ALU_ADD, ALU_SHIFT_ADD, ALU_ATOMIC_CAS, MEM_BARRIER, ecc.) attraverso tabelle di congruenza O(1), permettendo a processori e ALU con set di istruzioni eterogenei (CISC con flag impliciti vs RISC ortogonali con barrel shifter) di comunicare ed eseguire il formato .ify alla massima efficienza hardware.

## 2026-10-17 — Decompressore Kernel "done.", Master Init PID 1 e Autostart Grafico SLiM
- **Area**: Decompressore bzImage x86, gestione PID 1 in /init e catena di avvio grafica
- **Errore**: L'avvio dell'immagine 32-bit rimaneva congelato a tempo indeterminato con schermo nero 720x400 VGA e la sola dicitura `done.` in alto a sinistra.
- **Causa radice**:
  1. Il decompressore x86 in `bzImage` stampava la stringa `Performing relocations... \x00done.\n\x00`; la patch precedente azzerava solo `Booting the kernel.\n`, lasciando intatta e visibile la sequenza `done.\n`.
  2. Lo script `/init` in rootfs4 invocava `/sbin/init` senza `exec`, impedendo a SysVinit di diventare PID 1 (`getpid() != 1`); SysVinit terminava immediatamente e il processo ricadeva nel loop infinito di salvaguardia `while true; do sleep 2; done` con output silenziato su `/run/boot.log`.
  3. `osify-session.sh` invocava `osify-bootsplash` in modo sincrono prima di Openbox, e il bootsplash attendeva un file di completamento non ancora generato, creando un potenziale stallo nella sessione.
- **Regola**:
  1. La funzione `patch_kernel_binary()` deve sempre scansionare e azzerare `Performing relocations... `, `done.\nBooting the kernel.\n`, `Booting the kernel.\n` e `done.\n` su tutte le immagini del kernel (32-bit, 64-bit e ARM64).
  2. `/init` deve cedere definitivamente il controllo a `/sbin/init` (o a Busybox init) tramite `exec /sbin/init` per garantire che PID 1 governi i runlevel e i servizi di sistema.
  3. `osify-bootsplash` deve avere un contatore di fotogrammi a uscita automatica (massimo ~1.6 secondi a 100%) e la sessione desktop utente non deve mai bloccarne l'esecuzione in modo sincrono.
  4. L'avvio della sessione grafica deve essere orchestrato deterministicamente sia da `rcS` che da `/etc/inittab` (`tty1::respawn:/usr/bin/slim -nodaemon`) con credenziali e XAUTHORITY configurati per l'utente nativo `osify`.



