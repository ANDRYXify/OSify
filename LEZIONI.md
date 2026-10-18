# LEZIONI APPRESE — REGISTRO ERRORI E REGOLE ARCHITETTURALI OSIFY

## LE 7 LEGGI INVIOLABILI DEL CODICE OSIFY (CONTROPIANO SOVRANO v2.0)
1. **Isolamento Architetturale Assoluto**: Nessun registro di controllo CPU (`CR3`, `TTBR0`, `satp`), istruzione assembly o primitiva di virtualizzazione (`vmxon`, `hvc`) può comparire fuori da `sistema/nucleo/arch/<arch>/`.
2. **Principio del Superset Nativo**: Quando un sottosistema del kernel viene progettato (IPC `RingBus`, sincronizzazione `WaitMux`, VMM multi-granularità, TLS switching), deve essere un *superset* proprietario capace di soddisfare nativamente OSify, Windows NT, macOS Darwin e Linux, mai un clone limitato di uno solo di essi.
3. **Sicurezza Hardware prima della Compatibilità Cieca**: Nessun codice binario di terze parti (driver `.sys`, `.kext`, moduli kernel esterni) può mai entrare nel Ring 0 nativo di OSify; qualsiasi driver esterno a livello kernel deve essere confinato in una **Cella Aegis (HVCS)** via `arch_hv.h` (SLAT/EPT/Stage-2).
4. **Zero Indirizzi Magici**: Nessun driver può usare porte I/O o indirizzi MMIO cablati nel codice (eccetto i driver esplicitamente confinati in `driver/x86_legacy/` per target Vintage i686); tutta la scoperta hardware avviene via PCIe ECAM, ACPI o DeviceTree.
5. **Verità Ingegneristica nei Test**: Una funzionalità è considerata "Operativa" nella documentazione solo quando possiede un test automatizzato reale che la verifica empiricamente.
6. **Imposizione W^X Incondizionata**: Nessuna pagina di memoria — né nel kernel, né in userspace, né nei traduttori JIT — può mai avere contemporaneamente i bit di Scrittura ed Esecuzione attivi (`OSIFY_MAP_W | OSIFY_MAP_X` restituisce sempre errore in `arch_mmu_map`).
7. **Purezza delle Licenze**: Il codice del kernel e delle librerie di sistema deve essere 100% originale o compatibile con la licenza del progetto; è tassativamente vietato copiare codice GPLv2-only dal kernel Linux.

## 2026-10-18 — System Call Dispatcher: Troncamento Puntatori su Host a 64-bit e Salvaguardia IOPL Seriale
- **Area**: Sottosistema System Call (`osify_syscall.c`, `test_kernel_skin.c`), Gestione Privilegi Ring 3 e Portabilità 32/64 bit
- **Errore**: Durante l'esecuzione dei test avanzati del kernel (`test_osify_kernel`) su macchina di sviluppo host a 64-bit, il processo subiva un `EXC_BAD_ACCESS` (SIGSEGV a riga `str w8, [x1]`) al collaudo del vettore `SYS_MEM_STATS`.
- **Causa radice**:
  1. Il passaggio di puntatori allocati sullo stack host a 64-bit (`&ram_tot`, `&ram_free`) subiva un cast esplicito a `uint32_t`, troncando i 32 bit superiori dell'indirizzo virtuale (es. `0x16f9291d0` -> `0x6f9291d0`). Quando il dispatcher de-referenziava il puntatore castato (`*p_total = 2048`), accedeva a una pagina non mappata.
  2. La routine di emissione seriale `osify_serial_print` eseguiva istruzioni di I/O su porta fisica (`inb`/`outb` a `0x3F8`) senza verificare se l'hardware seriale fosse attivo o se l'ambiente di esecuzione fosse a Ring 3, scatenando violazioni di privilegio IOPL sui sistemi host.
- **Regola**:
  1. Tipi uintptr_t Obbligatori nei Dispatcher: Tutti i registri di transito per argomenti generici o puntatori (`a1`, `a2`, `a3`) devono impiegare categoricamente `uintptr_t`, garantendo l'integrità dei puntatori sia in Ring 0 bare-metal a 32 bit che in ambienti host/emulati a 64 bit.
  2. Gate di Attivazione I/O Seriale: Le istruzioni `inb`/`outb` su porte fisiche devono essere subordinate al flag di inizializzazione reale `g_serial_hw_active`, prevenendo tentativi illegittimi di I/O in contesti Ring 3.

