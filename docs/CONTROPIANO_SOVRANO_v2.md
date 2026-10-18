# CONTROPIANO ARCHITETTURALE OSIFY v2.0 — NUCLEO SOVRANO, BASE PROPRIETARIA E COMPATIBILITÀ UNIVERSALE SICURA

**Specifica Ingegneristica Ring -1 -> Ring 0 -> Ring 3 di Andrea Taliento (ANDRYXify)**

---

## 0. Evoluzione Ingegneristica: Dal Piano Originale al Contropiano Sovrano v2.0

Un sistema operativo realmente a sé stante non può né limitarsi a una singola CPU, né adottare come proprio scheletro interno il modello di un altro OS (come POSIX/Linux), altrimenti erediterà tutti i colli di bottiglia di quel modello quando tenterà di eseguire software nato per architetture diverse (Windows NT, macOS XNU/Mach). Inoltre, non può rinunciare a eseguire software complesso (macOS, Anti-Cheat Kernel-Level): deve invece costruire le **architetture di contenimento hardware** per eseguirli senza mai compromettere la sicurezza del sistema ospite.

| Aspetto | Piano Originale v1 | Contropiano Precedente (Limitante) | **Contropiano Sovrano v2.0 (Definitivo)** | **Razionale da Systems Engineer** |
| :--- | :--- | :--- | :--- | :--- |
| **Dipendenza CPU** | Legato a x86 (`CR3`, `IDT`, `PIC`, `int 0x80`) | Nucleo neutro + `arch.h` | **Nucleo Neutro + `arch.h` (Ring 0) + `arch_hv.h` (Ring -1/EL2)** | Astrae sia il supervisore sia la virtualizzazione hardware per l'isolamento sicuro. |
| **Modello Base del Kernel** | Ibrido POSIX-like (`sys_fork`, `int 0x80`) | Quasi-POSIX (`futex`, `mmap` standard) | **Modello Proprietario OSify Superset** (Capability Handle, `WaitMux`, `RingBus` IPC) | Se la base è un *superset* di NT, Mach e POSIX, qualsiasi personalità gira a velocità nativa senza hack. |
| **Granularità MMU** | Pagine fisse 4KB x86 | `arch_page_size()` statico | **VMM Multi-Granularità (4KB/16KB/2MB) + Sub-Page Protection** | Permette a binari x86/Windows/macOS (4KB) di girare su ARM64 (16KB) senza page fault spuri. |
| **Formato App `.ify` e Sicurezza** | Binario generico | WebAssembly standard + BearSSL esterno | **OSifyIR (Bytecode AOT Proprietario) + OSifyCrypt Nativo** | Zero dipendenze da standard web o librerie terze; supporto diretto a SIMD, thread e GPU nativa. |
| **Compatibilità Windows** | Parser PE nel kernel | Solo tramite Linux -> Wine | **Personalità Nativa NT (`OSIFY_PERS_NT`) + Sottosistema Win32 Userspace** | Evita il doppio passaggio `Win32 -> Linux -> OSify`; traduce le syscall NT direttamente nel kernel OSify. |
| **Compatibilità macOS** | Parser Mach-O nel kernel | Escluso ("Framework chiusi") | **Sottosistema Dual-ABI Darwin (`OSIFY_PERS_DARWIN`) + Orchid Clean-Room Frameworks** | Mach-O è documentato; le trap Mach/BSD si intercettano nel kernel e Cocoa/Metal si mappano in Ring 3 su Obsidian. |
| **Anti-Cheat Kernel** | Non trattato | Escluso ("Bloccato") | **OSify Aegis (HVCS: Hardware-Virtualized Containment Sandbox a Ring -1/EL2)** | I driver `.sys` girano a vero Ring 0 *dentro una Micro-Cella isolata via SLAT/EPT*, vedono solo il gioco e mai il kernel OSify. |

---

## 1. Criteri Verificabili di Sovranità ("A Sé Stante al 100%")

OSify è certificato come sistema operativo sovrano quando soddisfa simultaneamente questi 6 invarianti ingegneristici:

