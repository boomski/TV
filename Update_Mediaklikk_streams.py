import requests
import re

CHANNEL_FILE = "mediaklikk_channels.txt"
PLAYLIST = "playlists/TCL.m3u"

headers = {
    "User-Agent": "Mozilla/5.0"
}

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

def get_stream(page_url):
    try:
        html = requests.get(page_url, headers=headers, timeout=10).text
        match = re.search(r'video\s*:\s*"([^"]+)"', html)
        if not match:
            return None
        video_id = match.group(1)
        player_api = f"https://player.mediaklikk.hu/playernew/player.php?video={video_id}"
        player_html = requests.get(player_api, headers=headers, timeout=10).text
        m3u8 = re.search(r'(https?://[^"]+\.m3u8[^"]*)', player_html)
        if m3u8:
            return m3u8.group(1)
        return None
    except:
        return None

# Lees huidige playlist of maak nieuwe
try:
    with open(PLAYLIST, "r") as f:
        lines = f.readlines()
except:
    lines = ["#EXTM3U\n"]

with open(CHANNEL_FILE) as f:
    for line in f:
        if "|" not in line:
            continue
        name, page = line.strip().split("|")
        print("Scrapen:", name)
        stream = get_stream(page)
        if not stream:
            print("⚠️ fallback gebruikt voor", name)
            stream = FALLBACK

        # Vervang bestaande regel of voeg toe
        found = False
        for i, l in enumerate(lines):
            if name in l:
                if i+1 < len(lines):
                    lines[i+1] = stream + "\n"
                else:
                    lines.append(stream + "\n")
                found = True
                break
        if not found:
            lines.append(f"#EXTINF:-1,{name}\n")
            lines.append(stream + "\n")

# Schrijf playlist
with open(PLAYLIST, "w") as f:
    f.writelines(lines)

print("✅ Playlist bijgewerkt:", PLAYLIST)
