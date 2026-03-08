#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import m3u8
from urllib.parse import urljoin

# ========================================
# Configuratie
# ========================================

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ========================================
# Playlist laden
# ========================================

try:
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist_lines = f.readlines()
except FileNotFoundError:
    print("❌ TCL.m3u niet gevonden")
    exit()


# ========================================
# Beste kwaliteit kiezen
# ========================================

def get_best_stream(master_url):

    try:

        master = m3u8.load(master_url)

        best_stream = master_url
        best_bw = 0

        for p in master.playlists:

            bw = p.stream_info.bandwidth

            if bw > best_bw:
                best_bw = bw
                best_stream = urljoin(master_url, p.uri)

        return best_stream

    except:
        return master_url


# ========================================
# Playlist updaten
# ========================================

def update_playlist(channel, stream):

    found = False

    for i, line in enumerate(playlist_lines):

        if channel in line:

            if i + 1 < len(playlist_lines):
                playlist_lines[i + 1] = stream + "\n"
            else:
                playlist_lines.append(stream + "\n")

            found = True
            break

    if not found:

        print("⚠️ Kanaal niet in playlist, toevoegen:", channel)

        playlist_lines.append(f"#EXTINF:-1,{channel}\n")
        playlist_lines.append(stream + "\n")


# ========================================
# Scraping
# ========================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    for line in open(CHANNEL_FILE, encoding="utf-8"):

        if "|" not in line:
            continue

        channel, url = line.strip().split("|")

        print("🔎 Scrapen:", channel)

        stream_url = None

        # network listener
        def handle_request(request):

            nonlocal stream_url

            if ".m3u8" in request.url and not stream_url:
                stream_url = request.url

        page.on("request", handle_request)

        try:

            page.goto(url, timeout=30000)

            page.wait_for_timeout(7000)

        except Exception as e:

            print("❌ Pagina fout:", e)

        page.remove_listener("request", handle_request)

        if stream_url:

            best = get_best_stream(stream_url)

        else:

            best = FALLBACK

        print("✅ Stream gevonden:", best)

        update_playlist(channel, best)

    browser.close()


# ========================================
# Playlist opslaan
# ========================================

with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
