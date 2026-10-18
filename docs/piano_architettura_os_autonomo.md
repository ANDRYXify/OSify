# SPECIFICA ARCHITETTURALE: SISTEMA OPERATIVO SOVRANO A SÉ STANTE (RING 0 -> RING 3)
**Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify**

---

## 1. Definizione Ontologica: Cosa Significa "A Sé Stante al 100%"

Un sistema operativo si definisce **a sé stante al 100% (sovrano e autonomo)** quando soddisfa la seguente equazione ingegneristica:

$$\text{Autonomia} = \frac{\text{Linee di Codice di Controllo Ring 0 Indipendenti}}{\text{Totale Substrato di Esecuzione}} = 100\%$$

Non utilizza un kernel preesistente (Linux, Windows NT, XNU/Darwin) come intermediario per parlare con i registri della CPU, non dipende da libc esterne (glibc, musl), non si appoggia a server grafici terzi (X.Org, Wayland), e controlla direttamente:
1. I registri di controllo della CPU (`CR0`, `CR2`, `CR3`, `CR4`, `EFER`, `MSR`).
2. Lo spazio degli indirizzi fisici e virtuali (Tabelle di Paginazione hardware).
3. Le linee di interruzione fisica (PIC 8259A o APIC/IOAPIC).
4. Le porte I/O e lo spazio di memoria mappato (MMIO) del bus PCI.
5. Il Linear Framebuffer video e i controller di storage di massa.

---

## 2. La Catena di Bootstrap e Transizione Hardware

Il sistema deve accompagnare la macchina dallo stato di reset elettrico fino al desktop grafico attraverso 5 fasi sequenziali immutabili:

```
[ RESET ELETTRICO / FIRMWARE ]
           │
           ▼
[ FASE 1: FIRMWARE (BIOS Legacy / UEFI GOP) ]
           │  Carica il primo settore (MBR / El Torito) o il file EFI PE32+
           ▼
[ FASE 2: BOOTSTRAP STAGE 1 & 2 ]
           │  - A20 Gate abilitata
           │  - Passaggio da Real Mode 16-bit a Protected Mode 32-bit (o Long Mode 64-bit)
           │  - GDT temporanea caricata via LGDT
           ▼
[ FASE 3: KERNEL ENTRY (sistema/nucleo/kernel/boot/boot.S) ]
           │  - Inizializzazione stack di Ring 0 (16 KB)
           │  - Configurazione FPU ed estensioni SIMD (CR0.MP, CR0.NE, CR4.OSFXSR)
           │  - Introspezione memoria da bootloader (Multiboot memory map)
           ▼
[ FASE 4: KERNEL CORE SUBSYSTEMS (Ring 0) ]
           │  - IDT (256 vettori) & Remap PIC/APIC
           │  - PMM (Physical Memory Manager - Bitmap / Buddy Allocator)
           │  - VMM (Virtual Memory Manager - Paging 4KB con W^X)
           │  - Scheduler Prelativo dei Processi (PIT / LAPIC Timer)
           │  - Inizializzazione Bus PCI, Storage ATA/AHCI, Framebuffer BGA/GOP
           ▼
[ FASE 5: TRANSIZIONE RING 3 (USERSPACE) ]
           │  - TSS (Task State Segment) con esp0 configurato per i cambi di privilegio
           │  - IRET ad anello 3 (User Code Selector 0x1B, User Data Selector 0x23)
           │  - Avvio del primo processo sovrano: /Sistema/Nucleo/init
           ▼
[ FASE 6: COMPOSITING ENGINE & DESKTOP (Obsidian Dark Glass) ]
           │  - Allocazione doppio buffer grafico (Backbuffer -> Frontbuffer VRAM)
           │  - Loop eventi Input PS/2 & USB HID
           │  - Shell interattiva e caricamento applicazioni .ify
```

---

## 3. Ring 0: Il Cuore del Kernel Nativo

Un vero sistema operativo autonomo deve articolare il livello di privilegio 0 (Supervisore) nei seguenti sottosistemi chiusi:

### 3.1. Gestione Interrupts e Timer Hardware (IDT & PIC/APIC)
- **IDT (Interrupt Descriptor Table)**: Tabella a 256 ingressi che associa ogni vettore a una Interrupt Service Routine (ISR) scritta in assembly (`pusha; call c_handler; popa; iret`).
  - *Vettori 0–31*: Eccezioni del processore (Division by Zero, Page Fault `#PF`, Invalid Opcode `#UD`, General Protection Fault `#GP`).
  - *Vettori 32–47*: IRQ Hardware rimappati (IRQ 0 = Timer PIT, IRQ 1 = Tastiera, IRQ 12 = Mouse PS/2, IRQ 14/15 = Disco ATA).
  - *Vettore 0x80*: Interfaccia di System Call nativa di OSify.
