#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import m3u8
from urllib.parse import urljoin

# ========================================
# Configuratie
# ========================================
CHANNEL_FILE = "mediaklikk_channels.txt"  # lijst met kanalen
PLAYLIST_FILE = "TCL.m3u"                # bestaande playlist in hoofdmap
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# ========================================
# Functie: scrape master M3U8 en hoogste kwaliteit kiezen
# ========================================
def get_best_stream(page_url):
    try:
        r = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print("❌ Kan pagina niet ophalen:", e)
        return FALLBACK

    # Zoek master M3U8 URL in <script> tags
    soup = BeautifulSoup(html, "html.parser")
    m3u8_url = None
    for script in soup.find_all("script"):
        if ".m3u8" in script.text:
            start = script.text.find("http")
            end = script.text.find(".m3u8") + 5
            m3u8_url = script.text[start:end]
            break

    if not m3u8_url:
        print("⚠️ Geen M3U8 gevonden, fallback wordt gebruikt")
        return FALLBACK

    # Master playlist laden en hoogste kwaliteit kiezen
    try:
        master = m3u8.load(m3u8_url)
        best_stream = m3u8_url  # fallback als geen substreams
        best_bw = 0
        for p in master.playlists:
            if p.stream_info.bandwidth > best_bw:
                best_bw = p.stream_info.bandwidth
                best_stream = urljoin(m3u8_url, p.uri)
        return best_stream
    except Exception as e:
        print("⚠️ Fout bij laden master playlist:", e)
        return FALLBACK

# ========================================
# Bestaande playlist inlezen
# ========================================
try:
    with open(PLAYLIST_FILE, "r") as f:
        lines = f.readlines()
except FileNotFoundError:
    print("❌ Playlist bestaat niet. Maak eerst TCL.m3u met kanaalnamen.")
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

        # Kanaal toevoegen als niet aanwezig
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
