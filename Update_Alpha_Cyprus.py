import re
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

REFERRER = "https://alphacyprus.com.cy/"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def normalize_stream(url):

    parsed = urlparse(url)

    base = parsed.scheme + "://" + parsed.netloc + parsed.path

    # chunks → playlist
    base = re.sub(r"chunks\.m3u8", "playlist.m3u8", base)

    # quality playlist → master playlist
    base = re.sub(r"/l\d+/hd/playlist\.m3u8", "/playlist.m3u8", base)

    if parsed.query:
        return base + "?" + parsed.query

    return base


def capture_stream():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        def handle_response(response):

            nonlocal stream

            url = response.url

            if ".m3u8" in url and "alphacyp" in url:

                stream = normalize_stream(url)

        page.on("response", handle_response)

        try:

            page.goto(PAGE_URL, timeout=60000)

            page.wait_for_timeout(12000)

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

        if line.startswith("#EXTINF") and CHANNEL_NAME in line:

            print("📺 Alpha Cyprus gevonden")

            new_lines.append(line)

            new_lines.append(f"#EXTVLCOPT:http-referrer={REFERRER}")
            new_lines.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
            new_lines.append(stream)

            i += 1

            # oude regels verwijderen
            while i < len(lines) and not lines[i].startswith("#EXTINF"):

                if (
                    ".m3u8" in lines[i]
                    or "#EXTVLCOPT:http-referrer" in lines[i]
                    or "#EXTVLCOPT:http-user-agent" in lines[i]
                ):
                    i += 1
                    continue

                new_lines.append(lines[i])
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
