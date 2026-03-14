import re
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

EXTINF_LINE = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Cyprus/Alpha%20Cyprus.png",🇨🇾 | Alpha Cyprus'


def capture_stream():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        def handle_response(response):

            nonlocal stream

            if ".m3u8" in response.url and "alphacyp" in response.url:

                stream = response.url

        page.on("response", handle_response)

        try:

            page.goto(PAGE_URL, timeout=60000)

            page.wait_for_timeout(10000)

        except Exception as e:

            print("⚠️ Page error:", e)

        browser.close()

    return stream


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

        if line == EXTINF_LINE:

            new_lines.append(line)

            new_lines.append(stream)

            i += 1

            while i < len(lines) and not lines[i].startswith("#EXTINF"):

                i += 1

            continue

        new_lines.append(line)

        i += 1

    path.write_text("\n".join(new_lines), encoding="utf-8")

    print("🎵 Alpha Cyprus stream geupdate")


def main():

    print("🚀 Alpha Cyprus scraper gestart")

    stream = capture_stream()

    if stream:

        print("✅ Stream gevonden:")
        print(stream)

        update_playlist(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
