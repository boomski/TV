#!/usr/bin/env python3

import requests
import re
import m3u8
from urllib.parse import urljoin

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ===============================
# Playlist laden
# ===============================
with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
    playlist_lines = f.readlines()


def update_playlist(channel, stream):
    found = False
    for i, line in enumerate(playlist_lines):
        if channel in line:
            if i + 1 < len(playlist_lines):
                playlist_lines[i + 1] = stream + "\n"
            found = True
            break
    if not found:
        playlist_lines.append(f"#EXTINF:-1,{channel}\n")
        playlist_lines.append(stream + "\n")


# ===============================
# Beste kwaliteit kiezen
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
                best = urljoin(master_url, p.uri)
        return best
    except:
        return master_url


# ===============================
# Scraper pro
# ===============================
with open(CHANNEL_FILE, encoding="utf-8") as f:

    for line in f:
        if "|" not in line:
            continue

        channel, page_url = line.strip().split("|")
        print("🔎 Scrapen:", channel)

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(page_url, headers=headers, timeout=20)
            html = r.text

            # JW Player config vinden
            match = re.search(r'jwplayer\("player"\)\.setup\((\{.*?\})\);', html, re.DOTALL)
            if not match:
                print("⚠️ JW Player config niet gevonden, fallback gebruikt")
                stream_url = FALLBACK
            else:
                config_text = match.group(1)
                # zoek naar file URL (meestal .m3u8)
                m3u8_match = re.search(r'"file"\s*:\s*"([^"]+\.m3u8[^"]*)"', config_text)
                if m3u8_match:
                    stream_url = m3u8_match.group(1)
                else:
                    print("⚠️ Geen m3u8 in config, fallback gebruikt")
                    stream_url = FALLBACK

        except Exception as e:
            print("❌ Fout bij ophalen:", e)
            stream_url = FALLBACK

        best_stream = get_best_stream(stream_url)
        print("✅ Stream gevonden:", best_stream)
        update_playlist(channel, best_stream)


# ===============================
# Playlist opslaan
# ===============================
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print("\n🎵 Playlist succesvol bijgewerkt:", PLAYLIST_FILE)