1. **Purezza di Ring 0 / Ring -1**: Nessuna riga di codice appartenente a Linux, XNU, FreeBSD o Windows NT viene eseguita in modalità supervisore o hypervisor.
2. **Neutralità Multi-Architettura**: Lo stesso commit del nucleo compila e avvia il desktop su almeno due architetture radicalmente diverse (`x86_64` e `AArch64`), mantenendo `i686` e `riscv64` come target di prima classe.
3. **Semantica Proprietaria Indipendente**: Il sistema nativo (Init, Window Server, Servizi, App `.ify`) utilizza esclusivamente l'ABI proprietaria OSify, il protocollo IPC `RingBus` e il filesystem transazionale `OSifyFS v2`.
4. **Isolamento Spaziale e Temporale Totale**: Il crash o il tentativo di exploit di un'applicazione nativa, di un'app macOS/Windows o di un driver Anti-Cheat in Cella Aegis non altera lo stato del kernel né delle altre applicazioni in esecuzione.
5. **Persistenza Crittografata e Verificata**: `/Sistema` è montato da un'immagine immutabile firmata con `OSifyCrypt` (Ed25519 + Albero di Merkle BLAKE3); i dati utente persistono su `OSifyFS v2`.
6. **Self-Hosting**: OSify compila l'intero albero sorgente del proprio kernel, dei propri servizi e dei propri pacchetti `.ify` girando su sé stesso.

---

## 2. Architettura a Strati e Isolamento Orizzontale/Verticale

```
┌──────────────────┬───────────────────┬───────────────────┬──────────────────────┐
│   APP .ify       │  ELF Linux / BSD  │  Windows PE/COFF  │  macOS Mach-O (.app) │
│ (OSifyIR -> AOT) │  (libc / POSIX)   │  (Win32 / DX/VK)  │ (Orchid Cocoa/Metal) │
├──────────────────┼───────────────────┼───────────────────┼──────────────────────┤
│   libosify       │  Layer UEM-Linux  │   Layer UEM-NT    │  Layer UEM-Darwin    │
│ (Nativa Pura)    │  (Ring 3 Shim)    │ (ntdll/kernelbase)│ (libSystem/dyld/MIG) │
├══════════════════┴═══════════════════┴═══════════════════┴══════════════════════┤
│                       CONFINE DI PRIVILEGIO (SYSCALL / TRAP)                    │
├──────────────────────────────────────────────────────────┬──────────────────────┤
│  DISPATCHER PERSONALITÀ KERNEL (Nativa | Linux | NT | XNU)│   CELLA AEGIS (HVCS) │
├──────────────────────────────────────────────────────────┤   [Ring 0 Ospite]    │
│  NUCLEO SOVRANO PROPRIETARIO OSIFY (Ring 0 / EL1 / S)    │   Driver Anti-Cheat  │
│  • WaitMux Sync Engine (Superset NT/Mach/POSIX)          │   (.sys / .kext)     │
│  • VMM Multi-Granularità (4K/16K Sub-Page) + PMM Slab    │   Isolato via SLAT   │
│  • OSify RingBus IPC (Zero-Copy Shared Memory Rings)     │   (Vede solo il      │
│  • VFS + OSifyFS v2 (Extent + COW + Merkle Checksum)     │    processo Gioco)   │
│  • OSifyNet (TCP/QUIC) + OSifyCrypt (Nativo)             │                      │
├──────────────────────────────────────────────────────────┴──────────────────────┤
│         CONTRATTO HARDWARE: arch.h (Supervisore) + arch_hv.h (Hypervisor)       │
├──────────────────┬───────────────────┬───────────────────┬──────────────────────┤
│   Porta x86_64   │   Porta AArch64   │   Porta RISC-V 64 │      Porta i686      │
│  (Ring 0 + VT-x) │  (EL1 + EL2 Stg2) │ (S-Mode + HS-Mode)│  (Ring 0 + PAE/NX)   │
└──────────────────┴───────────────────┴───────────────────┴──────────────────────┘
                                HARDWARE FISICO / BUS
```

---

## 3. Struttura del Repository Sovrano

