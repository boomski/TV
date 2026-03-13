#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "Aftermind_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    if not os.path.exists(CHANNEL_FILE):
        print("⚠️ Aftermind_Channels.txt niet gevonden")
        return channels

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line or "|" not in line:
                continue

            extinf, page_url = line.rsplit("|", 1)

            channels.append({
                "extinf": extinf.strip(),
                "url": page_url.strip()
            })

    return channels


def scrape_stream(page, url):

    try:

        page.goto(url, timeout=30000, wait_until="domcontentloaded")

        html = page.content()

        match = re.search(r'https?:\/\/[^\s\'"]+\.m3u8(\?token=[^\s\'"]+)?', html)

        if match:
            return match.group(0)

        return None

    except Exception as e:

        print("❌ Page error:", e)

        return None


def update_playlist(streams):

    lines = []

    if os.path.exists(PLAYLIST_FILE):

        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    new_lines = []

    skip = False

    for line in lines:

        if skip:
            skip = False
            continue

        found = False

        for extinf in streams.keys():

            if line.startswith(extinf):

                found = True
                skip = True
                break

        if not found:
            new_lines.append(line)

    for extinf, data in streams.items():

        stream_url = data["stream"]
        referer = data["referer"]

        new_lines.append(extinf)
        new_lines.append(f"#EXTVLCOPT:http-referrer={referer}")
        new_lines.append(stream_url)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

        f.write("\n".join(new_lines))

    print("🎵 TCL.m3u opgeslagen")


def main():

    print("🚀 Aftermind scraper gestart")

    channels = read_channels()

    print("📺 Kanalen:", len(channels))

    if not channels:
        return

    streams = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        for ch in channels:

            extinf = ch["extinf"]
            url = ch["url"]

            print("\n🔎 Scrapen:", extinf)

            stream = scrape_stream(page, url)

            if stream:

                print("✅ Stream gevonden:", stream)

                streams[extinf] = {
                    "stream": stream,
                    "referer": url
                }

            else:

                print("⚠️ fallback gebruikt")

                streams[extinf] = {
                    "stream": FALLBACK,
                    "referer": url
                }

        browser.close()

    update_playlist(streams)


if __name__ == "__main__":
    main()
