import re
from pathlib import Path
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

INSERT_ABOVE = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Cyprus/AlfaSport.png",🇨🇾 | AlfaSport'


def read_channels():

    channels = []

    if not Path(CHANNEL_FILE).exists():
        print("❌ JWPlayer_Channels.txt ontbreekt")
        return channels

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if "|" not in line:
                continue

            extinf, url = line.rsplit("|", 1)

            channels.append({
                "extinf": extinf.strip(),
                "url": url.strip()
            })

    return channels


def capture_stream(page, url):

    stream = None

    def handle_response(response):

        nonlocal stream

        if ".m3u8" in response.url:
            stream = response.url

    page.on("response", handle_response)

    try:

        page.goto(url, timeout=45000)

        page.wait_for_timeout(10000)

    except Exception as e:

        print("⚠️ Page error:", e)

    page.remove_listener("response", handle_response)

    return stream


def update_playlist(channels, streams):

    if not Path(PLAYLIST_FILE).exists():
        print("⚠️ TCL.m3u niet gevonden")
        return

    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):

        if skip_next:
            skip_next = False
            continue

        replaced = False

        for ch in channels:

            if line.startswith(ch["extinf"]):

                stream = streams.get(ch["extinf"], FALLBACK)

                new_lines.append(ch["extinf"])
                new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
                new_lines.append(stream)

                skip_next = True
                replaced = True
                break

        if not replaced:
            new_lines.append(line)

    # nieuwe kanalen toevoegen indien ze niet bestaan

    for ch in channels:

        if not any(ch["extinf"] in l for l in new_lines):

            stream = streams.get(ch["extinf"], FALLBACK)

            try:

                index = new_lines.index(INSERT_ABOVE)

                new_lines.insert(index, ch["extinf"])
                new_lines.insert(index + 1, f"#EXTVLCOPT:http-referrer={ch['url']}")
                new_lines.insert(index + 2, stream)

            except ValueError:

                new_lines.append(ch["extinf"])
                new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
                new_lines.append(stream)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

        f.write("\n".join(new_lines))

    print("🎵 TCL.m3u opgeslagen")


def main():

    print("🚀 JWPlayer scraper gestart")

    channels = read_channels()

    print("📺 Kanalen:", len(channels))

    streams = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        for ch in channels:

            print("\n🔎 Scrapen:", ch["extinf"])

            stream = capture_stream(page, ch["url"])

            if stream:

                print("✅ Stream:", stream)

                streams[ch["extinf"]] = stream

            else:

                print("⚠️ fallback gebruikt")

                streams[ch["extinf"]] = FALLBACK

        browser.close()

    update_playlist(channels, streams)


if __name__ == "__main__":
    main()
