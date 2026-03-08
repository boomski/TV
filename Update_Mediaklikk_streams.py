#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import m3u8
from urllib.parse import urljoin, unquote, parse_qs, urlparse

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# kanaal ID mapping
CHANNEL_IDS = {
    "M1": "301",
    "M2": "302",
    "Duna": "303",
    "M4 Sport": "304",
    "M5": "305",
    "Duna World": "306"
}


# ================================
# beste kwaliteit kiezen
# ================================
def get_best_stream(master_url):

    try:
        master = m3u8.load(master_url)

        best = master_url
        best_bw = 0

        for p in master.playlists:

            bw = p.stream_info.bandwidth

            if bw > best_bw:
                best_bw = bw
                best = urljoin(master_url, p.uri)

        return best

    except:
        return master_url


# ================================
# playlist laden
# ================================
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


# ================================
# stream extract
# ================================
def extract_stream(url):

    if "jwpltx.com" in url:

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        if "mu" in params:
            return unquote(params["mu"][0])

    if "connectmedia.hu" in url and ".m3u8" in url:
        return url

    return None


# ================================
# scraper
# ================================
with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for line in open(CHANNEL_FILE, encoding="utf-8"):

        if "|" not in line:
            continue

        channel, url = line.strip().split("|")

        print("🔎 Scrapen:", channel)

        streams = []

        def handle_response(response):

            stream = extract_stream(response.url)

            if stream:
                streams.append(stream)

        page.on("response", handle_response)

        try:

            page.goto(url, timeout=30000)
            page.wait_for_timeout(7000)

        except Exception as e:

            print("❌ Pagina fout:", e)

        page.remove_listener("response", handle_response)

        # juiste stream kiezen
        stream_url = None
        channel_id = CHANNEL_IDS.get(channel)

        if channel_id:

            for s in streams:
                if f"{channel_id}-" in s:
                    stream_url = s
                    break

        if not stream_url and streams:
            stream_url = streams[-1]

        if not stream_url:
            stream_url = FALLBACK

        best = get_best_stream(stream_url)

        print("✅ Stream gevonden:", best)

        update_playlist(channel, best)

    browser.close()


# ================================
# playlist opslaan
# ================================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
