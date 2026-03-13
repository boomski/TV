#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# --- Config ---
CHANNELS_FILE = "Aftermind_Channels.txt"  # Elke regel: EXTINF|PAGE_URL
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

def load_channels(file_path):
    """Laad kanalen uit bestand."""
    channels = []
    if not os.path.exists(file_path):
        print(f"⚠️ Kanalenbestand {file_path} niet gevonden")
        return channels
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "|" in line:
                extinf, url = line.split("|", 1)
                channels.append({"extinf": extinf.strip(), "url": url.strip()})
    return channels

def scrape_channel(page, channel):
    """Scrape de echte m3u8 URL van een kanaal."""
    try:
        page.goto(channel["url"], wait_until="domcontentloaded", timeout=30000)
        # --- STRIKTE REGEX: enkel .m3u8 URL met token ---
        m3u8_links = page.eval_on_selector_all(
            "script",
            """
            elements => elements
                .map(e => {
                    const match = e.innerText.match(/https?:\/\/[^\\s'"]+\\.m3u8(\\?token=[^\\s'"]+)?/);
                    return match ? match[0] : null;
                })
                .filter(Boolean)
            """
        )
        if m3u8_links:
            return m3u8_links[0]
        else:
            return None
    except Exception as e:
        print(f"❌ Page error: {e}")
        return None

def update_playlist(channels, playlist_file):
    """Update TCL.m3u met de nieuwste streams."""
    playlist_lines = []
    # Laad bestaande playlist als fallback
    if os.path.exists(playlist_file):
        with open(playlist_file, "r", encoding="utf-8") as f:
            playlist_lines = f.readlines()

    # Nieuwe playlist content
    new_lines = []
    for ch in channels:
        extinf_line = ch["extinf"]
        url = ch.get("stream", FALLBACK)
        # Kijk of kanaal al in playlist staat, vervang URL
        replaced = False
        for i, line in enumerate(playlist_lines):
            if line.strip() == extinf_line:
                playlist_lines[i+1] = url + "\n"
                replaced = True
                break
        if not replaced:
            new_lines.append(extinf_line + "\n")
            new_lines.append(url + "\n")

    # Schrijf playlist
    with open(playlist_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        # Eerst bestaande met updates
        f.writelines(playlist_lines)
        # Dan nieuwe kanalen
        f.writelines(new_lines)

    print(f"🎵 Playlist succesvol bijgewerkt: {playlist_file}")

def main():
    print("🚀 Aftermind auto scraper gestart")
    channels = load_channels(CHANNELS_FILE)
    if not channels:
        print("⚠️ Geen kanalen gevonden in kanalenbestand.")
        return

    print(f"📺 Kanalen: {len(channels)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for ch in channels:
            print(f"🔎 Scrapen: {ch['extinf']}")
            stream = scrape_channel(page, ch)
            if stream:
                ch["stream"] = stream
                print(f"✅ Stream gevonden: {stream}")
            else:
                ch["stream"] = FALLBACK
                print(f"⚠️ fallback gebruikt: {FALLBACK}")
        browser.close()

    update_playlist(channels, PLAYLIST_FILE)

if __name__ == "__main__":
    main()
