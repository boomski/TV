from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"
PLAYLIST_FILE = "TCL.m3u"
CHANNEL_NAME = "Alpha Cyprus"


def capture_stream():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):

            nonlocal stream

            url = response.url

            if (
                "playlist.m3u8" in url
                and "cloudskep.com" in url
                and "alphacyp" in url
                and "wmsAuthSign" in url
            ):

                print("🎯 master gevonden:", url)

                stream = url

        page.on("response", handle_response)

        page.goto(PAGE_URL)

        page.wait_for_timeout(10000)

        browser.close()

    return stream


def update_playlist(stream):

    path = Path(PLAYLIST_FILE)

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


def main():

    print("🚀 Alpha Cyprus master scraper gestart")

    stream = capture_stream()

    if stream:

        print("✅ Master playlist gevonden:")
        print(stream)

        update_playlist(stream)

    else:

        print("❌ Geen master playlist gevonden")


if __name__ == "__main__":
    main()
