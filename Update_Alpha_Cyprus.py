from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"


def score_stream(url):

    score = 0

    if "/fhd/" in url:
        score += 100
    elif "/hd/" in url:
        score += 50
    elif "/sd/" in url:
        score += 10

    if "am" in url:
        score += 5
    elif "eu" in url:
        score += 3
    elif "us" in url:
        score += 1

    return score


def capture_stream():

    streams = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = p.chromium.launch().new_page()

        def handle_response(response):

            url = response.url

            if (
                ".m3u8" in url
                and "cloudskep.com" in url
                and "alphacyp" in url
                and "chunks.m3u8" in url
            ):

                streams.append(url)

                print("🔎 gevonden:", url)

        page.on("response", handle_response)

        page.goto(PAGE_URL)

        page.wait_for_timeout(10000)

        browser.close()

    if not streams:
        return None

    best = max(streams, key=score_stream)

    return best


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

    print("🚀 Alpha Cyprus scraper gestart")

    stream = capture_stream()

    if stream:

        print("✅ Beste stream:")
        print(stream)

        update_playlist(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
