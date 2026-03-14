#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
from pathlib import Path

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    i = 0

    while i < len(lines):

        line = lines[i]

        if line.startswith("#EXTINF"):

            # formaat: EXTINF|URL
            if "|" in line and line.count("|") >= 2:

                parts = line.split("|")

                extinf = "|".join(parts[:-1]).strip()
                url = parts[-1].strip()

                channels.append({
                    "extinf": extinf,
                    "url": url
                })

                i += 1
                continue

            # formaat: EXTINF + volgende regel URL
            if i + 1 < len(lines):

                extinf = line
                url = lines[i + 1]

                channels.append({
                    "extinf": extinf,
                    "url": url
                })

                i += 2
                continue

        i += 1

    return channels


def get_stream(page_url):

    try:

        r = requests.get(
            page_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        if r.status_code != 200:
            return None

        match = re.search(r"https?:\/\/[^\s\"']+\.m3u8(\?[^\s\"']+)?", r.text)

        if match:
            return match.group(0)

    except Exception:
        pass

    return None


def build_block(extinf, referrer, stream):

    if stream is None:
        stream = FALLBACK

    block = [extinf]

    block.append(f"#EXTVLCOPT:http-referrer={referrer}")

    if "yayin" in stream or "kuzeykibrissmart" in stream or "kibristv" in stream:

        block.append("#EXTVLCOPT:http-origin=https://canlitv.com")
        block.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0")
        block.append("#EXTVLCOPT:http-header=Accept:*/*")

    block.append(stream)

    return block


def update_playlist(channels):

    path = Path(PLAYLIST_FILE)

    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["#EXTM3U"]

    new_lines = []
    i = 0

    while i < len(lines):

        line = lines[i]

        ch = next((c for c in channels if c["extinf"] == line), None)

        if ch:

            print("\n🔎 Scrapen:", ch["extinf"])

            stream = get_stream(ch["url"])

            if stream:
                print("✅ Stream gevonden")
            else:
                print("⚠️ fallback gebruikt")

            block = build_block(line, ch["url"], stream)

            new_lines.extend(block)

            i += 1

            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            continue

        new_lines.append(line)
        i += 1

    existing = [l for l in new_lines if l.startswith("#EXTINF")]

    for ch in channels:

        if ch["extinf"] not in existing:

            print("\n➕ Nieuw kanaal:", ch["extinf"])

            stream = get_stream(ch["url"])

            block = build_block(ch["extinf"], ch["url"], stream)

            new_lines.append("")
            new_lines.extend(block)

    path.write_text("\n".join(new_lines), encoding="utf-8")

    print("\n🎵 TCL.m3u opgeslagen")


def main():

    print("🚀 JWPlayer scraper gestart")

    channels = read_channels()

    print("📺 Kanalen:", len(channels))

    update_playlist(channels)


if __name__ == "__main__":
    main()
