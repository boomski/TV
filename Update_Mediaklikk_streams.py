#!/usr/bin/env python3
import requests
import re
import m3u8
from urllib.parse import urljoin
import os

# ========================================
# Configuratie
# ========================================
CHANNEL_FILE = "mediaklikk_channels.txt"  # kanaalnaam|webpagina
PLAYLIST_FILE = "TCL.m3u"                 # bestaande playlist in hoofdmap
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ========================================
# Functie: haal hoogste kwaliteit M3U8 stream van een MediaKlikk kanaal
# ========================================
def get_best_stream(page_url):
    try:
        html = requests.get(page_url, headers=HEADERS, timeout=10).text
        match = re.search(r'video\s*:\s*"([^"]+)"', html)
        if not match:
            print("⚠️ Video ID niet gevonden op pagina, fallback wordt gebruikt")
            return FALLBACK
        video_id = match.group(1)

        # Haal player API op
        player_api = f"https://player.mediaklikk.hu/playernew/player.php?video={video_id}"
        player_html = requests.get(player_api, headers=HEADERS, timeout=10).text

        # Zoek M3U8 URL
        m3u8_match = re.search(r'(https?://[^"]+\.m3u8[^"]*)', player_html)
        if not m3u8_match:
            print("⚠️ Geen M3U8 gevonden in player, fallback wordt gebruikt")
            return FALLBACK

        master_url = m3u8_match.group(1)

        # Kies hoogste kwaliteit
        try:
            master = m3u8.load(master_url)
            best_bw = 0
            best_stream = master_url
            for p in master.playlists:
                if p.stream_info.bandwidth > best_bw:
                    best_bw = p.stream_info.bandwidth
                    best_stream = urljoin(master_url, p.uri)
            return best_stream
        except:
            # Als master playlist niet geladen kan worden, gebruik master URL zelf
            return master_url

    except Exception as e:
        print("❌ Fout bij ophalen stream:", e)
        return FALLBACK

# ========================================
# Lees bestaande playlist
# ========================================
try:
    with open(PLAYLIST_FILE, "r") as f:
        lines = f.readlines()
except FileNotFoundError:
    print("❌ Playlist TCL.m3u bestaat niet. Maak eerst een playlist met kanaalnamen.")
    exit()

# ========================================
# Loop door alle kanalen in mediaklikk_channels.txt
# ========================================
with open(CHANNEL_FILE) as f:
    for line in f:
        if "|" not in line:
            continue
        channel_name, page_url = line.strip().split("|")
        print("🔎 Scrapen:", channel_name)

        stream_url = get_best_stream(page_url)
        print("✅ Stream gevonden:", stream_url)

        # Zoek kanaal in playlist en vervang URL
        found = False
        for i, l in enumerate(lines):
            if channel_name in l:
                if i + 1 < len(lines):
                    lines[i + 1] = stream_url + "\n"
                else:
                    lines.append(stream_url + "\n")
                found = True
                break

        # Kanaal toevoegen als nog niet aanwezig
        if not found:
            print(f"⚠️ Kanaal {channel_name} niet gevonden in playlist, toevoegen")
            lines.append(f"#EXTINF:-1,{channel_name}\n")
            lines.append(stream_url + "\n")

# ========================================
# Schrijf playlist terug
# ========================================
with open(PLAYLIST_FILE, "w") as f:
    f.writelines(lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