## 2026-10-18 — Kernel Nativo Bare-Metal: Registri Vettoriali SSE/XMM, Inizializzazione CR0/CR4 e Protezione Anti-Triple-Fault IDT
- **Area**: Kernel Nativo Bare-Metal C freestanding (`osify_kernel.elf`), Bootstrap Assembly (`boot.S`), Interrupt Descriptor Table (`osify_idt.c`) e compilazione Clang/LLVM
- **Errore**: All'avvio del kernel su macchina virtuale QEMU o silicio bare-metal, la macchina subiva un riavvio istantaneo in loop (triple-fault) subito dopo aver stampato la stringa di inizializzazione IDT (`[1/10]`).
- **Causa radice**:
  1. Durante la compilazione del codice freestanding con Clang a 32-bit (`-target i386-unknown-none-elf -O2`), il compilatore ha auto-vettorizzato le funzioni di memoria standard (`osify_memset`) emettendo istruzioni SSE (`movd %ebx, %xmm0`, `movdqu %xmm0, ...`).
  2. All'avvio in 32-bit Protected Mode da Multiboot, il processore x86 ha le estensioni SSE disabilitate nei registri di controllo (`CR4.OSFXSR` bit 9 a 0, e `CR0.EM` bit 2 attivo). L'esecuzione di qualsiasi istruzione XMM senza abilitazione preventiva scatena un'eccezione hardware immediata `#UD` (Invalid Opcode, Vector 6).
  3. L'Interrupt Descriptor Table (`g_idt`) non conteneva gestori validi per i 256 vettori di eccezione, scatenando a cascata un Double Fault (`#DF`, Vector 8) e un Triple-Fault che riavviava deterministicamente la CPU.
- **Regola**:
  1. Flag Freestanding Obbligatori: Tutti i moduli del kernel bare-metal devono categoricamente essere compilati con i flag di protezione architetturale `-mno-sse -mno-sse2 -mno-mmx` per impedire la generazione silente di istruzioni vettoriali nel codice di ring 0.
  2. Abilitazione Hardware Preventiva in Bootstrap: L'entry point assembly (`boot.S`) deve configurare esplicitamente i registri `CR0` (azzeramento bit 2 `EM`, abilitazione bit 1 `MP` e bit 5 `NE`) e `CR4` (abilitazione bit 9 `OSFXSR` e bit 10 `OSXMMEXCPT`), invocando `fninit` prima di passare l'esecuzione al codice C.
  3. Popolamento Completo Tabella IDT: Inizializzare preventivamente tutti i 256 cancelli della tabella IDT con una ISR di salvaguardia predefinita (`osify_default_isr` con `iret`, flag `0x8E` e selettore codice attivo) e mascherare tutti gli IRQ del PIC (`0xFF`) prima di invocare `lidt`, prevenendo qualsiasi triple-fault all'arrivo di interrupt o tick hardware.

## 2026-10-18 — Masterizzazione Ibrida xorriso: Percorsi Relativi El Torito, Pulizia [BOOT] e Integrita Syslinux
- **Area**: Bootloader ISO Universale Ibrida (UEFI x86_64, BIOS Legacy x86_64, Vintage 32-bit i686) e Packaging xorriso
- **Errore**: L'avvio dell'ISO Unica Universale e della versione 64-bit su BIOS Legacy in ambiente reale o QEMU si arrestava al prompt Syslinux o a 0% senza procedere all'avvio automatico, e su UEFI la masterizzazione conteneva strutture duplicate o spurie.
- **Causa radice**:
  1. Nei comandi `xorriso -as mkisofs`, i percorsi passati a `-c` (`/boot/syslinux/boot.cat`), `-b` (`/boot/syslinux/isolinux.bin`) ed `-e` (`/boot/grub/efi.img`) includevano uno slash iniziale `/`, che in modalità mkisofs può corrompere i percorsi relativi della tabella El Torito.
  2. L'estrazione preliminare della ISO con `7z x` generava cartelle spurie `[BOOT]` contenenti le immagini d'avvio grezze estratte (`1-Boot-NoEmul.img`, `2-Boot-NoEmul.img`), che venivano poi re-incluse da xorriso sporcando l'indice di boot.
  3. La presenza di cartelle ridondanti (`boot/isolinux`, `isolinux`) e copie multiple di `isolinux.bin` con stati di patch parziali disallineava il caricamento di `ldlinux.c32`.
