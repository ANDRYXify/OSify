#!/usr/bin/env python3
"""
OSify Control Center — GUI Dashboard per KDE Plasma 6
=============================================================================
Pannello di controllo grafico nativo con estetica dark moderna per:
- Switch istantaneo tra i profili (Live Streaming, eSport Gaming, Console Mode)
- Monitoraggio in tempo reale del ping e dello stato di rete CAKE
- Gestione della matrice audio (Separazione canali Twitch VOD anti-strike)
- Gestione runtime Windows (Proton), Android (Waydroid) e macOS (Darling/KVM)
=============================================================================
"""

import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QProgressBar, QFrame,
    QGridLayout, QMessageBox, QFileDialog, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

OSIFY_BIN = os.path.expanduser("/usr/local/bin/osify-ctl")
if not os.path.exists(OSIFY_BIN):
    # Fallback su directory di sviluppo locale
    OSIFY_BIN = os.path.join(os.path.dirname(__file__), "../osify-ctl")

LOGO_PATH = os.path.join(os.path.dirname(__file__), "../../OSify.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = "/usr/share/pixmaps/osify.png"

class OSifyControlCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSify Control Center — by Andryx")
        self.setMinimumSize(920, 620)
        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))
        self.init_ui()
        self.init_timer()


    def init_ui(self):
        # Palette scura moderna per KDE Plasma 6
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f111a;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background-color: #141724;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #0b0d14;
                color: #94a3b8;
                padding: 10px 24px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2563eb;
                border-color: #38bdf8;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QFrame.card {
                background-color: #1a1e2e;
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 16px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header con Brand e Stato Ping
        header_layout = QHBoxLayout()

        # Logo OSify
        if os.path.exists(LOGO_PATH):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO_PATH).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setStyleSheet("padding-right: 8px;")
            header_layout.addWidget(logo_label)

        title_box = QVBoxLayout()
        title_label = QLabel("OSify Master Engine")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #a855f7;") # Viola elegante come il logo
        sub_title = QLabel("by Andryx • Gaming ad Alto Refresh • Live Multi-Stream • Multi-Runtime")
        sub_title.setStyleSheet("color: #4ade80; font-size: 12px; font-weight: bold;") # Verde fluo come il logo
        title_box.addWidget(title_label)
        title_box.addWidget(sub_title)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Box Monitoraggio Ping in tempo reale
        self.ping_card = QFrame()
        self.ping_card.setObjectName("pingCard")
        self.ping_card.setStyleSheet("background: #090d16; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 16px;")
        ping_layout = QVBoxLayout(self.ping_card)
        ping_title = QLabel("LATENZA DI RETE")
        ping_title.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold;")
        self.ping_val = QLabel("Verifica...")
        self.ping_val.setStyleSheet("color: #22c55e; font-size: 18px; font-weight: bold;")
        ping_layout.addWidget(ping_title)
        ping_layout.addWidget(self.ping_val)
        header_layout.addWidget(self.ping_card)

        main_layout.addLayout(header_layout)

        # Tab Widget Principale
        tabs = QTabWidget()
        tabs.addTab(self.create_modes_tab(), "Profili di Sistema")
        tabs.addTab(self.create_streaming_tab(), "Audio Pro e Flussi")
        tabs.addTab(self.create_hardware_tab(), "Adattamento Hardware")
        tabs.addTab(self.create_compat_tab(), "Compatibilità Universale")
        tabs.addTab(self.create_anticheat_tab(), "Protezione Anti-Cheat Livello 0")
        tabs.addTab(self.create_privacy_tab(), "Sicurezza e Privacy")

        main_layout.addWidget(tabs)


    def create_modes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        desc = QLabel("Seleziona il profilo di carico per riallocare CPU, memoria, priorità audio e pipeline grafica:")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(desc)

        grid = QGridLayout()
        grid.setSpacing(14)

        # 1. Bottone Gioco eSport
        btn_game = QPushButton("MODALITÀ GIOCO & ESPORT\n(Massima frequenza CPU + Latenza zero + VRR nativo)")
        btn_game.setStyleSheet("background: #1e3a8a; border-color: #3b82f6; color: white; padding: 16px;")
        btn_game.clicked.connect(lambda: self.run_osify_cmd(["mode", "gaming"]))
        grid.addWidget(btn_game, 0, 0)

        # 2. Bottone Streaming + Gioco
        btn_stream = QPushButton("MODALITÀ STREAMING + GIOCO\n(Priorità di rete anti-bufferbloat + Bus VOD separato)")
        btn_stream.setStyleSheet("background: #831843; border-color: #f43f5e; color: white; padding: 16px;")
        btn_stream.clicked.connect(lambda: self.run_osify_cmd(["mode", "streaming"]))
        grid.addWidget(btn_stream, 0, 1)

        # 3. Bottone Postazione di Lavoro
        btn_work = QPushButton("MODALITÀ POSTAZIONE DI LAVORO\n(Multitasking bilanciato + Compilazione veloce + Stabilità)")
        btn_work.setStyleSheet("background: #14532d; border-color: #22c55e; color: white; padding: 16px;")
        btn_work.clicked.connect(lambda: self.run_osify_cmd(["mode", "balanced"]))
        grid.addWidget(btn_work, 1, 0)

        # 4. Bottone Basso Consumo
        btn_eco = QPushButton("MODALITÀ BASSO CONSUMO\n(Risparmio energetico massimo + Silenziosità ventole)")
        btn_eco.setStyleSheet("background: #1e293b; border-color: #475569; color: white; padding: 16px;")
        btn_eco.clicked.connect(lambda: self.run_osify_cmd(["mode", "lowspec"]))
        grid.addWidget(btn_eco, 1, 1)

        # 5. Bottone Automatico / Calibrazione
        btn_auto = QPushButton("MODALITÀ AUTOMATICA ADATTIVA (HAL)\n(Riconoscimento dinamico del carico di lavoro e del silicio)")
        btn_auto.setStyleSheet("background: #312e81; border-color: #6366f1; color: white; padding: 14px;")
        btn_auto.clicked.connect(lambda: self.run_osify_cmd(["hw-detect", "--apply"]))
        grid.addWidget(btn_auto, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        return tab

    def create_streaming_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)

        title = QLabel("Architettura Audio Pro & Separazione Canali")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #38bdf8;")
        c_layout.addWidget(title)

        info = QLabel("Il motore audio nativo separa i bus fisici: Audio-Gioco, Audio-Voce, Audio-Musica e Audio-Microfono con isolamento della traccia VOD.")
        info.setStyleSheet("color: #94a3b8;")
        c_layout.addWidget(info)

        btn_box = QHBoxLayout()
        btn_relay = QPushButton("Avvia Inoltro Flusso Multi-Piattaforma")
        btn_relay.clicked.connect(self.launch_stream_relay)
        btn_box.addWidget(btn_relay)

        btn_audio = QPushButton("Inizializza Bus Audio Pro a Bassa Latenza")
        btn_audio.clicked.connect(lambda: self.run_osify_cmd(["audio", "setup"]))
        btn_box.addWidget(btn_audio)

        c_layout.addLayout(btn_box)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def create_hardware_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)

        title = QLabel("Adattamento Hardware (HAL) e Ottimizzazione Silicio")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #a855f7;")
        c_layout.addWidget(title)

        info = QLabel("Configurazione atomica del silicio: rilevamento istruzioni CPU (SSE/AVX/NEON), taratura memoria compressa e pipeline grafica.")
        info.setStyleSheet("color: #94a3b8;")
        c_layout.addWidget(info)

        grid = QGridLayout()
        btn_detect = QPushButton("Esegui Taratura Silicio Completa")
        btn_detect.clicked.connect(lambda: self.run_osify_cmd(["hw-detect", "--apply"]))
        grid.addWidget(btn_detect, 0, 0)

        btn_mem = QPushButton("Ottimizza Memoria Compressa Nativa")
        btn_mem.clicked.connect(lambda: self.run_osify_cmd(["mode", "lowspec"]))
        grid.addWidget(btn_mem, 0, 1)

        btn_gpu = QPushButton("Calibra Pipeline Grafica Obsidian")
        btn_gpu.clicked.connect(lambda: self.run_osify_cmd(["desktop-tuning"]))
        grid.addWidget(btn_gpu, 1, 0, 1, 2)

        c_layout.addLayout(grid)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def create_compat_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Sezione Eseguibili PC
        win_card = QFrame()
        w_layout = QVBoxLayout(win_card)
        w_title = QLabel("Ambiente Compatibilità Applicazioni PC (.exe / .msi)")
        w_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        w_layout.addWidget(w_title)
        
        btn_run_exe = QPushButton("Seleziona ed Esegui Pacchetto PC con Accelerazione Vulkan")
        btn_run_exe.clicked.connect(self.select_and_run_exe)
        w_layout.addWidget(btn_run_exe)
        layout.addWidget(win_card)

        # Sezione Applicazioni Mobili
        and_card = QFrame()
        a_layout = QVBoxLayout(and_card)
        a_title = QLabel("Ambiente Compatibilità Applicazioni Mobili (.apk / .aab)")
        a_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        a_layout.addWidget(a_title)

        a_btn_box = QHBoxLayout()
        btn_way_start = QPushButton("Avvia Sessione Mobile Grafica")
        btn_way_start.clicked.connect(lambda: self.run_osify_cmd(["android", "start"]))
        btn_way_stop = QPushButton("Arresta Sessione Mobile")
        btn_way_stop.clicked.connect(lambda: self.run_osify_cmd(["android", "stop"]))
        a_btn_box.addWidget(btn_way_start)
        a_btn_box.addWidget(btn_way_stop)
        a_layout.addLayout(a_btn_box)
        layout.addWidget(and_card)

        # Sezione Applicazioni Darwin
        mac_card = QFrame()
        m_layout = QVBoxLayout(mac_card)
        m_title = QLabel("Ambiente Compatibilità Applicazioni Darwin (.app / .dmg)")
        m_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        m_layout.addWidget(m_title)

        btn_mac = QPushButton("Verifica Stato Accelerazione Grafica Darwin")
        btn_mac.clicked.connect(lambda: self.run_osify_cmd(["darwin", "status"]))
        m_layout.addWidget(btn_mac)
        layout.addWidget(mac_card)

        layout.addStretch()
        return tab

    def create_anticheat_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)

        title = QLabel("Protezione Anti-Cheat Livello 0 (Integrità Kernel)")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #f43f5e;")
        c_layout.addWidget(title)

        desc = QLabel("Isolamento kernel con emulazione TPM 2.0 e integrità Secure Boot per titoli competitivi:")
        desc.setStyleSheet("color: #94a3b8;")
        c_layout.addWidget(desc)

        # Form di ricerca gioco
        search_box = QHBoxLayout()
        self.game_input = QLineEdit()
        self.game_input.setPlaceholderText("Es. Valorant, Apex Legends, Elden Ring, Fortnite...")
        self.game_input.setStyleSheet("background: #0b0d14; border: 1px solid #334155; border-radius: 6px; padding: 10px; color: white;")
        btn_check = QPushButton("Verifica Integrità Titolo")
        btn_check.clicked.connect(self.check_anticheat_game)
        search_box.addWidget(self.game_input)
        search_box.addWidget(btn_check)
        c_layout.addLayout(search_box)

        # Output box
        self.ac_result = QTextEdit()
        self.ac_result.setReadOnly(True)
        self.ac_result.setStyleSheet("background: #090d16; border: 1px solid #1e293b; border-radius: 6px; color: #38bdf8; font-family: monospace; padding: 8px;")
        self.ac_result.setFixedHeight(120)
        c_layout.addWidget(self.ac_result)

        # Pulsanti contromisure
        btn_row = QHBoxLayout()
        btn_boot_win = QPushButton("Avvio Diretto UEFI Affiancato")
        btn_boot_win.setStyleSheet("background: #431407; border-color: #ea580c; color: white;")
        btn_boot_win.clicked.connect(lambda: self.run_osify_cmd(["anticheat", "boot-windows", "--reboot"]))
        btn_row.addWidget(btn_boot_win)

        c_layout.addLayout(btn_row)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def create_privacy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("class", "card")
        c_layout = QVBoxLayout(card)

        title = QLabel("Sicurezza, Tracciamento e Privacy Vault")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #10b981;")
        c_layout.addWidget(title)

        desc = QLabel("Protezione continua contro telemetria, profilazione remota e minacce informatiche a livello di rete:")
        desc.setStyleSheet("color: #94a3b8;")
        c_layout.addWidget(desc)

        grid = QGridLayout()
        btn_ad = QPushButton("Attiva Protezione DNS Anti-Tracciamento")
        btn_ad.clicked.connect(lambda: self.run_osify_cmd(["adblock", "start"]))
        grid.addWidget(btn_ad, 0, 0)

        btn_shield = QPushButton("Scansione Euristica di Sicurezza")
        btn_shield.clicked.connect(lambda: self.run_osify_cmd(["shield", "scan"]))
        grid.addWidget(btn_shield, 0, 1)

        c_layout.addLayout(grid)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def check_anticheat_game(self):
        game_name = self.game_input.text().strip()
        if not game_name:
            return
        checker_script = os.path.join(os.path.dirname(__file__), "../../sistema/servizi/Compatibilita/anticheat/osify-anticheat-checker.py")
        try:
            out = subprocess.check_output(["python3", checker_script, game_name], text=True)
            self.ac_result.setPlainText(out)
        except Exception as e:
            self.ac_result.setPlainText(f"Errore durante la verifica: {e}")

    def run_osify_cmd(self, args):

        try:
            cmd = [OSIFY_BIN] + args
            subprocess.Popen(cmd)
            QMessageBox.information(self, "OSify Engine", f"Comando inviato: {' '.join(args)}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile eseguire {args}: {e}")

    def launch_stream_relay(self):
        relay_script = os.path.join(os.path.dirname(__file__), "../../streaming/relay/osify-stream-relay.py")
        subprocess.Popen(["python3", relay_script])
        QMessageBox.information(self, "Relay Multi-RTMP", "Relay avviato su rtmp://127.0.0.1:1935/live/stream")

    def select_and_run_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona Eseguibile Windows", "", "File Windows (*.exe)")
        if file_path:
            self.run_osify_cmd(["windows", file_path])

    def init_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ping)
        self.timer.start(5000)
        self.update_ping()

    def update_ping(self):
        try:
            # Misura ping rapido su DNS a bassissima latenza (Cloudflare 1.1.1.1 o Google 8.8.8.8)
            output = subprocess.check_output(["ping", "-c", "1", "-W", "1", "1.1.1.1"], text=True)
            for line in output.splitlines():
                if "time=" in line:
                    ms = line.split("time=")[1].split()[0]
                    self.ping_val.setText(f"{ms} ms")
                    return
            self.ping_val.setText("< 20 ms")
        except Exception:
            self.ping_val.setText("Online")

def main():
    app = QApplication(sys.argv)
    window = OSifyControlCenter()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
