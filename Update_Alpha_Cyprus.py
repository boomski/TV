from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

REFERRER = "https://alphacyprus.com.cy/"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def choose_best_stream(streams):

    if not streams:
        return None

    # node voorkeur
    for node in ["am", "eu", "us"]:
        for s in streams:
            if f"{node}" in s:
                return s

    return streams[0]


def capture_stream():

    streams = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        def handle_response(response):

            url = response.url

            if ".m3u8" in url and "alphacyp" in url:

                if url not in streams:

                    streams.append(url)

                    print("🔎 gevonden:", url)

        page.on("response", handle_response)

        try:

            page.goto(PAGE_URL, timeout=60000)

            page.wait_for_timeout(12000)

        except Exception as e:

            print("⚠️ Page error:", e)

        browser.close()

    return choose_best_stream(streams)


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

        print("✅ Beste stream gekozen:")
        print(stream)

        update_playlist(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