- **Regola**:
  1. Percorsi Relativi Obbligatori in xorriso: Tutti i parametri El Torito (`-c boot/syslinux/boot.cat`, `-b boot/syslinux/isolinux.bin`, `-e boot/grub/efi.img`) devono categoricamente omettere lo slash iniziale.
  2. Sanificazione Pre-Masterizzazione: Rimuovere sempre prima di invocare xorriso qualsiasi cartella spuria generata da 7z (`[BOOT]`), qualsiasi cartella duplicata di boot (`boot/isolinux`, `isolinux`) e rigenerare unicamente `boot/syslinux/boot.cat`.
  3. Configurazione Boot Unificata: Centralizzare i file di configurazione in `boot/syslinux/syslinux.cfg` e `boot/syslinux/isolinux.cfg` con toolchain e moduli `.c32` (ldlinux, libcom32, libutil, vesamenu) coerenti e verificati.

## 2026-10-18 — UEM Dispatcher Poliglota, Formattatore Freestanding Kernel & Popolamento Userspace Live
- **Area**: Universal Execution Module (UEM), Freestanding Runtime C (`osify_snprintf`) e Packaging RootFS Live 64-bit / ARM64
- **Errore**:
  1. I collegamenti in `/usr/bin/` (`osify-hub`, `osify-wifi`, `osify-ctl`, ecc.) nella ISO 64-bit e ARM64 puntavano a `/opt/osify/...` inesistente nel rootfs Alpine diskless, rendendo inerte il click sulle icone della Dock e mancava `/usr/bin/osify-exec`.
  2. Nei runner UEM (`osify-pe-runner.sh`, `osify-wasm-runner.sh`, `osify-cross-runner.sh`, `osify-dos-runner.sh`, `osify-java-runner.sh`), l'invocazione di `exec runtime "$FILE" "$@"` senza `shift` preventivo passava il nome del binario due volte consecutive, corrompendo gli argomenti a riga di comando.
  3. Nel dispatcher UEM, l'assenza del tool `od` provocava la mancata rilevazione del magic number lasciando cadere l'esecuzione di `.exe` su un tentativo diretto di kernel exec con `Exec format error`, e l'invocazione rigida di `osify-pe-runner.sh` falliva in assenza del suffisso `.sh`.
  4. In `osify_kstring.c`, `%d` trattava i valori come unsigned stampando numeri positivi enormi per interi negativi senza il segno `-`, mentre `%p` (puntatori) e `%c` (caratteri) non erano implementati provocando lo scarto dei token senza consumare `va_arg` e sfasando gli argomenti variadici successivi.
  5. Nei messaggi di errore di `osify-dos-runner.sh` e `osify-java-runner.sh` comparivano residui testuali di package manager terzi (`pacman -S`).
- **Causa radice**: Assunzione scorretta sulla presenza implicita di cartelle `/opt/osify` e comandi esterni (`od`) nei rootfs diskless minimali; omissione di `shift` post-assegnazione del primo argomento negli script shell; parser freestanding incompleto per formati C standard.
- **Regola**:
  1. Popolamento Completo Userspace: La funzione `populate_osify_userspace` deve copiare direttamente tutti i binari di sistema, script UEM e utility in `usr/bin/` e `usr/local/bin/` (con bit `0o755`), copiare tutti i `.desktop` e le associazioni `mimeapps.list` in `etc/xdg` e `usr/share/applications`, e replicare la gerarchia in `/opt/osify` per retrocompatibilità totale.
  2. Argomenti Puliti nei Runner: Ogni runner shell che memorizza `$1` in una variabile (`BIN_FILE`, `EXE_FILE`, ecc.) deve eseguire immediatamente `shift` prima di passare `"$@"` al runtime sottostante.
  3. Sniffing Multi-Tool e Fallback Estensione: Il dispatcher universale deve tentare la lettura dei primi byte con `od`, `hexdump` o `python3`, disporre di fallback infallibile basato sull'estensione del file (`.exe`, `.apk`, `.wasm`, `.jar`, `.app`, ecc.), e risolvere i moduli runner tramite `run_uem_module` scansionando indifferentemente varianti con e senza suffisso `.sh` nei percorsi di sistema.
  4. Formattazione Freestanding Robusta: `osify_snprintf` deve gestire correttamente il segno negativo per `%d`/`%i` (con salvaguardia anti-overflow su `INT64_MIN`), i puntatori `%p` (con prefisso `0x` o `(nil)`), i caratteri `%c`, il padding numerico con zeri (`%0`), e i modificatori di lunghezza long (`%ld`, `%lu`, `%lx`).
  5. Autonomia Testuale Assoluta: Nessun comando o riferimento a distribuzioni Linux terze (`pacman`, `apt`, `dnf`) deve comparire negli output dei runner o nel codice di OSify.

