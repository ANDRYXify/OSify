#!/usr/bin/env python3
"""
OSify Wi-Fi Manager 2050 (Native macOS Aesthetics)
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Gestore Wi-Fi grafico nativo in Python / Tkinter:
- Scansione automatica e reattiva delle reti Wi-Fi (iw, nmcli, wpa_supplicant)
- Interfaccia Dark Glass con intensita del segnale e indicatori di sicurezza
- Connessione con un click WPA/WPA2/WPA3 e memorizzazione credenziali
=============================================================================
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

def find_iface():
    try:
        out = subprocess.check_output("iw dev 2>/dev/null", shell=True, text=True)
        for line in out.splitlines():
            if "Interface" in line:
                return line.split()[1]
    except Exception:
        pass
    for cand in ["wlan0", "wlp2s0", "wlp3s0", "ath0"]:
        if os.path.exists(f"/sys/class/net/{cand}"):
            return cand
    return "wlan0"

def get_current_ssid(iface):
    try:
        out = subprocess.check_output(f"iwgetid {iface} -r 2>/dev/null", shell=True, text=True).strip()
        if out:
            return out
    except Exception:
        pass
    return None

def scan_ssids(iface):
    networks = []
    seen = set()
    
    # 1. Prova con iw
    try:
        subprocess.run(f"ip link set {iface} up 2>/dev/null || ifconfig {iface} up 2>/dev/null", shell=True)
        out = subprocess.check_output(f"iw dev {iface} scan 2>/dev/null", shell=True, text=True)
        curr_ssid = ""
        curr_sig = "50%"
        curr_sec = "WPA2"
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("SSID:"):
                curr_ssid = line.split(":", 1)[1].strip()
            elif line.startswith("signal:"):
                try:
                    dbm = float(line.split()[1])
                    sig_p = max(10, min(100, int((dbm + 100) * 2)))
                    curr_sig = f"{sig_p}%"
                except Exception:
                    pass
            elif "RSN" in line or "WPA" in line:
                curr_sec = "WPA2/WPA3"
            elif line.startswith("BSS "):
                if curr_ssid and curr_ssid not in seen:
                    seen.add(curr_ssid)
                    networks.append((curr_ssid, curr_sig, curr_sec))
                curr_ssid = ""
                curr_sig = "50%"
                curr_sec = "Aperta"
        if curr_ssid and curr_ssid not in seen:
            seen.add(curr_ssid)
            networks.append((curr_ssid, curr_sig, curr_sec))
    except Exception:
        pass

    # 2. Prova con nmcli se vuoto
    if not networks:
        try:
            out = subprocess.check_output("nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list 2>/dev/null", shell=True, text=True)
            for line in out.splitlines():
                parts = line.strip().split(":")
                if len(parts) >= 2 and parts[0] and parts[0] not in seen:
                    seen.add(parts[0])
                    sec = parts[2] if len(parts) > 2 and parts[2] else "Aperta"
                    networks.append((parts[0], f"{parts[1]}%", sec))
        except Exception:
            pass

    return sorted(networks, key=lambda x: int(x[1].replace("%", "")), reverse=True)

class OSifyWifiApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OSify — Connessione Wi-Fi")
        self.root.geometry("480x560")
        self.root.minsize(440, 480)
        self.root.configure(bg="#0b0e17")
        
        self.iface = find_iface()
        self.networks = []
        self.selected_ssid = None
        
        # Centra la finestra
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw-w)//2}+{max(40, (sh-h)//2 - 20)}")
        
        self.build_ui()
        self.refresh_scan()

    def build_ui(self):
        # Header
        head = tk.Frame(self.root, bg="#111625", padx=16, pady=14)
        head.pack(fill=tk.X)
        
        t_box = tk.Frame(head, bg="#111625")
        t_box.pack(side=tk.LEFT)
        tk.Label(t_box, text="Reti Senza Fili", font=("Helvetica", 16, "bold"), fg="#f8fafc", bg="#111625").pack(anchor="w")
        self.lbl_curr = tk.Label(t_box, text="Rilevamento in corso...", font=("Helvetica", 9), fg="#38bdf8", bg="#111625")
        self.lbl_curr.pack(anchor="w")
        
        btn_refresh = tk.Button(
            head, text="↻ Scansiona", font=("Helvetica", 9, "bold"),
            bg="#1e293b", fg="#f8fafc", activebackground="#38bdf8",
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            command=self.refresh_scan
        )
        btn_refresh.pack(side=tk.RIGHT)
        
        # Lista reti (Container scrollabile o pack)
        self.body = tk.Frame(self.root, bg="#0b0e17", padx=16, pady=10)
        self.body.pack(fill=tk.BOTH, expand=True)
        
        # Sezione Connessione Password in basso
        self.conn_frame = tk.Frame(self.root, bg="#111625", padx=16, pady=12)
        self.conn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.sel_lbl = tk.Label(self.conn_frame, text="Seleziona una rete per connetterti", font=("Helvetica", 10, "bold"), fg="#f8fafc", bg="#111625")
        self.sel_lbl.pack(anchor="w")
        
        inp_row = tk.Frame(self.conn_frame, bg="#111625")
        inp_row.pack(fill=tk.X, pady=(6, 0))
        
        self.pwd_var = tk.StringVar()
        self.pwd_entry = tk.Entry(inp_row, textvariable=self.pwd_var, show="•", font=("Helvetica", 11), bg="#1e293b", fg="#ffffff", insertbackground="#38bdf8", relief=tk.FLAT)
        self.pwd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 8))
        self.pwd_entry.bind("<Return>", lambda e: self.do_connect())
        
        self.btn_connect = tk.Button(
            inp_row, text="Connetti", font=("Helvetica", 10, "bold"),
            bg="#0284c7", fg="#ffffff", activebackground="#38bdf8",
            relief=tk.FLAT, padx=16, pady=4, cursor="hand2",
            command=self.do_connect
        )
        self.btn_connect.pack(side=tk.RIGHT)

    def refresh_scan(self):
        curr = get_current_ssid(self.iface)
        if curr:
            self.lbl_curr.config(text=f"Connesso a: {curr} ({self.iface})", fg="#10b981")
        else:
            self.lbl_curr.config(text=f"Interfaccia attiva: {self.iface} (Disconnesso)", fg="#94a3b8")
            
        for w in self.body.winfo_children():
            w.destroy()
            
        loading = tk.Label(self.body, text="Scansione reti wireless in corso...", font=("Helvetica", 10), fg="#64748b", bg="#0b0e17", pady=30)
        loading.pack()
        self.root.update_idletasks()
        
        self.networks = scan_ssids(self.iface)
        loading.destroy()
        
        if not self.networks:
            tk.Label(self.body, text="Nessuna rete Wi-Fi trovata nelle vicinanze.\nAssicurati che lo switch fisico sia acceso.", font=("Helvetica", 10), fg="#94a3b8", bg="#0b0e17", pady=40).pack()
            return
            
        for ssid, sig, sec in self.networks[:10]:
            is_active = (ssid == curr)
            row = tk.Frame(self.body, bg="#1e293b" if is_active else "#131929", padx=10, pady=8, cursor="hand2", highlightthickness=1, highlightbackground="#38bdf8" if is_active else "#1e293b")
            row.pack(fill=tk.X, pady=2)
            
            ico = "" if "WPA" in sec else ""
            tk.Label(row, text=ico, font=("Helvetica", 11), bg=row["bg"], fg="#38bdf8").pack(side=tk.LEFT, padx=(2, 8))
            
            name_lbl = tk.Label(row, text=ssid, font=("Helvetica", 11, "bold" if is_active else "normal"), fg="#38bdf8" if is_active else "#f8fafc", bg=row["bg"], anchor="w")
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            sig_lbl = tk.Label(row, text=f"{sig}  {sec}", font=("Helvetica", 8), fg="#94a3b8", bg=row["bg"])
            sig_lbl.pack(side=tk.RIGHT)
            
            def on_click(e, s=ssid):
                self.selected_ssid = s
                self.sel_lbl.config(text=f"Rete selezionata: {s}")
                self.pwd_entry.delete(0, tk.END)
                self.pwd_entry.focus_set()
                
            for w in (row, name_lbl, sig_lbl):
                w.bind("<Button-1>", on_click)

    def do_connect(self):
        if not self.selected_ssid:
            messagebox.showwarning("Selezione Richiesta", "Seleziona prima una rete Wi-Fi dalla lista.")
            return
        pwd = self.pwd_var.get().strip()
        ssid = self.selected_ssid
        
        self.btn_connect.config(text="Connessione...", state=tk.DISABLED)
        self.root.update_idletasks()
        
        # Connessione wpa_supplicant o nmcli
        success = False
        try:
            if subprocess.run("command -v nmcli >/dev/null 2>&1", shell=True).returncode == 0:
                cmd = f"nmcli dev wifi connect '{ssid}'"
                if pwd:
                    cmd += f" password '{pwd}'"
                r = subprocess.run(cmd, shell=True, timeout=15)
                success = (r.returncode == 0)
            else:
                # wpa_supplicant nativo
                wpa_conf = f"/etc/wpa_supplicant/{self.iface}.conf"
                os.makedirs(os.path.dirname(wpa_conf), exist_ok=True)
                if pwd:
                    subprocess.run(f"wpa_passphrase '{ssid}' '{pwd}' > '{wpa_conf}' 2>/dev/null", shell=True)
                else:
                    with open(wpa_conf, "w") as f:
                        f.write(f'network={{\n    ssid="{ssid}"\n    key_mgmt=NONE\n}}\n')
                subprocess.run(f"killall wpa_supplicant 2>/dev/null || true", shell=True)
                subprocess.run(f"wpa_supplicant -B -i {self.iface} -c '{wpa_conf}' 2>/dev/null", shell=True)
                subprocess.run(f"udhcpc -i {self.iface} -n -q -t 5 2>/dev/null || dhclient {self.iface} 2>/dev/null || true", shell=True)
                time.sleep(2)
                curr = get_current_ssid(self.iface)
                success = (curr == ssid)
        except Exception as e:
            pass
            
        self.btn_connect.config(text="Connetti", state=tk.NORMAL)
        if success:
            messagebox.showinfo("Wi-Fi Connesso", f"Connessione a '{ssid}' completata con successo!")
            self.refresh_scan()
        else:
            messagebox.showerror("Connessione Fallita", f"Impossibile connettersi a '{ssid}'. Verifica la password.")

if __name__ == "__main__":
    app = OSifyWifiApp()
    app.root.mainloop()