```
sistema/
  bootloader/
    osify-boot/             # Bootloader UEFI proprietario (PE32+ per x86_64/aa64/rv64) + BIOS Legacy
  nucleo/
    arch/
      arch.h                # Contratto CPU, MMU, Interrupt, Context, TLS/Per-CPU registers
      arch_hv.h             # Contratto Hardware Virtualization (SLAT, vCPU, VMExit) per Aegis
      x86_64/               # GDT/TSS, IDT, APIC/x2APIC, Paging 4/5-lvl, SYSCALL, VT-x/AMD-V
      aarch64/              # VBAR_EL1/EL2, GICv3, Generic Timer, TTBR0/1, Stage-2 MMU, SVC/HVC
      riscv64/              # stvec/vstvec, PLIC/AIA, Sv39/Sv48 + G-stage, ECALL
      i686/                 # Multiboot, PAE (64-bit PTE con NX), PIC/APIC, SYSENTER/INT 0x80
    kernel/
      main.c                # Punto d'ingresso neutro osify_main(osify_boot_info_t *bi)
      handle.c              # Tabella Capability Handles con diritti granulari
      synch.c               # WaitMux: motore di sincronizzazione universale
      crypto.c              # OSifyCrypt: ChaCha20, SHA3/BLAKE3, Ed25519 (verifica firme kernel/app)
    mm/                     # PMM Buddy+Bitmap, VMM con Sub-Page table, Slab Allocator, COW
    sched/                  # Scheduler Preemptive EEVDF/Multilevel, SMP Load Balancer, Threading
    ipc/                    # OSify RingBus (code lock-free zero-copy), Porte Capability, Shm
    fs/                     # VFS, OSifyFS v2 (COW/Transazionale), FAT32 (EFI), ISO9660, DevFS
    net/                    # Ethernet, ARP, IPv4/IPv6, TCP, UDP, DHCP, DNS, Stack QUIC/TLS base
    bus/                    # PCIe ECAM, ACPI (interprete AML leggero nativo), DeviceTree
    driver/
      virtio/               # blk, net, gpu, input, snd, rng (universali su ogni architettura)
      storage/              # NVMe (code di sottomissione/completamento), AHCI
      usb/                  # xHCI, HID, Mass Storage
      gpu/                  # Framebuffer GOP/BGA, DRM/KMS nativo (Intel Xe/Gen, AMD, VirtIO-GPU 3D)
      audio/                # Intel HDA, VirtIO-SND
      x86_legacy/           # ATA PIO, PS/2, PIT, RTL8139 (esclusivi per target Vintage i686)
    personalita/
      nativa/               # Dispatcher ABI OSify pura
      linux/                # Traduttore syscall Linux + emulazione futex/epoll su WaitMux
      nt/                   # Traduttore syscall Windows NT (NtCreateFile, NtWaitForMultipleObjects...)
      darwin/               # Dispatcher Dual-ABI (Mach Traps + BSD Syscalls + MIG IPC router)
    aegis/                  # Sottosistema HVCS per contenimento Anti-Cheat e driver esterni in Ring -1
  libosify/                 # Libreria di sistema nativa freestanding (zero dipendenze POSIX)
  uem/                      # Runtime Ring 3 per il Ponte di Compatibilità Universale
    nt_subsys/              # Loader PE/COFF, ntdll.dll / kernel32.dll / user32.dll clean-room
    darwin_orchid/          # Loader dyld Mach-O, libSystem, CoreFoundation, Cocoa & Metal->Obsidian
    cpu_bridge/             # Traduttore binario dinamico JIT cross-arch (x86_64 <-> AArch64/RISC-V)
  servizi/                  # init, obsidian-wm (Window Server), netd, audiod, pkgd, aegisd
  applicazioni/             # Suite nativa .ify
tests/
  host/                     # Test algoritmici su codice neutro (strutture dati, OSifyFS, parser)
  qemu/                     # Test di integrazione full-system automatizzati per ogni architettura
```

---

## 4. Fondamenta Proprietarie del Kernel (Perché OSify non si "Tarpa le Ali")

Se costruissimo il kernel di OSify ricalcando Linux, avremmo gli stessi problemi di Linux nell'eseguire software Windows e macOS (lentezza nella sincronizzazione NT, impossibilità di gestire le porte Mach nativamente, conflitti sui registri di Thread Local Storage `FS`/`GS`, problemi con pagine da 4KB su ARM64). OSify risolve il problema alla radice nel proprio **Nucleo Neutro**:

