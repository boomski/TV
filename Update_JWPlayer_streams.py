#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests
from pathlib import Path

# ---------- CONFIG ----------
TCL_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# Kanalen lijst (kan ook uit JWPlayer_Channels.txt gelezen worden)
CHANNELS = [
    {
        "extinf": '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Cyprus/TV2020.png",🇨🇾 | TV2020',
        "url": "https://canlitv.com/tv-2020?ulke=cy"
    },
    {
        "extinf": '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Cyprus/Okku%20TV.png",🇨🇾 | Okku TV',
        "url": "https://canlitv.com/okku-tv?ulke=cy"
    }
]

# ---------- FUNCTIES ----------

def get_jwplayer_stream(page_url):
    """
    Haal de directe .m3u8 link van JWPlayer pagina.
    """
    try:
        resp = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        # Zoek een m3u8 link in de pagina
        match = re.search(r"https?:\/\/[^\s'\"<>]+\.m3u8(\?[^\s'\"<>]+)?", resp.text)
        if match:
            return match.group(0)
        return None
    except requests.RequestException:
        return None

def write_block(extinf, referrer, stream):
    """
    Maak de m3u block met headers en fallback
    """
    block = [extinf]
    block.append(f"#EXTVLCOPT:http-referrer={referrer}")

    # Extra headers voor 'yayin' links
    if "yayin" in stream or "edge.kuzeykibrissmart" in stream or "play.kibristv" in stream:
        block.append("#EXTVLCOPT:http-origin=https://canlitv.com")
        block.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0")
        block.append("#EXTVLCOPT:http-header=Accept:*/*")

    block.append(stream if stream else FALLBACK)
    return block

def update_tcl_file(blocks):
    """
    Voeg de blocks toe boven bestaande Cyprus kanalen in TCL.m3u
    Oude links worden vervangen
    """
    tcl_path = Path(TCL_FILE)
    if tcl_path.exists():
        lines = tcl_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["#EXTM3U"]

    # Zoek positie van eerste Cyprus kanaal
    insert_idx = 1
    for i, line in enumerate(lines):
        if "Cyprus" in line:
            insert_idx = i
            break

    # Maak dict van extinf -> nieuwe stream om duplicaten te vervangen
    new_extinf_map = {b[0]: b[1:] for b in blocks}

    updated_lines = []
    skip_next = False
    for line in lines:
        if skip_next:
            # skip oude m3u8/fallback links
            if line.startswith("http") or line.startswith("#EXTVLCOPT"):
                continue
            else:
                skip_next = False
        if line in new_extinf_map:
            # overschrijven
            updated_lines.extend([line] + new_extinf_map[line])
            skip_next = True
            continue
        updated_lines.append(line)

    # Voeg nieuw blok toe als niet aanwezig
    for extinf, rest in new_extinf_map.items():
        if extinf not in lines:
            updated_lines[insert_idx:insert_idx] = [extinf] + rest

    tcl_path.write_text("\n".join(updated_lines), encoding="utf-8")
    print(f"🎵 {TCL_FILE} opgeslagen")

# ---------- MAIN ----------

def main():
    print("🚀 JWPlayer scraper gestart")
    print(f"📺 Kanalen: {len(CHANNELS)}\n")

    blocks = []
    for ch in CHANNELS:
        extinf = ch["extinf"]
        url = ch["url"]
        print(f"🔎 Scrapen: {extinf}")

        stream = get_jwplayer_stream(url)
        if not stream:
            print("⚠️ fallback gebruikt")
        blocks.append(write_block(extinf, url, stream))

    update_tcl_file(blocks)

if __name__ == "__main__":
    main()
