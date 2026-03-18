import subprocess

PLAYLIST = "TCL.m3u"
CHANNEL_FILE = "twitch_Kanalenlijst.txt"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():
    channels = []

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue

            parts = line.split("|")
            extinf = "|".join(parts[:-1]).strip()
            url = parts[-1].strip()

            channels.append({
                "extinf": extinf,
                "url": url
            })

    return channels


def get_best_stream(url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-f", "best", "-g", url],
            capture_output=True,
            text=True,
            timeout=20
        )

        streams = result.stdout.strip().split("\n")

        for s in streams:
            if ".m3u8" in s:
                return s

    except Exception as e:
        print("⚠️ Fout:", e)

    return FALLBACK


def update_playlist(channels):
    with open(PLAYLIST, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # check of dit een twitch kanaal is
        ch = next((c for c in channels if c["extinf"] == line), None)

        if ch:
            print(f"\n🔎 Scrapen: {ch['url']}")

            stream = get_best_stream(ch["url"])

            print(f"✅ Stream gevonden")

            # skip oude regels
            i += 1
            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            # nieuwe stream toevoegen
            new_lines.append(stream)
            continue

        i += 1

    # ontbrekende kanalen toevoegen
    existing = [l for l in new_lines if l.startswith("#EXTINF")]

    for ch in channels:
        if ch["extinf"] not in existing:
            print(f"➕ Toevoegen: {ch['extinf']}")

            stream = get_best_stream(ch["url"])

            new_lines.append("")
            new_lines.append(ch["extinf"])
            new_lines.append(stream)

    with open(PLAYLIST, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    print("\n🎵 Playlist volledig geüpdatet")


def main():
    print("🚀 Twitch multi scraper gestart")

    channels = read_channels()
    print(f"📺 Kanalen: {len(channels)}")

    update_playlist(channels)


if __name__ == "__main__":
    main()
