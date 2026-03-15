import base64
import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE_URL = "https://alphacyprus.com.cy/live"

PLAYLIST_FILE = "TCL.m3u"

CHANNEL_NAME = "Alpha Cyprus"

REFRESH_MARGIN_MINUTES = 5


def decode_token(url):

    try:

        query = parse_qs(urlparse(url).query)

        token = query.get("wmsAuthSign", [None])[0]

        if not token:
            return None

        decoded = base64.b64decode(token).decode()

        parts = dict(
            item.split("=")
            for item in decoded.split("&")
            if "=" in item
        )

        server_time = parts.get("server_time")
        validminutes = int(parts.get("validminutes", 0))

        server_time = datetime.datetime.strptime(
            server_time,
            "%m/%d/%Y %I:%M:%S %p"
        )

        expiry = server_time + datetime.timedelta(minutes=validminutes)

        return expiry

    except Exception:

        return None


def read_current_stream():

    path = Path(PLAYLIST_FILE)

    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").splitlines()

    for line in lines:

        if "playlist.m3u8" in line and "wmsAuthSign" in line:

            return line

    return None


def token_still_valid(stream):

    expiry = decode_token(stream)

    if not expiry:
        return False

    now = datetime.datetime.utcnow()

    remaining = (expiry - now).total_seconds() / 60

    print(f"⏳ Token verloopt over {remaining:.1f} minuten")

    return remaining > REFRESH_MARGIN_MINUTES


def scrape_stream():

    stream = None

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        def handle_response(response):

            nonlocal stream

            url = response.url

            if (
                "l4.cloudskep.com" in url
                and "playlist.m3u8"
                and "wmsAuthSign" in url
            ):

                print("🎯 Token gevonden")

                stream = url

        page.on("response", handle_response)

        page.goto(PAGE_URL)

        page.wait_for_timeout(8000)

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

    print("🎵 Playlist geupdate")


def main():

    print("🚀 Alpha Cyprus smart scraper gestart")

    current = read_current_stream()

    if current and token_still_valid(current):

        print("✅ Token nog geldig — geen scrape nodig")
        return

    print("🔄 Nieuwe token ophalen...")

    stream = scrape_stream()

    if stream:

        print("✅ Nieuwe stream gevonden")

        update_playlist(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
