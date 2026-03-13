#!/usr/bin/env python3
import requests
import re
import os

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"
CHANNEL_FILE = "Aftermind_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

print("🚀 Aftermind scraper gestart")

# Lees kanalen
channels = []
with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Verwacht formaat: EXTINF|page_url
        if "|" not in line:
            continue
        extinf, page_url = line.split("|", 1)
        channels.append({"extinf": extinf.strip(), "page_url": page_url.strip()})

print(f"📺 Kanalen: {len(channels)}")

# Lees huidige playlist
if os.path.exists(PLAYLIST_FILE):
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist_lines = f.readlines()
else:
    playlist_lines = ["#EXTM3U\n"]

# Functie om een kanaal te updaten
def update_playlist(extinf, stream_url):
    updated = False
    for i, line in enumerate(playlist_lines):
        if extinf in line:
            # Vervang volgende regel (de URL) door de nieuwe
            if i + 1 < len(playlist_lines):
                playlist_lines[i + 1] = stream_url + "\n"
                updated = True
            break
    if not updated:
        # Voeg kanaal toe onderaan
        if not playlist_lines[-1].endswith("\n"):
            playlist_lines.append("\n")
        playlist_lines.append(extinf + "\n")
        playlist_lines.append(stream_url + "\n")
    return updated

# Loop door kanalen
for ch in channels:
    extinf = ch["extinf"]
    url = ch["page_url"]

    print(f"\n🔎 Scrapen: {extinf}")

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        # Zoek m3u8 in de pagina
        m3u8_match = re.search(r'(https?://[^\s"\'<>]+\.m3u8\?token=[^"\s<>]+)', r.text)
        if m3u8_match:
            stream_url = m3u8_match.group(1)
            print(f"✅ Stream gevonden: {stream_url}")
        else:
            stream_url = FALLBACK
            print(f"⚠️ geen stream gevonden, fallback wordt gebruikt")
    except Exception as e:
        stream_url = FALLBACK
        print(f"❌ Page error: {e}, fallback gebruikt")

    updated = update_playlist(extinf, stream_url)
    if updated:
        print(f"🔄 geupdate: {extinf}")

# Sla playlist op
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 TCL.m3u opgeslagen")
