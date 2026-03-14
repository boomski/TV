#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    if not os.path.exists(CHANNEL_FILE):
        print("⚠️ JWPlayer_Channels.txt ontbreekt")
        return channels

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line or "|" not in line:
                continue

            extinf, url = line.rsplit("|", 1)

            channels.append({
                "extinf": extinf.strip(),
                "url": url.strip()
            })

    return channels


def capture_stream(page, url):

    stream = None

    def handle_response(response):

        nonlocal stream

        if ".m3u8" in response.url:
            stream = response.url

    page.on("response", handle_response)

    try:

        page.goto(url, timeout=45000)

        # langer wachten zodat JWPlayer start
        page.wait_for_timeout(12000)

    except Exception as e:

        print("❌ Page error:", e)

    page.remove_listener("response", handle_response)

    return stream


def update_playlist(channels, streams):

    if not os.path.exists(PLAYLIST_FILE):
        print("⚠️ TCL.m3u ontbreekt")
        return

    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    i = 0

    while i < len(lines):

        line = lines[i]

        for ch in channels:

            if line.startswith(ch["extinf"]):

                stream = streams.get(ch["extinf"])

                if stream:

                    print("🔄 Update:", ch["extinf"])

                    if i + 1 < len(lines):
                        lines[i+1] = stream
                    else:
                        lines.append(stream)

                i += 2
                break

        else:
            i += 1

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("🎵 TCL.m3u opgeslagen")


def main():

    print("🚀 JWPlayer scraper gestart")

    channels = read_channels()

    print("📺 Kanalen:", len(channels))

    streams = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        for ch in channels:

            print("\n🔎 Scrapen:", ch["extinf"])

            stream = capture_stream(page, ch["url"])

            if stream:

                print("✅ Stream:", stream)

                streams[ch["extinf"]] = stream

            else:

                print("⚠️ fallback gebruikt")

                streams[ch["extinf"]] = FALLBACK

        browser.close()

    update_playlist(channels, streams)


if __name__ == "__main__":
    main()