### 4.1. Il Motore di Sincronizzazione Universale (`osify_wait_mux`)

- **Il problema negli altri OS**: Linux ha `futex`/`epoll` (orientati ai file descriptor); Windows NT ha `WaitForMultipleObjects` (che attende contemporaneamente su thread, mutex, eventi, semafori e timer con `WaitAll` o `WaitAny`); macOS/XNU usa i **Port Set Mach** e `kqueue`.
- **La soluzione proprietaria OSify**: Ogni oggetto del kernel di OSify (`osify_task_t`, `osify_port_t`, `osify_timer_t`, `osify_event_t`, `osify_shm_t`) inizia con un header comune `osify_synch_hdr_t`. La primitiva nativa `sys_wait_mux(osify_handle_t *handles, size_t count, uint32_t mode, uint64_t timeout_ns)` opera direttamente nello scheduler a Ring 0:
  - Per le app native `.ify`: offre reattività sub-microsecondo.
  - Per la personalità Windows NT: mappa `NtWaitForMultipleObjects` **1:1 senza emulazione in userspace** e senza server intermedi (come `wineserver`), garantendo prestazioni identiche al bare-metal Windows nei videogiochi.
  - Per la personalità macOS Darwin: mappa i `mach_port_set` e `kqueue` direttamente sullo stesso motore.

### 4.2. VMM Multi-Granularità con *Sub-Page Protection*

- **Il problema**: I binari Windows, Linux x86 e macOS x86_64 assumono che `PAGE_SIZE` sia sempre **4096 byte (4KB)**. Molte CPU moderne (es. Apple Silicon o profili AArch64 ad alte prestazioni) usano o preferiscono pagine da **16KB**. Se un binario chiama `mmap`/`VirtualAlloc` con permessi diversi (`R-X` e `RW-`) su due blocchi contigui da 4KB dentro una pagina hardware da 16KB, un kernel tradizionale va in crash o viola `W^X`.
- **La soluzione proprietaria OSify**: Il VMM di OSify traccia le allocazioni con granularità logica di **4KB** su tutte le architetture. Sulle porte con pagine fisiche da 4KB (`x86_64`, `AArch64-4K`, `riscv64`), la mappatura è diretta 1:1. Sulle porte con pagine da 16KB/64KB, `arch_mmu_map` utilizza tabelle di stato sub-pagina e page-shadowing automatico per garantire il rispetto rigoroso di **W^X** anche a livello di sotto-pagina da 4KB.

### 4.3. Contesto Registri Poliglotta (`TLS / Thread Pointer Switching`)

- Windows `x86_64` usa il registro `GS` per puntare al `TEB` (Thread Environment Block), mentre Linux `x86_64` usa `FS` per il Thread Local Storage e `GS` per il kernel; macOS usa `GS` con offset specifici.
- Nel contratto `arch.h` di OSify, ogni `osify_ctx_t` mantiene **due puntatori TLS utente indipendenti** (`user_tls_primary` e `user_tls_secondary`) salvati e ripristinati in hardware durante il context switch. Un processo può persino chiamare codice Windows e codice nativo OSify nello stesso thread senza corrompere i registri segmento/sistema (`FSBase`/`GSBase` su x86_64, `TPIDR_EL0`/`TPIDRRO_EL0` su AArch64, `tp` su RISC-V).

### 4.4. IPC Proprietaria `OSify RingBus` (Zero-Copy)

- Invece di copiare byte tramite `read`/`write` come nelle pipe UNIX tradizionali, l'IPC nativa di OSify utilizza `sys_ringbus_create()`: istanzia una coppia di ring buffer lock-free (Submission Queue / Completion Queue) in memoria condivisa tra due processi (es. un'app e il Window Server `Obsidian Dark Glass`, o un'app e lo stack di rete/audio).
- I comandi grafici, i buffer audio PCM e i pacchetti di rete viaggiano a **zero copie di memoria** e spesso **zero syscall** (grazie al polling cooperativo del kernel), riducendo la latenza grafica e audio ai minimi fisici dell'hardware.

---

## 5. Il Contratto Hardware Esteso (`arch.h` + `arch_hv.h`)

