import re
import requests
from pathlib import Path

PAGE_URL = "https://www.alphacyprus.com.cy/live"
PLAYLIST_FILE = "TCL.m3u"
CHANNEL_NAME = "Alpha Cyprus"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.alphacyprus.com.cy/",
    "Origin": "https://www.alphacyprus.com.cy"
}


def get_token():

    print("🌐 Live pagina laden")

    r = requests.get(PAGE_URL, headers=HEADERS, timeout=10)

    html = r.text

    matches = re.findall(
        r"https://[a-z0-9]+\.cloudskep\.com/alphacyp/acy/[^\"]+\.m3u8\?wmsAuthSign=[^\"']+",
        html
    )

    if matches:

        print("🎯 stream gevonden")

        return matches[0]

    print("❌ geen token gevonden")

    return None


def update_playlist(stream):

    path = Path(PLAYLIST_FILE)

    if not path.exists():

        print("❌ TCL.m3u niet gevonden")
        return

    lines = path.read_text(encoding="utf-8").splitlines()

    new_lines = []
    i = 0

    while i < len(lines):

        line = lines[i]

        if line.startswith("#EXTINF") and CHANNEL_NAME in line:

            print("📺 kanaal gevonden")

            new_lines.append(line)

            new_lines.append("#EXTVLCOPT:http-referrer=https://www.alphacyprus.com.cy/")
            new_lines.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0")

            new_lines.append(stream)

            i += 1

            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            continue

        new_lines.append(line)
        i += 1

    path.write_text("\n".join(new_lines), encoding="utf-8")

    print("🎵 TCL.m3u geupdate")


def main():

    print("🚀 Alpha Cyprus API scraper")

    stream = get_token()

    if stream:

        update_playlist(stream)


if __name__ == "__main__":
    main()
