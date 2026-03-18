import subprocess

PLAYLIST = "TCL.m3u"

CHANNELS = {
    '#EXTINF:-1 tvg-logo="logo.png",🇺🇸 | ABC News Live': "https://www.twitch.tv/abcnewsal",
}

FALLBACK = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"


def get_best_stream(url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-f", "best", "-g", url],
            capture_output=True,
            text=True,
            timeout=20
        )

        streams = result.stdout.strip().split("\n")

        # meestal eerste = beste kwaliteit
        for s in streams:
            if ".m3u8" in s:
                return s

    except Exception as e:
        print("⚠️ Fout:", e)

    return FALLBACK


def update_playlist():
    with open(PLAYLIST, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        if line in CHANNELS:
            url = CHANNELS[line]

            print(f"🔎 Scrapen: {url}")

            stream = get_best_stream(url)

            print(f"✅ Beste stream gevonden")

            # skip oude regels (url + headers)
            i += 1
            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            # nieuwe stream toevoegen
            new_lines.append(stream)
            continue

        i += 1

    with open(PLAYLIST, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    print("🎵 Playlist geüpdatet met beste kwaliteit")


if __name__ == "__main__":
    update_playlist()
