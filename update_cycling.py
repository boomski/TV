import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Bestanden
PLAYLIST_FILE = "Cycling.m3u"

# Headers voor requests
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Aantal parallelle threads
MAX_WORKERS = 10


def get_stream_url(page_url):
    """
    Haal de m3u8 of mp4 stream URL van een Mail.ru video pagina
    """
    try:
        html = requests.get(page_url, headers=HEADERS, timeout=10).text

        m3u8_match = re.search(r'https?://[^"]+\.m3u8[^"]*', html)
        if m3u8_match:
            return m3u8_match.group(0)

        mp4_match = re.search(r'https?://[^"]+\.mp4[^"]*', html)
        if mp4_match:
            return mp4_match.group(0)

        return None

    except Exception as e:
        print(f"❌ Fout bij {page_url}: {e}")
        return None


def update_playlist():
    """
    Update de playlist door alleen de URL onder elke #SOURCE te vervangen
    """
    # Lees bestaande playlist
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    # Verzamel alle #SOURCE regels
    sources = []
    for i, line in enumerate(lines):
        if line.startswith("#SOURCE:"):
            url = line.replace("#SOURCE:", "").strip()
            sources.append((i, url))

    print(f"🚀 {len(sources)} streams parallel ophalen...")

    # Parallel ophalen
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(get_stream_url, url): (index, url)
            for index, url in sources
        }

        for future in as_completed(future_map):
            index, url = future_map[future]
            stream = future.result()

            if stream:
                print(f"✅ {url}")
            else:
                print(f"⚠️ {url} - geen stream gevonden")

            results[index] = stream

    # Update playlist lines
    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("#SOURCE:"):
            updated_lines.append(line)
            # skip oude stream lijn
            if i + 1 < len(lines):
                i += 1

            new_stream = results.get(i - 1)
            if new_stream:
                updated_lines.append(new_stream)
            else:
                updated_lines.append("ERROR_NO_STREAM")
        else:
            updated_lines.append(line)

        i += 1

    # Schrijf playlist terug
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print("\n🎉 Playlist succesvol geüpdatet!")


if __name__ == "__main__":
    update_playlist()