Nessuna istruzione dipendente dalla CPU può esistere fuori da `sistema/nucleo/arch/<arch>/`.

### Contratto Supervisore (`arch.h`)
- Inizializzazione SMP, topologia CPU, registri timer, RDRAND/entropia.
- Paginazione hardware e W^X validation.
- Context Switch poliglotta con `arch_ctx_set_tls` e `arch_enter_user`.
- Accesso sicuro spazio utente (`arch_copy_from_user`, `arch_copy_to_user`).

### Contratto Hypervisor (`arch_hv.h`)
- Rilevamento estensioni di virtualizzazione hardware (Intel VT-x, AMD-V, ARM EL2 Stage-2, RISC-V H-Extension).
- Creazione e ciclo di vita di celle di isolamento hardware `osify_cell_t`.
- Configurazione tabelle SLAT (Second-Level Address Translation: EPT/NPT/Stage-2).
- Esecuzione vCPU e dispatching dei `osify_vmexit_t`.

---

## 6. Formato Proprietario `.ify` e Window Server Obsidian Dark Glass

1. **Formato Applicativo `.ify` (OSify Native Package)**:
   - Contiene il manifesto firmato crittograficamente (`manifest.ifym`), asset, e il binario intermedio **OSifyIR**.
   - Compilazione **AOT (Ahead-Of-Time)** locale gestita da `pkgd` con abilitazione delle estensioni vettoriali native del processore (AVX2, NEON, RVV).
   - Isolamento a Capability Tokens basato sulle dichiarazioni del manifesto.
2. **Window Server `Obsidian Dark Glass`**:
   - Comunicazione zero-copy con i client tramite **OSify RingBus**.
   - Compositing su Linear Framebuffer con curve Squircle hardware/software, sfocatura multi-passaggio Dark Glass e palette ciano/ardesia.
   - Esposizione del protocollo **ODGP (OSify Display & GPU Protocol)** per il mapping diretto di Metal (macOS) e DirectX/Vulkan (Windows).

---

## 7. Il Ponte di Compatibilità Universale (UEM) Completo

### 7.1. Sottosistema macOS / Darwin (`OSIFY_PERS_DARWIN` + Orchid Framework)
- **`osify-dyld`**: loader Ring 3 per slice Mach-O e Fat Binary `0xCAFEBABE`, binding opcodes e commpage mapping.
- **Dual-ABI Dispatcher Kernel**: smistamento simultaneo di BSD Syscalls (classe `0x2000000`) verso il VFS/rete e Mach Traps (classe `0x1000000`) verso le Porte IPC e il `WaitMux` di OSify.
- **Orchid Clean-Room Framework**: implementazione in spazio utente di `libSystem`, `libobjc`, `CoreFoundation`, `Cocoa` e transpilazione `Metal` $\rightarrow$ ODGP Obsidian.

### 7.2. Sottosistema Windows NT (`OSIFY_PERS_NT`)
- Emulazione diretta delle syscall `ntoskrnl` (`NtCreateFile`, `NtAllocateVirtualMemory`, `NtWaitForMultipleObjects`).
- DLL di sistema pulite clean-room in Ring 3 (`ntdll.dll`, `kernel32.dll`, `d3d11.dll`) con mapping diretto su VFS e ODGP.

### 7.3. Architettura OSify Aegis (HVCS: Hardware-Virtualized Containment Sandbox)
- **Risoluzione del paradosso degli Anti-Cheat (.sys)**:
  - Gli anti-cheat (Vanguard, EAC, BattlEye) richiedono Ring 0 e verificano `CR3`, IDT e MSR.
  - Caricarli nel Ring 0 di OSify distruggerebbe la sicurezza del sistema ospite.
  - **La Cella Aegis**: Il driver `.sys` gira a **vero Ring 0 hardware dentro una Cella Aegis virtualizzata via SLAT/EPT/Stage-2**.
  - **Mutual Blindness (Isolamento Bidirezionale)**: L'anti-cheat vede il processo gioco e l'ambiente NT virtualizzato, ma non può leggere un solo byte del kernel OSify né dei file privati dell'utente. Al contempo, i processi di OSify non possono manomettere la Cella Aegis (garantendo l'integrità del match competitivo con attestazione vTPM).

