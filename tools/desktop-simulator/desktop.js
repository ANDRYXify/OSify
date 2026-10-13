/**
 * OSify Interactive Desktop Engine
 * Ingegnerizzato da Andrea Taliento (ANDRYXify)
 */

document.addEventListener("DOMContentLoaded", () => {
    let topZIndex = 100;
    const windows = document.querySelectorAll(".os-window");
    const dockItems = document.querySelectorAll(".dock-item");
    const deskIcons = document.querySelectorAll(".desk-icon");

    // 1. OROLOGIO IN TEMPO REALE
    function updateClock() {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        document.getElementById("clock").textContent = `${hrs}:${mins}`;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. GESTIONE FINESTRE (PORTA IN PRIMO PIANO, DRAG, CLOSE/MAX)
    function bringToFront(win) {
        topZIndex += 1;
        windows.forEach(w => w.classList.remove("active-window"));
        win.style.zIndex = topZIndex;
        win.classList.add("active-window");
        win.style.display = "flex";
    }

    windows.forEach(win => {
        win.addEventListener("mousedown", () => bringToFront(win));

        // Dragging tramite Titlebar
        const titlebar = win.querySelector(".window-titlebar");
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        titlebar.addEventListener("mousedown", (e) => {
            if (e.target.classList.contains("light")) return; // Non trascinare se clicchi i pallini
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            initialLeft = win.offsetLeft;
            initialTop = win.offsetTop;
            bringToFront(win);
        });

        document.addEventListener("mousemove", (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            win.style.left = `${Math.max(0, initialLeft + dx)}px`;
            win.style.top = `${Math.max(32, initialTop + dy)}px`;
        });

        document.addEventListener("mouseup", () => {
            isDragging = false;
        });

        // Controlli Finestra (Pallini macOS)
        const btnClose = win.querySelector(".light.close");
        const btnMin = win.querySelector(".light.minimize");
        const btnMax = win.querySelector(".light.maximize");

        if (btnClose) {
            btnClose.addEventListener("click", (e) => {
                e.stopPropagation();
                win.style.display = "none";
            });
        }
        if (btnMin) {
            btnMin.addEventListener("click", (e) => {
                e.stopPropagation();
                win.style.display = "none";
            });
        }
        if (btnMax) {
            let isMax = false;
            let prevRect = {};
            btnMax.addEventListener("click", (e) => {
                e.stopPropagation();
                if (!isMax) {
                    prevRect = { left: win.style.left, top: win.style.top, width: win.style.width, height: win.style.height };
                    win.style.left = "0px";
                    win.style.top = "32px";
                    win.style.width = "100%";
                    win.style.height = "calc(100% - 90px)";
                    isMax = true;
                } else {
                    win.style.left = prevRect.left;
                    win.style.top = prevRect.top;
                    win.style.width = prevRect.width;
                    win.style.height = prevRect.height;
                    isMax = false;
                }
            });
        }
    });

    // 3. APERTURA APPLICAZIONI (DOCK & DESKTOP ICONS)
    const appWindowMap = {
        "browser": document.getElementById("win-browser"),
        "control-center": document.getElementById("win-control-center"),
        "terminal": document.getElementById("win-terminal"),
        "blocks": document.getElementById("win-blocks"),
        "presentation": document.getElementById("win-presentation"),
        "installer": document.getElementById("win-installer")
    };

    function openApp(appId) {
        const targetWin = appWindowMap[appId];
        if (targetWin) {
            bringToFront(targetWin);
        }
    }

    dockItems.forEach(item => {
        item.addEventListener("click", () => {
            const appId = item.getAttribute("data-app");
            openApp(appId);
        });
    });

    deskIcons.forEach(icon => {
        icon.addEventListener("dblclick", () => {
            const appId = icon.getAttribute("data-app");
            openApp(appId);
        });
        // Click singolo su touch o mobile
        icon.addEventListener("click", () => {
            const appId = icon.getAttribute("data-app");
            openApp(appId);
        });
    });

    // Finestra di default aperta in primo piano: Browser e Control Center
    bringToFront(document.getElementById("win-control-center"));
    bringToFront(document.getElementById("win-browser"));

    // 4. BROWSER WEB INTERATTIVO
    const browserFrame = document.getElementById("browser-frame");
    const browserUrlInput = document.getElementById("browser-url");
    const btnBrowserGo = document.getElementById("btn-browser-go");
    const bookmarks = document.querySelectorAll(".bm-item");

    function loadUrl(url) {
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "https://" + url;
        }
        browserUrlInput.value = url;
        browserFrame.src = url;
    }

    btnBrowserGo.addEventListener("click", () => loadUrl(browserUrlInput.value));
    browserUrlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") loadUrl(browserUrlInput.value);
    });

    bookmarks.forEach(bm => {
        bm.addEventListener("click", () => {
            const url = bm.getAttribute("data-url");
            loadUrl(url);
        });
    });

    document.getElementById("br-reload").addEventListener("click", () => {
        browserFrame.src = browserFrame.src;
    });

    // 5. CONTROL CENTER: SELETTORE PROFILI PRESTAZIONALI
    const pCards = document.querySelectorAll(".p-card");
    const lblRam = document.getElementById("lbl-ram-usage");
    const badgeProfile = document.getElementById("badge-current-profile");

    const profileData = {
        "card-gaming": {
            badge: "ESPORT GAMING (500 FPS)",
            ram: "RAM: 620 MB / 16 GB",
            ping: "Ping: 8ms (CAKE EF)"
        },
        "card-streaming": {
            badge: "ZERO-LAG STREAMING",
            ram: "RAM: 810 MB / 16 GB",
            ping: "Ping: 14ms (CAKE AF31)"
        },
        "card-vintage": {
            badge: "TOSHIBA NETBOOK NB200",
            ram: "RAM: 124 MB / 1 GB",
            ping: "Ping: 12ms (ZRAM lz4)"
        }
    };

    pCards.forEach(card => {
        card.addEventListener("click", () => {
            pCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            const data = profileData[card.id];
            if (data) {
                badgeProfile.textContent = data.badge;
                lblRam.textContent = data.ram;
            }
        });
    });

    // Anti-Cheat Checker
    const acInput = document.getElementById("ac-input");
    const btnCheckAc = document.getElementById("btn-check-ac");
    const acResult = document.getElementById("ac-result-badge");

    const acDatabase = {
        "valorant": {
            name: "Riot Vanguard (Ring-0 Kernel)",
            status: "RING0_BLOCK",
            desc: "Driver kernel Windows Ring-0 bloccante.<br><strong>Soluzione OSify</strong>: Profilo KVM Cloaked Stealth (CPUID hidden, SMBIOS ASUS ROG) oppure Fast-Boot UEFI istantaneo."
        },
        "elden ring": {
            name: "Easy Anti-Cheat (EAC Bridge)",
            status: "SUPPORTED",
            desc: "Pienamente compatibile con Proton-GE e modulo EAC nativo Linux di OSify. <strong>Nessun ostacolo.</strong>"
        },
        "apex legends": {
            name: "Easy Anti-Cheat Linux Native",
            status: "SUPPORTED",
            desc: "Pienamente compatibile e supportato ufficialmente con shader cache asincrona DXVK."
        },
        "fortnite": {
            name: "BattlEye / EAC Hybrid",
            status: "HYBRID",
            desc: "Richiede profilo Stealth VM KVM o Fast-Boot UEFI su partizione Windows nativa."
        }
    };

    btnCheckAc.addEventListener("click", () => {
        const query = acInput.value.trim().toLowerCase();
        const found = acDatabase[query] || {
            name: "Anti-Cheat Generico / Non Bloccante",
            status: "SUPPORTED",
            desc: "Compatibile tramite Proton-GE con Fsync (futex2) e DXVK ad alte prestazioni."
        };

        if (found.status === "RING0_BLOCK" || found.status === "HYBRID") {
            acResult.className = "result-box ring0-warn";
            acResult.innerHTML = `<strong>🛡️ ${found.name}</strong>: ${found.desc}`;
        } else {
            acResult.className = "result-box";
            acResult.style.background = "rgba(16, 185, 129, 0.15)";
            acResult.style.borderColor = "rgba(16, 185, 129, 0.4)";
            acResult.style.color = "#6EE7B7";
            acResult.innerHTML = `<strong>✓ ${found.name}</strong>: ${found.desc}`;
        }
    });

    // 6. BLOCCHI LEGO ARCHITETTURA (DINAMICI)
    const blocksData = [
        { id: "gaming", name: "🎮 Gaming & eSport Engine", desc: "Proton-GE, GameScope, BORE, Futex2, Mimalloc", active: true },
        { id: "streaming", name: "📡 Live Streaming Suite", desc: "CAKE QoS, Relay Twitch/Kick/YT, PipeWire Track 2", active: true },
        { id: "emulation", name: "🕹️ Console Emulation Matrix", desc: "RetroArch, RPCS3, Ryujinx, RADV GPL cache", active: true },
        { id: "vintage", name: "⚡ Vintage Netbook Engine", desc: "Tuning Intel Atom N280, ZRAM lz4, Openbox ultra-light", active: true },
        { id: "presentation", name: "📊 Presentazioni & NDI", desc: "PowerPoint Wine, EasyWorship, Inhibit Sleep", active: false },
        { id: "android", name: "🤖 Android Waydroid", desc: "GPU passthrough DRI3, traduttore ARM libndk", active: false }
    ];

    const blocksContainer = document.getElementById("blocks-container");
    if (blocksContainer) {
        blocksData.forEach(b => {
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.alignItems = "center";
            row.style.justifyContent = "space-between";
            row.style.padding = "10px 14px";
            row.style.background = "rgba(255, 255, 255, 0.04)";
            row.style.borderRadius = "8px";
            row.style.marginBottom = "8px";
            row.style.border = "1px solid rgba(255, 255, 255, 0.08)";

            row.innerHTML = `
                <div>
                    <strong style="color: #FFFFFF; font-size: 13px;">${b.name}</strong>
                    <div style="color: #94A3B8; font-size: 11px;">${b.desc}</div>
                </div>
                <button class="primary-neon-btn" style="background: ${b.active ? '#10B981' : '#333348'};">
                    ${b.active ? 'ATTIVO' : 'ABILITA'}
                </button>
            `;

            const btn = row.querySelector("button");
            btn.addEventListener("click", () => {
                b.active = !b.active;
                btn.style.background = b.active ? '#10B981' : '#333348';
                btn.textContent = b.active ? 'ATTIVO' : 'ABILITA';
            });

            blocksContainer.appendChild(row);
        });
    }

    // 7. MISSION CONTROL OVERLAY (F3 / macOS SPACES)
    const mcOverlay = document.getElementById("mission-control-overlay");
    const mcGrid = document.getElementById("mc-windows-grid");
    const btnToggleMc = document.getElementById("btn-toggle-mission-control");

    function toggleMissionControl() {
        const isHidden = mcOverlay.classList.contains("hidden");
        if (isHidden) {
            // Popola anteprime finestre
            mcGrid.innerHTML = "";
            windows.forEach(w => {
                if (w.style.display !== "none") {
                    const title = w.querySelector(".title-text").textContent;
                    const thumb = document.createElement("div");
                    thumb.className = "mc-thumb";
                    thumb.innerHTML = `
                        <div class="mc-thumb-title">${title}</div>
                        <div class="mc-thumb-preview">🖥️</div>
                    `;
                    thumb.addEventListener("click", () => {
                        mcOverlay.classList.add("hidden");
                        bringToFront(w);
                    });
                    mcGrid.appendChild(thumb);
                }
            });
            mcOverlay.classList.remove("hidden");
        } else {
            mcOverlay.classList.add("hidden");
        }
    }

    btnToggleMc.addEventListener("click", toggleMissionControl);
    document.addEventListener("keydown", (e) => {
        if (e.key === "F3") {
            e.preventDefault();
            toggleMissionControl();
        }
        if (e.key === "Escape" && !mcOverlay.classList.contains("hidden")) {
            mcOverlay.classList.add("hidden");
        }
    });

    // 8. SELETTORE RISOLUZIONE (TOSHIBA NB200 1024x600 VS FULL HD 1080p)
    const btnResNetbook = document.getElementById("btn-res-netbook");
    const btnResModern = document.getElementById("btn-res-modern");

    btnResNetbook.addEventListener("click", () => {
        document.body.className = "theme-cyberpunk mode-netbook";
        btnResNetbook.classList.add("active");
        btnResModern.classList.remove("active");
    });

    btnResModern.addEventListener("click", () => {
        document.body.className = "theme-cyberpunk mode-modern";
        btnResModern.classList.add("active");
        btnResNetbook.classList.remove("active");
    });

    // 9. SIMULAZIONE INSTALLATORE LIVE
    const btnRunInstall = document.getElementById("btn-run-live-install");
    const instProgress = document.getElementById("inst-progress");
    const instStatus = document.getElementById("inst-status-label");

    if (btnRunInstall) {
        btnRunInstall.addEventListener("click", () => {
            btnRunInstall.disabled = true;
            instProgress.style.width = "0%";
            instStatus.textContent = "Preparazione partizioni Btrfs...";

            let step = 0;
            const steps = [
                { p: "25%", msg: "Formattazione disco con subvolumi Btrfs compressi zstd..." },
                { p: "50%", msg: "Copia sistema base OSify e kernel BORE ultra-low-latency..." },
                { p: "75%", msg: "Configurazione bootloader UEFI e Syslinux MBR..." },
                { p: "100%", msg: "Rimozione partizione temporanea OSIFY_BOOT. Fatto!" }
            ];

            const interval = setInterval(() => {
                if (step < steps.length) {
                    instProgress.style.width = steps[step].p;
                    instStatus.textContent = steps[step].msg;
                    step++;
                } else {
                    clearInterval(interval);
                    instStatus.innerHTML = "<strong style='color: #10B981;'>✓ Installazione completata con successo! Pronto al riavvio.</strong>";
                    btnRunInstall.textContent = "INSTALLAZIONE COMPLETATA";
                    btnRunInstall.style.background = "#10B981";
                }
            }, 800);
        });
    }
});
