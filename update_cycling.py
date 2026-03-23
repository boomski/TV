import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

PLAYLIST_FILE = "Cycling.m3u"
MAX_WORKERS = 5  # iets lager houden (yt-dlp is zwaarder)


def get_stream_url(page_url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", page_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            url = result.stdout.strip().split("\n")[0]
            return url

        return None

    except Exception as e:
        print(f"❌ fout bij {page_url}: {e}")
        return None


def update_playlist():
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    sources = []
    for i, line in enumerate(lines):
        if line.startswith("#SOURCE:"):
            url = line.replace("#SOURCE:", "").strip()
            sources.append((i, url))

    print(f"🚀 {len(sources)} streams ophalen met yt-dlp...")

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
                print(f"⚠️ {url}")

            results[index] = stream

    updated_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("#SOURCE:"):
            updated_lines.append(line)

            if i + 1 < len(lines):
                i += 1  # skip oude URL

            new_stream = results.get(i - 1)

            if new_stream:
                updated_lines.append(new_stream)
            else:
                updated_lines.append("ERROR_NO_STREAM")

        else:
            updated_lines.append(line)

        i += 1

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print("\n🎉 Playlist geüpdatet met yt-dlp!")


if __name__ == "__main__":
    update_playlist()
