import re
import requests
from pathlib import Path

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def find_master_playlist():

    print("🔎 pagina laden")

    r = requests.get(PAGE_URL, headers=HEADERS, timeout=10)

    html = r.text

    matches = re.findall(
        r"https://l4\.cloudskep\.com/alphacyp/acy/playlist\.m3u8\?wmsAuthSign=[^\"']+",
        html
    )

    if matches:

        print("🎯 token gevonden")

        return matches[0]

    return None


def stream_works(url):

    try:

        r = requests.get(url, headers=HEADERS, timeout=5)

        if r.status_code == 200 and "#EXTM3U" in r.text:

            print("✅ stream werkt")

            return True

    except:

        pass

    print("❌ stream test mislukt")

    return False


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

            new_lines.append(line)
            new_lines.append(stream)

            i += 1

            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            continue

        new_lines.append(line)

        i += 1

    path.write_text("\n".join(new_lines), encoding="utf-8")

    print("🎵 playlist geupdate")


def main():

    print("🚀 Alpha Cyprus snelle scraper")

    stream = find_master_playlist()

    if not stream:

        print("❌ geen token gevonden")

        return

    if stream_works(stream):

        update_playlist(stream)


if __name__ == "__main__":
    main()
