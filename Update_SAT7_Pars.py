from pathlib import Path
from urllib.parse import unquote, parse_qs, urlparse
from playwright.sync_api import sync_playwright

PAGE_URL = "https://sat7plus.org/live/pars"

PLAYLIST_FILE = "TCL.m3u"

EXTINF_LINE = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Cyprus/Sat7%20Pars.png",🇨🇾 | Sat7 Pars'


def extract_real_stream(url):

    if "resource=" in url:

        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        if "resource" in qs:

            decoded = unquote(qs["resource"][0])

            return decoded

    return url


def capture_stream():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        def handle_response(response):

            nonlocal stream

            url = response.url

            if ".m3u8" in url or "resource=" in url:

                real = extract_real_stream(url)

                if ".m3u8" in real and "kwikmotion" in real:

                    stream = real

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

    print("🎵 Sat7 Pars stream geupdate")


def main():

    print("🚀 Sat7 Pars scraper gestart")

    stream = capture_stream()

    if stream:

        print("✅ Stream gevonden:")
        print(stream)

        update_playlist(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
