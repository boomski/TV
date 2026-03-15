from pathlib import Path
from playwright.sync_api import sync_playwright
import requests

PAGE_URL = "https://www.alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.alphacyprus.com.cy/",
    "Origin": "https://www.alphacyprus.com.cy",
    "Accept": "*/*"
}


def stream_works(url):

    try:

        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code == 200 and "#EXTM3U" in r.text:

            print("✅ stream werkt")

            return True

    except Exception as e:

        print("⚠️ test error:", e)

    return False


def capture_stream():

    tokens = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width":1280,"height":720}
        )

        page = context.new_page()

        def handle_response(response):

            url = response.url

            if (
                "l4.cloudskep.com" in url
                and "playlist.m3u8" in url
                and "wmsAuthSign=" in url
            ):

                if url not in tokens:

                    print("🔎 token gevonden:", url)

                    tokens.append(url)

        page.on("response", handle_response)

        try:

            page.goto(PAGE_URL, timeout=60000, wait_until="networkidle")

            page.wait_for_timeout(10000)

        except Exception as e:

            print("⚠️ page error:", e)

        browser.close()

    print(f"📡 {len(tokens)} tokens gevonden")

    for url in tokens:

        print("🧪 testen:", url)

        if stream_works(url):

            print("🎯 werkende token:", url)

            return url

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

    print("🚀 Alpha Cyprus robuuste scraper gestart")

    stream = capture_stream()

    if stream:

        update_playlist(stream)

    else:

        print("❌ geen werkende token gevonden")


if __name__ == "__main__":
    main()