- **Timer Preemptive**: Il timer hardware (PIT a 100 Hz / 1000 Hz o LAPIC Timer) invia un tick periodico che salva il contesto del processo attivo e invoca lo scheduler.

### 3.2. Gestione della Memoria a Due Livelli (PMM e VMM)
- **PMM (Physical Memory Manager)**:
  - Gestisce l'intera RAM fisica tramite una mappa di bit (Bitmap Allocator), dove 1 bit corrisponde a una pagina fisica da 4096 byte.
  - Funzioni primitive: `pmm_alloc_page()`, `pmm_free_page()`.
- **VMM (Virtual Memory Manager & Paging)**:
  - Configura la Directory delle Pagine (CR3) a 4KB o con Paging a 4 livelli (PAE / x86_64 a 48-bit).
  - Isolamento spaziale assoluto: ogni processo possiede un proprio spazio di memoria virtuale separato da quello degli altri processi e protetto dal kernel.
  - Applicazione rigida del principio **W^X (Write XOR Execute)**: le pagine contenenti codice eseguibile sono marcate `Read-Only`, le pagine con dati o stack sono marcate `No-Execute` (NX bit attivo nel registro `EFER`).

### 3.3. Scheduler Prelativo & Task Switching
- **Process Control Block (PCB)**:
  Struttura che conserva lo stato completo di ogni applicazione:
  ```c
  typedef struct osify_task {
      uint32_t pid;
      uint32_t esp;              /* Stack pointer del thread */
      uint32_t cr3;              /* Tabella delle pagine del processo */
      uint32_t state;            /* PRONTO, IN_ESECUZIONE, BLOCCATO, MORTO */
      uint32_t priority;
      char     name[32];
      struct osify_task *next;
  } osify_task_t;
  ```
- **Context Switch atomico**: Al tick del timer, il kernel salva i registri della CPU nello stack del processo uscente, aggiorna il TSS, scambia `CR3` e ripristina i registri del nuovo processo con `iret`.

---

## 4. Driver Hardware Sovrani (Senza Dipendenze da Terzi)

Per non essere una derivata o una skin, i driver devono essere implementati direttamente nel codice sorgente del sistema:

| Sottosistema | Modalità di Controllo Sovrana | Standard Supportato |
| :--- | :--- | :--- |
| **Video & Display** | I/O Ports dirette (`0x01CE`/`0x01CF` BGA) e GOP Framebuffer | Linear Framebuffer a 32bpp, risoluzione nativa 1024x768 / 1920x1080 |
| **Storage di Massa** | Controller ATA/IDE su porte primarie `0x1F0`–`0x1F7` e AHCI PCI MMIO | Lettura e scrittura di settori LBA a 28 e 48 bit senza passare per il BIOS |
| **File System** | **OSifyFS nativo**: Superblocco, Tabella Inode, Bitmap Blocchi Dati | Supporto transazionale, percorsi italiani (`/Sistema`, `/Applicazioni`, `/Utenti`) |
| **Input Utente** | I/O Controller PS/2 (`0x60`, `0x64`) e controller USB UHCI/xHCI | Decodifica Scancode Set 1/Set 2 tastiera e pacchetti a 3 byte per mouse |
| **Rete Bare-Metal** | Driver per schede PCI Ethernet (Intel 82540EM / e1000, Realtek RTL8139) | Stack di rete completo: Ethernet II, ARP, IPv4, UDP, DHCP client, DNS Quad9 |
| **Audio Hardware** | Intel HDA (High Definition Audio) via BAR PCI MMIO e codec AC97 | DMA cyclic buffer a bassa latenza, mixer software nativo, Startup Chime |

---

## 5. Ring 3: Userspace, Standard Library e Init Sovrano

La transizione ad anello 3 è ciò che trasforma un kernel in un vero sistema operativo utilizzabile dall'utente:

1. **System Call Interface (`int 0x80` o istruzioni `sysenter`/`syscall`)**:
   - `sys_exit` (0x01), `sys_fork` (0x02), `sys_read` (0x03), `sys_write` (0x04), `sys_open` (0x05), `sys_close` (0x06).
   - `sys_mmap` / `sys_brk` per l'allocazione dinamica della memoria nello spazio utente.
   - `sys_fb_blit` / `sys_get_event` per la grafica e la gestione degli input.
