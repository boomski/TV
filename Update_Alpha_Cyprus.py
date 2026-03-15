from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def capture_stream():

    found = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720}
        )

        page = context.new_page()

        def handle_response(response):

            url = response.url

            if (
                "l4.cloudskep.com" in url
                and "playlist.m3u8" in url
                and "wmsAuthSign=" in url
            ):

                if url not in found:

                    found.append(url)

                    print("🔎 token gevonden:", url)

        page.on("response", handle_response)

        try:

            page.goto(PAGE_URL, timeout=60000, wait_until="networkidle")

            # player scripts laten laden
            page.wait_for_timeout(8000)

        except Exception as e:

            print("⚠️ Page error:", e)

        browser.close()

    if not found:

        return None

    print(f"📡 {len(found)} tokens gevonden")

    # laatste token is meestal de juiste
    best = found[-1]

    print("🎯 gekozen token:", best)

    return best


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
            new_lines.append(stream)

            i += 1

            # oude regels verwijderen
            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            continue

        new_lines.append(line)

        i += 1

    path.write_text("\n".join(new_lines), encoding="utf-8")

    print("🎵 playlist geupdate")


def main():

    print("🚀 Alpha Cyprus robuuste scraper gestart")

    stream = capture_stream()

    if not stream:

        print("❌ geen token gevonden")

        return

    update_playlist(stream)


if __name__ == "__main__":
    main()
