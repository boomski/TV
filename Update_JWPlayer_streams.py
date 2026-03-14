#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests

CHANNEL_FILE = "channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    if not os.path.exists(CHANNEL_FILE):
        print("⚠️ channels.txt ontbreekt")
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


def scrape_stream(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=20)

        html = r.text

        # JWPlayer playlist.m3u8?hash
        match = re.search(r'https?:\/\/[^\s\'"]+playlist\.m3u8\?hash=[a-zA-Z0-9]+', html)

        if match:
            return match.group(0)

        # fallback gewone m3u8
        match = re.search(r'https?:\/\/[^\s\'"]+\.m3u8(\?[^\'"\s]+)?', html)

        if match:
            return match.group(0)

        return None

    except Exception as e:

        print("❌ Request error:", e)
        return None


def update_playlist(lines, channels, streams):

    i = 0

    while i < len(lines):

        line = lines[i]

        for ch in channels:

            if line.startswith(ch["extinf"]):

                stream = streams.get(ch["extinf"])

                if stream:

                    print("🔄 Update:", ch["extinf"])

                    lines[i] = ch["extinf"]
                    lines[i+1] = stream

                i += 2
                break

        else:
            i += 1

    return lines


def main():

    print("🚀 JWPlayer scraper gestart")

    channels = read_channels()

    print("📺 Kanalen:", len(channels))

    streams = {}

    for ch in channels:

        print("\n🔎 Scrapen:", ch["extinf"])

        stream = scrape_stream(ch["url"])

        if stream:

            print("✅ Stream gevonden:", stream)
            streams[ch["extinf"]] = stream

        else:

            print("⚠️ fallback gebruikt")
            streams[ch["extinf"]] = FALLBACK

    lines = []

    if os.path.exists(PLAYLIST_FILE):

        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    lines = update_playlist(lines, channels, streams)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

        f.write("\n".join(lines))

    print("🎵 TCL.m3u opgeslagen")


if __name__ == "__main__":
    main()