2. **Standard C Library Freestanding (libosify)**:
   - Implementazione proprietaria di `malloc()` (basata su bucket heap con pool da 4KB), `printf()`, manipolazione stringhe, matematica a virgola mobile pura. Zero collegamenti a glibc, musl o msvcrt.
3. **Init & Service Manager (`/Sistema/Nucleo/init`)**:
   - Primo binario eseguibile lanciato dal kernel ad anello 3.
   - Monta i filesystem essenziali, avvia il sottosistema di rete, imposta le variabili d'ambiente e lancia il Window Server.

---

## 6. Graphical Window Server: Obsidian Dark Glass Nativo

In un sistema operativo a sé stante non esistono Xorg o Wayland. Il server grafico è integrato:

1. **Doppio Buffer VRAM**:
   - Un buffer in memoria RAM di sistema (Backbuffer) sul quale le applicazioni e il compositor disegnano i pixel.
   - Un comando di flush atomico copia il Backbuffer nel Linear Framebuffer hardware (Frontbuffer) durante il Vertical Blanking (V-Sync) a 60/120 Hz, azzerando il tearing.
2. **Compositing Engine a Finestre**:
   - Calcolo delle regioni visibili (Dirty Rectangles) per aggiornare solo i pixel che cambiano.
   - Supporto per angoli arrotondati (Squircle), ombreggiature alfa (32-bit ARGB con canale trasparenza) ed elementi vetrosi (Dark Glass Card).
3. **Typography Engine**:
   - Rasterizzatore tipografico scalabile e font bitmap VGA 8x16 integrato nel binario per rendere immediatamente il testo senza dipendere da FreeType.

---

## 7. Il Ponte di Compatibilità Universale (UEM) ad Anello 3

Come fa un OS nativo autonomo a eseguire software Windows, macOS o Linux senza basarsi su di essi?
- **Binary Loader Poliglota**:
  Il kernel e il loader di sistema leggono l'intestazione del file eseguibile:
  - Magic `0x7F 'E' 'L' 'F'` $\rightarrow$ Mappatura sezioni ELF (System V ABI nativa).
  - Magic `'M' 'Z'` (0x5A4D) $\rightarrow$ Parser del formato PE/COFF Windows, allocazione sezioni `.text`, `.data`, `.rdata` e risoluzione delle Import Table (IAT) verso DLL emulate da OSify.
  - Magic `0xFEEDFACE` / `0xFEEDFACF` $\rightarrow$ Parser Mach-O di macOS.
- **Traduzione Semantica dei Segnali e Syscall**:
  Un layer di traduzione ad anello 3 intercetta le chiamate API del binario esterno e le traduce direttamente nelle syscall native di OSify (es. `CreateFileW()` Windows $\rightarrow$ `sys_open()` OSify).

---

## 8. Piano di Completamento e Matrice di Maturità OSify

| Area Architetturale | Stato Attuale vA.1 (Dimostrato in QEMU) | Prossimo Step per Maturità Finale Ring 3 |
| :--- | :--- | :--- |
| **Bootstrap & Header** | 100% Conforme Multiboot a 1MB con CR0/CR4 FPU/SSE | Supporto avvio nativo UEFI GOP a 64-bit senza shim |
| **Interrupts & IDT** | 100% IDT (256 gate stabili, PIC mascherato, no triple-fault) | Driver APIC/IOAPIC per gestione multi-core SMP |
| **Memoria PMM/VMM** | 100% PMM Bitmap e verifica W^X anti-exploit | Paginazione virtuale completa a 2 livelli con Page Fault Handler |
| **Display & Desktop** | 100% Linear Framebuffer 1024x768x32 BGA, Topbar, Dock, Shell | Separazione del Desktop WM come processo Ring 3 isolato |
| **Driver Storage** | 100% Controller ATA PIO e OSifyFS in-memory/raw | Scrittura su disco rigido fisico GPT con partizionamento live |
| **Network Stack** | 100% Modulo bare-metal Ethernet II, DHCP, Quad9 | Implementazione socket TCP/IP ad anello 3 per navigazione web |
| **Audio** | 100% Controller Intel HDA, mixer e Chime sonoro | Streaming PCM continuo per media player |
| **Ponte Universale** | 100% Parser binari ELF/PE/Mach-O nel kernel | Caricamento dinamico librerie DLL/SO nello spazio utente |