---

## 8. Roadmap Ingegneristica delle 12 Fasi

- **Fase 0**: Contratto `arch.h`, porte `x86_64` e `AArch64`, serial log, panic handler.
- **Fase 1**: PMM Buddy, VMM Multi-Granularità (Sub-Page 4K/16K), Slab Heap, W^X.
- **Fase 2**: Interrupt, Timer tickless, Scheduler SMP, Context Switch Poliglotta (Dual-TLS), `WaitMux`.
- **Fase 3**: Ring 3, Capability Handles, `spawn`/`wait`/`exit`, `OSifyCrypt`, `copy_from/to_user`.
- **Fase 4**: VFS, `OSifyFS v2` (Extent + COW + BLAKE3), FAT32, `virtio-blk`, NVMe.
- **Fase 5**: IPC `OSify RingBus` zero-copy, Window Server `Obsidian Dark Glass` in Ring 3, `virtio-gpu`.
- **Fase 6**: Stack di rete nativo (TCP/UDP/DHCP/DNS), TLS 1.3 nativo (`OSifyCrypt`), formato `.ify` AOT.
- **Fase 7**: Ponte UEM Fase 1: Personalità `OSIFY_PERS_LINUX` (ELF) + MS-DOS / JVM.
- **Fase 8**: Ponte UEM Fase 2: Personalità `OSIFY_PERS_NT` + Loader PE/COFF + DLL Win32 + `cpu_bridge`.
- **Fase 9**: Ponte UEM Fase 3: Personalità `OSIFY_PERS_DARWIN` (Mach+BSD) + `osify-dyld` + *Orchid*.
- **Fase 10**: **OSify Aegis (`arch_hv.h`)**: Contenimento Hardware SLAT/EPT per driver `.sys` Anti-Cheat.
- **Fase 11**: Hardware Reale & Bootloader Proprietario (`osify-boot` UEFI/BIOS) + Porta `i686` e `riscv64`.
- **Fase 12**: **Self-Hosting Completo**: Toolchain LLVM/Clang portata su ABI nativa OSify.

---

## 9. Le 7 Leggi Inviolabili del Codice OSify (per `LEZIONI.md`)

1. **Isolamento Architetturale Assoluto**: Nessun registro (`CR3`, `TTBR0`, `satp`), istruzione assembly o primitiva di virtualizzazione (`vmxon`, `hvc`) può comparire fuori da `sistema/nucleo/arch/<arch>/`.
2. **Principio del Superset Nativo**: Quando un sottosistema del kernel viene progettato (IPC, sincronizzazione, VMM, TLS), deve essere progettato come *superset* capace di soddisfare nativamente OSify, Windows NT, macOS Darwin e Linux, mai come clone limitato di uno solo di essi.
3. **Sicurezza Hardware prima della Compatibilità Cieca**: Nessun codice binario di terze parti (driver `.sys`, `.kext`, moduli esterni) può mai entrare nel Ring 0 nativo di OSify; qualsiasi codice esterno che richieda privilegi Ring 0 deve essere confinato in una **Cella Aegis** via `arch_hv.h` (SLAT/EPT/Stage-2).
4. **Zero Indirizzi Magici**: Nessun driver può usare porte I/O o indirizzi MMIO cablati nel codice (eccetto i driver esplicitamente confinati in `driver/x86_legacy/` per i686); tutta la scoperta hardware avviene via PCIe ECAM, ACPI o DeviceTree.
5. **Verità Ingegneristica nei Test**: Una funzionalità è considerata "Operativa" nella documentazione solo quando possiede un test automatizzato in `tests/qemu/` che la verifica su almeno due architetture.
6. **Imposizione W^X Incondizionata**: Nessuna pagina di memoria — né nel kernel, né in userspace, né nei traduttori JIT — può mai avere contemporaneamente i bit di Scrittura ed Esecuzione attivi (`OSIFY_MAP_W | OSIFY_MAP_X` restituisce sempre errore in `arch_mmu_map`).
7. **Purezza delle Licenze**: Il codice del kernel e delle librerie di sistema deve essere 100% originale o compatibile con la licenza del progetto; è tassativamente vietato copiare codice GPLv2-only dal kernel Linux.