## 2026-10-17 — Bootloader Ibrido Universale: El Torito EFI, Partizione GPT isohybrid-gpt-basdat e Auto-Detect ifcpu64
- **Area**: Bootloader ISO Universale Ibrida (UEFI x86_64, BIOS Legacy x86_64, Vintage 32-bit i686)
- **Errore**: L'immagine ISO Universale `OSify-A.0-Universal.iso` non veniva avviata su macchine o VM UEFI cadendo nella `UEFI Interactive Shell v2.2` (EDK II), mentre su hardware BIOS legacy con GPU moderne si arrestava su uno schermo nero.
- **Causa radice**:
  1. La compilazione con `genisoimage` impostava unicamente il settore di boot BIOS (`-b boot/isolinux/isolinux.bin`) omettendo l'entry alternativa El Torito per UEFI (`-eltorito-alt-boot -e /boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat`) e mancando di scrivere la partizione GPT `EFI System Partition`, per cui il firmware UEFI rilevava solo un disco dati grezzo senza filesystem (`BLK1:`) e senza script `startup.nsh`.
  2. L'etichetta ISO (`-V`) era impostata su `OSIFY_UNIVERSAL`, rompendo la ricerca hardcoded `search --label OSify-2050-Gaming-x86_64` integrata nel binario GRUB EFI.
  3. Su BIOS legacy, Syslinux avviava deterministicamente il kernel 32-bit `bzImage` privo di parametro `video=-32` invece di auto-rilevare le CPU a 64-bit tramite `ifcpu64.c32` congruente.
- **Regola**:
  1. Masterizzazione xorriso Obbligatoria: La ISO universale deve sempre essere masterizzata con `xorriso` includendo sia il catalogo BIOS (`-b /boot/syslinux/isolinux.bin`) sia il catalogo alternativo El Torito EFI (`-eltorito-alt-boot -e /boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat`).
  2. Allineamento Etichetta EFI: L'etichetta volume `-V` passata a `xorriso` deve coincidere categoricamente con quella presente nel binario `bootx64.efi` (`OSify-2050-Gaming-x86_64`).
  3. Script Fallback EDK II: Inserire sempre `startup.nsh` e `STARTUP.NSH` nella radice del filesystem ISO per eseguire automaticamente `\EFI\BOOT\BOOTX64.EFI` qualora il firmware UEFI non rilevi le voci NVRAM.
  4. Auto-Rilevamento Silicio: Utilizzare `DEFAULT autodetect` con `COM32 ifcpu64.c32` e toolchain syslinux coerente per indirizzare a caldo su `osify64` (`vmlinuz-lts` a 64-bit con KMS) o su `osify32` (`bzImage` con `video=-32`).
  5. Bootsplash Solo-Logo Puro: Utilizzare `MENU HIDDEN`, `MENU ROWS 0` e colori `#00000000` (trasparenza totale) per non sovrapporre testi, box o timer al logo squircle luminescente.

## 2026-10-17 — Bootloader Universale Ibrido: Direttiva DEFAULT Obbligatoria per Timeout Automatico senza Input
- **Area**: Bootloader Syslinux / Isolinux per ISO Universale ibrida
- **Errore**: L'avvio dell'ISO Unica Universale (`OSify-A.0-Universal.iso`) in VM o macchine prive di interazione da tastiera si fermava indefinitamente sul menu vesamenu mostrando uno schermo nero anziché far partire automaticamente il desktop dopo il timeout.
- **Causa radice**: In Syslinux / Isolinux, la direttiva `ONTIMEOUT <label>` da sola non è sufficiente se manca la direttiva primaria `DEFAULT <label>`. In assenza di `DEFAULT`, vesamenu non seleziona alcuna voce attiva predefinita e blocca il caricamento del kernel e dell'initramfs.
- **Regola**:
  1. Configurazione Isolinux: Inserire sempre `DEFAULT osify` come prima riga prima di `UI vesamenu.c32` in tutti i file di configurazione (`boot/isolinux/isolinux.cfg`, `boot/syslinux/syslinux.cfg`, `isolinux/isolinux.cfg`).
  2. Percorsi Risorse Boot: Fare sempre riferimento alle immagini di sfondo con nomi file relativi alla cartella di boot (`MENU BACKGROUND splash.jpg`) per evitare fallimenti di risoluzione del percorso assoluto nel firmware del bootloader.
  3. Timeout Reattivo: Impostare un timeout non superiore a 20 decimi di secondo (`TIMEOUT 20`) per garantire un avvio scattante e immediato sul silicio.

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

