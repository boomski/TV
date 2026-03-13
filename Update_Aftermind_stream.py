#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# Bestand met kanalen
CHANNEL_FILE = "Aftermind_Channels.txt"
# Output playlist
PLAYLIST_FILE = "TCL.m3u"
# Fallback stream
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

def read_channels():
    channels = []
    if not os.path.exists(CHANNEL_FILE):
        print(f"⚠️ {CHANNEL_FILE} niet gevonden")
        return channels
    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                # Verwachte formaat: EXTINF|page_url
                if "|" in line:
                    extinf, page_url = line.split("|", 1)
                    channels.append({"extinf": extinf.strip(), "url": page_url.strip()})
    return channels

def scrape_streams(channels):
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for ch in channels:
            extinf = ch["extinf"]
            url = ch["url"]
            print(f"🔎 Scrapen: {extinf}")
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                # Extract m3u8 via regex in scripts
                links = page.eval_on_selector_all(
                    "script",
                    r"""
                    elements => elements
                        .map(e => {
                            const match = e.innerText.match(/https?:\/\/[^\s'"]+\.m3u8(\?token=[^\s'"]+)?/);
                            return match ? match[0] : null;
                        })
                        .filter(Boolean)
                    """
                )
                if links:
                    stream_url = links[0]
                    print(f"✅ Stream gevonden: {stream_url}")
                    results[extinf] = stream_url
                else:
                    print(f"⚠️ fallback gebruikt")
                    results[extinf] = FALLBACK
            except Exception as e:
                print(f"❌ Page error: {e}")
                print(f"⚠️ fallback gebruikt")
                results[extinf] = FALLBACK
        browser.close()
    return results

def update_playlist(streams):
    # Laad bestaande playlist (of maak nieuw)
    playlist_lines = []
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            playlist_lines = f.read().splitlines()
    new_lines = []
    for line in playlist_lines:
        # Bewaar alles behalve oude stream links voor onze kanalen
        keep = True
        for extinf in streams.keys():
            if line.startswith(extinf):
                keep = False
                break
        if keep:
            new_lines.append(line)
    # Voeg of update streams
    for extinf, url in streams.items():
        new_lines.append(extinf)
        new_lines.append(url)
    # Schrijf terug
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print(f"🎵 {PLAYLIST_FILE} opgeslagen")

def main():
    print("🚀 Aftermind scraper gestart")
    channels = read_channels()
    print(f"📺 Kanalen: {len(channels)}")
    if not channels:
        update_playlist({})
        return
    streams = scrape_streams(channels)
    update_playlist(streams)

if __name__ == "__main__":
    main()
