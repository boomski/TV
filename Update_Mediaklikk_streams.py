#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import m3u8
from urllib.parse import urljoin

# ========================================
# Configuratie
# ========================================
PAGE_URL = "PLAATS_HIER_DE_WEBPAGINA"   # vul hier de pagina van het kanaal in
PLAYLIST_FILE = "TCL.m3u"               # bestaande playlist in hoofdmap
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# ========================================
# Webpagina ophalen
# ========================================
try:
    r = requests.get(PAGE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    r.raise_for_status()
    html = r.text
except Exception as e:
    print("❌ Kan pagina niet ophalen:", e)
    html = ""

# ========================================
# Zoek master M3U8 URL in scripts
# ========================================
m3u8_url = None
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
for script in soup.find_all("script"):
    if ".m3u8" in script.text:
        start = script.text.find("http")
        end = script.text.find(".m3u8") + 5
        m3u8_url = script.text[start:end]
        break

if not m3u8_url:
    print("⚠️ Geen M3U8 gevonden, fallback wordt gebruikt")
    m3u8_url = FALLBACK
else:
    print("🎬 Master playlist:", m3u8_url)

# ========================================
# Master playlist laden en hoogste kwaliteit kiezen
# ========================================
best_stream = m3u8_url  # fallback als geen master playlist
try:
    master = m3u8.load(m3u8_url)
    best_bw = 0
    for p in master.playlists:
        if p.stream_info.bandwidth > best_bw:
            best_bw = p.stream_info.bandwidth
            best_stream = urljoin(m3u8_url, p.uri)
    print("✅ Beste stream gekozen:", best_stream)
except Exception as e:
    print("⚠️ Fout bij laden master playlist:", e)
    print("Fallback URL wordt gebruikt:", FALLBACK)
    best_stream = FALLBACK

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
# Kanaalnaam in playlist vinden en URL vervangen
# ========================================
channel_name = "Auto Stream"  # pas hier aan naar het juiste kanaal zoals in EXTINF
found = False
for i, line in enumerate(lines):
    if channel_name in line:
        if i + 1 < len(lines):
            lines[i + 1] = best_stream + "\n"
        else:
            lines.append(best_stream + "\n")
        found = True
        break

if not found:
    print(f"⚠️ Kanaal {channel_name} niet gevonden in playlist, toevoegen")
    lines.append(f"#EXTINF:-1,{channel_name}\n")
    lines.append(best_stream + "\n")

# ========================================
# Playlist terugschrijven
# ========================================
with open(PLAYLIST_FILE, "w") as f:
    f.writelines(lines)

print("🎵 Playlist bijgewerkt:", PLAYLIST_FILE)
