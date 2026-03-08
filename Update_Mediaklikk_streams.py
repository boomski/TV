#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import m3u8
from urllib.parse import urljoin
import time
import re

# ========================================
# Configuratie
# ========================================
CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

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
# Functie: haal m3u8 via headless Playwright
# ========================================
def get_m3u8_with_playwright(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            time.sleep(5)  # wacht op JW Player
            content = page.content()
            browser.close()

            match = re.search(r'(https?://[^"]+\.m3u8[^"]*)', content)
            if match:
                master_url = match.group(1)
                try:
                    master = m3u8.load(master_url)
                    best_stream = master_url
                    best_bw = 0
                    for p in master.playlists:
                        if p.stream_info.bandwidth > best_bw:
                            best_bw = p.stream_info.bandwidth
                            best_stream = urljoin(master_url, p.uri)
                    return best_stream
                except:
                    return master_url
            else:
                return FALLBACK
    except Exception as e:
        print("❌ Fout bij Playwright:", e)
        return FALLBACK

# ========================================
# Loop door kanalen
# ========================================
with open(CHANNEL_FILE) as f:
    for line in f:
        if "|" not in line:
            continue
        channel_name, page_url = line.strip().split("|")
        print("🔎 Scrapen:", channel_name)
        stream_url = get_m3u8_with_playwright(page_url)
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
            lines.append(f"#EXTINF:-1,{channel_name}\n")
            lines.append(stream_url + "\n")

# Schrijf playlist terug
with open(PLAYLIST_FILE, "w") as f:
    f.writelines(lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
