import json
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://sat7plus.org/live/pars"
PLAYLIST_FILE = "TCL.m3u"
CHANNEL_NAME = "Sat7 Pars"

stream = None


def capture_stream():

    global stream

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):

            global stream

            url = response.url

            try:

                if ".json" in url:

                    data = response.json()

                    if isinstance(data, dict):

                        sources = str(data)

                        if "m3u8" in sources:

                            for part in sources.split('"'):

                                if "m3u8" in part:

                                    stream = part

                elif ".m3u8" in url and "sat7" in url:

                    stream = url

            except:
                pass

        page.on("response", handle_response)

        page.goto(PAGE_URL)
        page.wait_for_timeout(15000)

        browser.close()

    return stream


def update_playlist(stream):

    path = Path(PLAYLIST_FILE)
    lines = path.read_text().splitlines()

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

    path.write_text("\n".join(new_lines))


def main():

    print("🚀 SAT7 Pars scraper gestart")

    s = capture_stream()

    if s:

        print("✅ Stream gevonden:", s)
        update_playlist(s)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
