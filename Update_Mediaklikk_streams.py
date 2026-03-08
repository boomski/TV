#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
from urllib.parse import unquote, parse_qs, urlparse
import os
import requests

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ===============================
# publieke IP ophalen
# ===============================
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=10).text.strip()
    except:
        return "127.0.0.1"


PUBLIC_IP = get_public_ip()


# ===============================
# master playlist + token
# ===============================
def build_stream(url):

    if "connectmedia.hu" not in url:
        return url

    parts = url.split("/")
    parts[-1] = "index.m3u8"

    base = "/".join(parts)

    return f"{base}?v=5iip:{PUBLIC_IP}"


# ===============================
# playlist laden
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
# JWPlayer mu extractor
# ===============================
def extract_mu(url):

    if "jwpltx.com" not in url:
        return None

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if "mu" not in params:
        return None

    stream = unquote(params["mu"][0])

    if ".m3u8" in stream:
        return stream

    return None


# ===============================
# scraping
# ===============================
with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for line in open(CHANNEL_FILE, encoding="utf-8"):

        if "|" not in line:
            continue

        channel, url = line.strip().split("|")

        print("🔎 Scrapen:", channel)

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
            page.wait_for_timeout(8000)
        except Exception as e:
            print("❌ Pagina fout:", e)

        page.remove_listener("response", handle_response)

        if not stream_url[0]:
            stream_url[0] = FALLBACK

        final_stream = build_stream(stream_url[0])

        print("✅ Stream gevonden:", final_stream)

        update_playlist(channel, final_stream)

    browser.close()


# ===============================
# playlist opslaan
# ===============================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