## 2026-10-18 — Completezza Assoluta delle Immagini ISO Bare-Metal e dell'Userspace Nativo
- **Area**: Pipeline di build delle immagini ISO, packaging userspace e collaudo bare-metal
- **Errore**: Generazione di un'immagine ISO minimale da 2MB contenente esclusivamente il kernel ELF e priva dell'intero userspace nativo (24 applicazioni .ify, servizi, driver, icone e gerarchia file system completa).
- **Causa radice**: `build/build-baremetal-iso.py` allocava un array di byte prefissato da 2MB scrivendo a mano il descrittore PVD per testare il solo avvio del kernel, senza pacchettizzare i comparti applicativi e di sistema con il motore di masterizzazione completo.
- **Regola**:
  1. Nessuna immagine di OSify puo mai essere uno stub parziale: ogni ISO deve contenere l'intera distribuzione a pieno titolo (/Sistema, /System, /Applicazioni con tutte le 24 app .ify, /UEM, /Desktop, /Strumenti, /Sicurezza, /Rete, /Documenti, /Utenti).
  2. La pipeline di build bare-metal deve sempre utilizzare `xorriso` con flag `-r -J -joliet-long`, MBR ibrido, El Torito e modulo multiboot `mboot.c32`, garantendo boot reale e accesso completo all'albero di archiviazione.
  3. Vietato chiedere al Compagno "cosa manca per": analizzare, progettare e consegnare l'opera completa e rifinita in ogni dettaglio.

## 2026-10-18 — Architettura Driverless Universale, Scheduler Eterogeneo e Introspezione Silicio
- **Area**: Kernel core, scheduler computazionale, introspezione hardware e display engine
- **Errore**: Rischio residuo di fallback grafico su controller video non convenzionali e assenza di differenziazione hardware automatica tra ALU scalare, pipeline SIMD e GPU blitter.
- **Causa radice**: Mancanza di un motore di scansione bus PCI generico (porte 0xCF8/0xCFC) e assenza di un sistema di connettori per distribuire i processi in base al tipo di carico di lavoro.
- **Regola**:
  1. Il sistema deve essere Driverless per quanto possibile: scansione PCI per agganciare direttamente il linear framebuffer di qualsiasi scheda grafica (Intel Iris, AMD Radeon, NVIDIA GeForce, Bochs, VMware) senza richiedere driver proprietari monolitici.
  2. Integrare sempre lo Scheduler Eterogeneo (`osify_hetero_dispatch`) con connettori di processo nativi per smistare automaticamente: compiti logici su ALU scalare, cifratura e matematica su SIMD (SSE2/AVX/NEON), interfaccia su GPU Blitter burst, e periferiche su I/O asincrono.
  3. Nessuna dipendenza da runtime esterni: divisioni a 64-bit in kernel 32-bit devono essere risolte con operandi dimensionalmente corretti o con helper freestanding espliciti (`__udivdi3`, `__umoddi3`).

## 2026-10-18 — Desktop Environment Dark Glass Sovrano, Scheda Acquisizione Integrata e Installazione Reale
- **Area**: Window Manager nativo, driverless capture subsystem e installatore su disco silicio
- **Errore**: Presentare un'interfaccia iniziale grezza con sola finestra terminale invece di consegnare un Desktop Environment 2050 completo (wallpaper cyber mesh, icone desktop, HUD laterale risorse, dock glassmorphism e scheda di acquisizione virtuale).
- **Causa radice**: Non aver dato per scontata la ricchezza visiva e le capacita di acquisizione video interna richieste per un sistema operativo di nuova generazione.
- **Regola**:
  1. La GUI deve essere sempre completa al 100%: wallpaper a cyber-mesh sfumato con logo filigrana, icone squircle a doppio strato sulla Scrivania, barra di stato dinamica, pannello HUD laterale per telemetria CPU/RAM/GFLOPS e dock a 6 canali con indicatori attivi.
  2. Implementare la Scheda di Acquisizione Virtuale nativa (`osify_capture_card`) tramite direct framebuffer tap e ring buffer DMA a 60 FPS, consentendo al sistema di fungere da capture card senza richiedere hardware HDMI esterno.
  3. Verificare sempre il ciclo di vita reale dell'utente: avvio da supporto, esecuzione comandi CLI e installazione permanente su disco fisso virtuale GPT convalidata visivamente con screendump reali.

