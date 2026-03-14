#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests

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


def get_player_id(html):

    patterns = [
        r'player/index\.php\?id=(\d+)',
        r'sayfa=(\d+)',
        r'id=(\d+)&mobile'
    ]

    for p in patterns:

        m = re.search(p, html)

        if m:
            return m.group(1)

    return None


def get_stream(player_id):

    player_url = f"https://canlitv.com/player/index.php?id={player_id}&mobile=0"

    try:

        r = requests.get(player_url, timeout=20)

        html = r.text

        # JWPlayer config bevat meestal playlist.m3u8
        match = re.search(
            r'https://[^"\']+\.m3u8\?hash=[a-zA-Z0-9]+',
            html
        )

        if match:
            return match.group(0)

    except Exception as e:

        print("❌ Player error:", e)

    return None


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

    for ch in channels:

        print("\n🔎 Scrapen:", ch["extinf"])

        try:

            r = requests.get(ch["url"], timeout=20)

            html = r.text

            player_id = get_player_id(html)

            if not player_id:

                print("⚠️ geen player id")

                streams[ch["extinf"]] = FALLBACK
                continue

            print("🎯 Player id:", player_id)

            stream = get_stream(player_id)

            if stream:

                print("✅ Stream gevonden:", stream)

                streams[ch["extinf"]] = stream

            else:

                print("⚠️ fallback gebruikt")

                streams[ch["extinf"]] = FALLBACK

        except Exception as e:

            print("❌ Error:", e)

            streams[ch["extinf"]] = FALLBACK

    update_playlist(channels, streams)


if __name__ == "__main__":
    main()
