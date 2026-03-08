#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import m3u8
from urllib.parse import unquote, parse_qs, urlparse
import os

# ===============================
# Config
# ===============================
CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# Mapping MediaKlikk kanaal-ID voor filteren
CHANNEL_IDS = {
    "M1": "301",
    "M2": "302",
    "Duna": "303",
    "M4 Sport": "304",
    "M5": "305",
    "Duna World": "306"
}


# ===============================
# Variant → master playlist converter
# ===============================
def to_master_playlist(url):
    if "connectmedia.hu" not in url:
        return url
    parts = url.split("/")
    parts[-1] = "index.m3u8"  # altijd master
    return "/".join(parts)


# ===============================
# Hoogste kwaliteit kiezen
# ===============================
def get_best_stream(master_url):
    try:
        master = m3u8.load(master_url)
        best = master_url
        best_bw = 0
        for p in master.playlists:
            bw = p.stream_info.bandwidth
            if bw > best_bw:
                best_bw = bw
                best = master_url.rsplit("/", 1)[0] + "/" + p.uri
        return best
    except:
        return master_url


# ===============================
# Playlist laden
# ===============================
if not os.path.exists(PLAYLIST_FILE):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
    playlist_lines = f.readlines()


def update_playlist(channel, stream):
    for i, line in enumerate(playlist_lines):
        if channel in line:
            if i + 1 < len(playlist_lines):
                playlist_lines[i + 1] = stream + "\n"
            return
    playlist_lines.append(f"#EXTINF:-1,{channel}\n")
    playlist_lines.append(stream + "\n")


# ===============================
# mu stream extract
# ===============================
def extract_mu(url):
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

        stream_url = None

        def handle_response(response):
            nonlocal stream_url
            try:
                s = extract_mu(response.url)
                if s:
                    stream_url = s
            except:
                pass

        page.on("response", handle_response)

        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(6000)
        except Exception as e:
            print(f"❌ Pagina fout voor {channel}: {e}")
            stream_url = FALLBACK

        page.remove_listener("response", handle_response)

        if not stream_url:
            stream_url = FALLBACK

        # Variant → master
        master = to_master_playlist(stream_url)
        best = get_best_stream(master)

        print("✅ Stream gevonden:", best)
        update_playlist(channel, best)

    browser.close()

# ===============================
# Playlist opslaan
# ===============================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
