#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import m3u8
from urllib.parse import urljoin

# ========================================
# Configuratie
# ========================================
CHANNEL_FILE = "mediaklikk_channels.txt"  # KanaalNaam|WebpaginaURL
PLAYLIST_FILE = "TCL.m3u"                 # Bestaande playlist in hoofdmap
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ========================================
# Functie: zoek automatisch player.php URL op pagina
# ========================================
def find_player_url(page_url):
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # 1️⃣ Kijk naar iframes
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "player.php" in src:
                return src

        # 2️⃣ Kijk naar scripts die player.php bevatten
        for script in soup.find_all("script"):
            if "player.php" in script.text:
                match = re.search(r'(https?://[^"\']*player\.php[^"\']*)', script.text)
                if match:
                    return match.group(1)

    except Exception as e:
        print("❌ Fout bij zoeken player URL:", e)

    return None

# ========================================
# Functie: haal hoogste kwaliteit M3U8 stream
# ========================================
def get_best_stream(player_url):
    if not player_url:
        return FALLBACK
    try:
        html = requests.get(player_url, headers=HEADERS, timeout=10).text
        m3u8_match = re.search(r'(https?://[^"]+\.m3u8[^"]*)', html)
        if not m3u8_match:
            return FALLBACK

        master_url = m3u8_match.group(1)
        master = m3u8.load(master_url)
        best_stream = master_url
        best_bw = 0
        for p in master.playlists:
            if p.stream_info.bandwidth > best_bw:
                best_bw = p.stream_info.bandwidth
                best_stream = urljoin(master_url, p.uri)
        return best_stream
    except Exception as e:
        print("❌ Fout bij ophalen M3U8:", e)
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

        # Zoek player.php automatisch
        player_url = find_player_url(page_url)
        if not player_url:
            print("⚠️ Geen player gevonden, fallback wordt gebruikt")
        else:
            print("🎬 Player URL gevonden:", player_url)

        # Haal beste stream
        stream_url = get_best_stream(player_url)
        print("✅ Stream gevonden:", stream_url)

        # Update playlist
        found = False
        for i, l in enumerate(lines):
            if channel_name in l:
                if i + 1 < len(lines):
                    lines[i + 1] = stream_url + "\n"
                else:
                    lines.append(stream_url + "\n")
                found = True
                break

        if not found:
            print(f"⚠️ Kanaal {channel_name} niet gevonden in playlist, toevoegen")
            lines.append(f"#EXTINF:-1,{channel_name}\n")
            lines.append(stream_url + "\n")

# ========================================
# Playlist terugschrijven
# ========================================
with open(PLAYLIST_FILE, "w") as f:
    f.writelines(lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
