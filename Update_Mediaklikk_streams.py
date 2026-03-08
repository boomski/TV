#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import os

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


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
# echte m3u8 detecteren
# ===============================
def detect_stream(page, url):

    stream_url = [None]

    def handle_response(response):

        rurl = response.url

        if ".m3u8" in rurl and "connectmedia.hu" in rurl:

            if "index.m3u8" in rurl:

                stream_url[0] = rurl

    page.on("response", handle_response)

    try:

        page.goto(url, timeout=30000)

        page.wait_for_timeout(10000)

    except Exception as e:

        print("❌ Page load error:", e)

    page.remove_listener("response", handle_response)

    return stream_url[0]


# ===============================
# scraping
# ===============================
with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0",
        locale="en-US"
    )

    page = context.new_page()

    for line in open(CHANNEL_FILE, encoding="utf-8"):

        if "|" not in line:
            continue

        channel, url = line.strip().split("|")

        print("🔎 Scrapen:", channel)

        stream = detect_stream(page, url)

        if not stream:
            print("⚠️ Geen stream gevonden")
            stream = FALLBACK

        else:
            print("✅ Stream gevonden:", stream)

        update_playlist(channel, stream)

    browser.close()


# ===============================
# playlist opslaan
# ===============================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
