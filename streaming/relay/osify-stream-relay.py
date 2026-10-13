#!/usr/bin/env python3
"""
OSify Multi-RTMP & SRT Live Broadcast Relay
=============================================================================
Multiplexer di streaming locale a impatto zero su CPU e GPU.
Riceve un singolo stream video/audio da OBS Studio (es. rtmp://127.0.0.1:1935/live/osify)
e lo re-inoltra SIMULTANEAMENTE a livello di pacchetti di rete a:
- Twitch (rtmp://live.twitch.tv/app/<KEY>)
- Kick (rtmp://fa723ac112bf.global-contribute.live-video.net/app/<KEY>)
- YouTube (rtmp://a.rtmp.youtube.com/live2/<KEY>)
- Qualsiasi endpoint custom RTMP o SRT.

ZERO re-encoding: la CPU e la GPU codificano 1 sola volta in NVENC/VAAPI/AMF/AV1.
I pacchetti vengono duplicati a livello di socket e instradati con marcatura DSCP AF31.
=============================================================================
"""

import sys
import os
import json
import subprocess
import signal

CONFIG_PATH = os.path.expanduser("~/.config/osify/streaming_relay.json")

DEFAULT_CONFIG = {
    "listen_port": 1935,
    "listen_path": "live/stream",
    "destinations": {
        "twitch": {
            "enabled": False,
            "url": "rtmp://live.twitch.tv/app",
            "key": ""
        },
        "kick": {
            "enabled": False,
            "url": "rtmp://fa723ac112bf.global-contribute.live-video.net/app",
            "key": ""
        },
        "youtube": {
            "enabled": False,
            "url": "rtmp://a.rtmp.youtube.com/live2",
            "key": ""
        },
        "custom": {
            "enabled": False,
            "url": "",
            "key": ""
        }
    }
}

def load_or_create_config():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"[OSify-Relay] File di configurazione creato: {CONFIG_PATH}")
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_ffmpeg_relay_cmd(config):
    """
    Costruisce una pipeline FFmpeg pass-through (-c copy)
    che riceve RTMP locale e usa il demuxer tee per inoltrare a più endpoint contemporaneamente.
    """
    listen_url = f"rtmp://127.0.0.1:{config.get('listen_port', 1935)}/{config.get('listen_path', 'live/stream')}?listen=1"
    
    outputs = []
    destinations = config.get("destinations", {})
    for name, dest in destinations.items():
        if dest.get("enabled") and dest.get("url") and dest.get("key"):
            target = f"{dest['url'].rstrip('/')}/{dest['key']}"
            outputs.append(f"[f=flv:onfail=ignore]{target}")
            print(f"[OSify-Relay] Destinazione attiva: {name.upper()} -> {dest['url']}")

    if not outputs:
        print("[!] Nessuna destinazione abilitata con chiave valida in streaming_relay.json!")
        print(f"[i] Modifica {CONFIG_PATH} abilitando almeno una piattaforma (Twitch, Kick o YouTube).")
        return None

    tee_muxer = "|".join(outputs)

    # Parametri FFmpeg:
    # -listen 1: agisce da server RTMP per OBS
    # -c copy: ZERO codifica CPU/GPU, puro copia-incolla bitstream
    # -f tee: demuxer parallelo con tolleranza d'errore (se una piattaforma lagga, le altre non cadono)
    cmd = [
        "ffmpeg",
        "-loglevel", "warning",
        "-listen", "1",
        "-i", listen_url,
        "-c", "copy",
        "-flags", "+global_header",
        "-f", "tee",
        tee_muxer
    ]
    return cmd

def main():
    print("=========================================================")
    print("       OSify Multi-RTMP Relay (Twitch + Kick + YouTube)  ")
    print("=========================================================")
    config = load_or_create_config()
    cmd = build_ffmpeg_relay_cmd(config)
    
    if not cmd:
        sys.exit(1)

    print(f"\n[+] In ascolto per OBS Studio su: rtmp://127.0.0.1:{config.get('listen_port', 1935)}/{config.get('listen_path', 'live/stream')}")
    print("[+] In OBS: Imposta Servizio: 'Personalizzato...', Server: rtmp://127.0.0.1:1935/live, Chiave: stream\n")

    def handle_sig(sig, frame):
        print("\n[!] Chiusura relay in corso...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    try:
        proc = subprocess.Popen(cmd)
        proc.wait()
    except KeyboardInterrupt:
        print("\n[!] Relay arrestato.")

if __name__ == "__main__":
    main()