## 2026-10-18 — UEM Bridge Bare-Metal, Formato Esportazione PPM Lossless e Geometria Window Manager
- **Area**: Window Manager nativo (`osify_desktop_wm.c`), Scheda di Acquisizione (`osify_capture_card.c`), File System Nativo (`osify_storage.c`) e Typography/Graphics
- **Errore**:
  1. Le righe di testo lunghe nel terminale e nell'Esplora File sforavano la larghezza della finestra andando a sovrascrivere l'HUD di destra.
  2. L'invocazione di `osify_fb_draw_squircle` per i pulsanti di cattura generava quadrati 140x140 invece di pulsanti rettangolari arrotondati.
  3. L'esecuzione dei binari da CLI falliva in assenza di un confronto percorsi case-insensitive o tollerante ai prefissi `/Applicazioni/` e `/UEM/`.
- **Causa radice**:
  1. `osify_fb_draw_string` nel terminale disegnava oltre il limite `win->w - 32` senza clipping orizzontale preventivo.
  2. `osify_fb_draw_squircle` accetta per specifica un parametro quadratico `size`, non larghezza e altezza distinte.
  3. `osify_fs_read_file` impiegava `osify_strcmp` esatto, rendendo vulnerabile il lookup dei file digitati con maiuscole/minuscole o senza prefisso assoluto.
- **Regola**:
## 2026-10-18 — Card Installatore Rounded Rect, Driver Mouse PS/2 e Calibrazione Spaziale Desktop 1024x768
- **Area**: Window Manager nativo (`osify_desktop_wm.c`), Driver Input PS/2 (`osify_ps2_input.c`), Card Installatore (`osify_installer.c`) e Typography
- **Errore**:
  1. `osify_installer_render` impiegava `osify_fb_draw_squircle` con `w = 720`, generando un quadrato 720x720 che invadeva il desktop e copriva la parte inferiore dello schermo fino a y=820.
  2. Le etichette lunghe delle sottocartelle in Esplora File (es. `[DIR] /Utenti/Compagno`) e delle finestre di background sforavano la larghezza del contenitore sporgendo a destra oltre la cornice.
  3. Il posizionamento non sincronizzato delle finestre a `x = 80` provocava una parziale sovrapposizione visiva sulle etichette delle icone desktop a sinistra (`Questo PC`).
- **Causa radice**:
  1. Omissione del parametro altezza `h` nell'invocazione di primitive quadratiche `squircle` su componenti a estensione rettangolare.
  2. Mancanza di un helper di disegno con clipping preventivo dei caratteri (`draw_window_string_clipped`) applicato alle stringhe interne dei componenti secondari.
  3. Mancata definizione di zone orizzontali stagne per il Desktop Environment a 1024x768.
- **Regola**:
  1. Rettangoli Arrotondati Obbligatori: Tutte le card, pannelli e finestre dell'installatore e del Window Manager devono impiegare categoricamente `osify_fb_draw_rounded_rect(fb, x, y, w, h, radius, hex_color)`.
  2. Tripartizione Rigorosa dello Spazio Orizzontale a 1024x768:
     - Zona Sinistra Icone Desktop: `x = 0..89` con etichette centrate sotto l'icona (`ix + 24 - len*9/2`) e limite massimo a 89px.
     - Zona Centrale Finestre: `x = 100..724` con larghezza massima di 624px, impedendo deterministicamente qualsiasi sovrapposizione sulle icone o sull'HUD.
     - Zona Destra Monitor Silicio: `x = 734..1008`.
  3. Clipping Sistematico delle Stringhe Interne: Applicare sempre `draw_window_string_clipped` con limite massimo di caratteri calcolato dinamicamente sul contenitore genitore.
  4. Protocollo Mouse PS/2 Hardware: Decodificare sempre i pacchetti a 3 byte del controller 8042 Aux (bit 5 di status port 0x64) per muovere il cursore e generare eventi di clic sia su silicio fisico che su QEMU, salvaguardando l'esecuzione con il flag `g_ps2_hw_active`.


