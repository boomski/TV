#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "Aftermind_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

INSERT_BEFORE = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Turkije/Tivibu%20Spor.jpg",🇹🇷 | Tivibu Spor 1'

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

            extinf, url = line.rsplit("|", 1)

            channels.append({
                "extinf": extinf.strip(),
                "url": url.strip()
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


def clean_old_streams(lines, channels):

    cleaned = []

    i = 0

    while i < len(lines):

        line = lines[i]

        remove = False

        for ch in channels:

            if line.startswith(ch["extinf"]):

                remove = True
                i += 3
                break

        if not remove:

            cleaned.append(line)
            i += 1

    return cleaned


def insert_streams(lines, streams):

    new_lines = []

    inserted = False

    for line in lines:

        if not inserted and line.startswith(INSERT_BEFORE):

            for extinf, data in streams.items():

                new_lines.append(extinf)
                new_lines.append(f"#EXTVLCOPT:http-referrer={data['referer']}")
                new_lines.append(data["stream"])

            inserted = True

        new_lines.append(line)

    return new_lines


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

    lines = []

    if os.path.exists(PLAYLIST_FILE):

        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    lines = clean_old_streams(lines, channels)

    lines = insert_streams(lines, streams)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

        f.write("\n".join(lines))

    print("🎵 TCL.m3u opgeslagen")


if __name__ == "__main__":
    main()
