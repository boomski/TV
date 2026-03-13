import requests
import re
import os

CHANNELS_FILE = "Aftermind_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

print("🚀 Aftermind scraper gestart")

# Lees kanalen
channels = []
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "|" in line:
                extinf, url = line.rsplit("|", 1)
                channels.append((extinf, url))
else:
    print(f"⚠️ Kanalenbestand {CHANNELS_FILE} niet gevonden")

print(f"📺 Kanalen: {len(channels)}")

# Laad bestaande playlist of maak nieuw
playlist_lines = []
if os.path.exists(PLAYLIST_FILE):
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist_lines = f.readlines()

# Functie om stream URL te scrapen
def get_stream(page_url):
    try:
        r = requests.get(page_url, timeout=15)
        r.raise_for_status()
        # Zoek m3u8 met token
        match = re.search(r'(https?://[^"]+index\.m3u8\?token=[^"&]+)', r.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"⚠️ Fout bij scrapen {page_url}: {e}")
    return FALLBACK

# Update playlist
for extinf, page_url in channels:
    print(f"🔎 Scrapen: {extinf}")
    stream_url = get_stream(page_url)
    if not stream_url:
        print(f"⚠️ fallback gebruikt voor {extinf}")
        stream_url = FALLBACK
    # Vervang bestaande entry in playlist
    updated = False
    for i, line in enumerate(playlist_lines):
        if extinf in line:
            # De regel onder EXTINF vervangen
            if i + 1 < len(playlist_lines):
                playlist_lines[i+1] = stream_url + "\n"
            else:
                playlist_lines.append(stream_url + "\n")
            updated = True
            break
    if not updated:
        playlist_lines.append(extinf + "\n")
        playlist_lines.append(stream_url + "\n")
    print(f"🔄 geupdate: {extinf}")

# Schrijf playlist terug
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.writelines(playlist_lines)

print(f"🎵 {PLAYLIST_FILE} opgeslagen")
