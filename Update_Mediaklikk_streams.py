#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
from urllib.parse import unquote, parse_qs, urlparse
import os

# ===============================
# Config
# ===============================
CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ===============================
# Functie: URL naar master playlist
# ===============================
def to_master_playlist(url):
    """Zorg dat we altijd index.m3u8 krijgen"""
    if "connectmedia.hu" in url:
        parts = url.split("/")
        parts[-1] = "index.m3u8"
        return "/".join(parts)
    return url


# ===============================
# Playlist laden en bijwerken
# ===============================
if not os.path.exists(PLAYLIST_FILE):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
    playlist_lines = f.readlines()


def update_playlist(channel, stream):
    """Vervang bestaande stream in playlist, of voeg toe"""
    for i, line in enumerate(playlist_lines):
        if channel in line:
            if i + 1 < len(playlist_lines):
                playlist_lines[i + 1] = stream + "\n"
            return
    # nieuw kanaal
    playlist_lines.append(f"#EXTINF:-1,{channel}\n")
    playlist_lines.append(stream + "\n")


# ===============================
# JW Player mu-extract
# ===============================
def extract_mu(url):
    """Pak echte m3u8 van JW Player mu-parameter"""
    if "jwpltx.com" not in url:
        return None
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "mu" not in params:
        return None
    stream = unquote(params["mu"][0])
    if "index.m3u8" in stream:
        return stream
    return None


# ===============================
# Playwright scraper
# ===============================
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for line in open(CHANNEL_FILE, encoding="utf-8"):

        if "|" not in line:
            continue

        channel, url = line.strip().split("|")

        print("🔎 Scrapen:", channel)

        # ✅ Mutable container voor stream_url
        stream_url = [None]

        def handle_response(response):
            try:
                s = extract_mu(response.url)
                if s:
                    stream_url[0] = s
            except:
                pass

        page.on("response", handle_response)

        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(6000)
        except Exception as e:
            print(f"❌ Pagina fout voor {channel}: {e}")
            stream_url[0] = FALLBACK

        page.remove_listener("response", handle_response)

        # fallback als niets gevonden
        if not stream_url[0]:
            stream_url[0] = FALLBACK

        # altijd master playlist
        master = to_master_playlist(stream_url[0])
        best = master

        print("✅ Stream gevonden:", best)
        update_playlist(channel, best)

    browser.close()


# ===============================
# Playlist opslaan
# ===============================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
