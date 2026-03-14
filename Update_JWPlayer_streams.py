import re
from pathlib import Path
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line or "|" not in line:
                continue

            extinf, url = line.rsplit("|", 1)

            channels.append({
                "extinf": extinf.strip(),
                "url": url.strip()
            })

    return channels


def convert_to_master(url):

    # chunklist → playlist (beste kwaliteit)
    if "chunklist" in url:
        url = re.sub(r"chunklist[^/]*\.m3u8", "playlist.m3u8", url)

    return url


def capture_stream(page, url):

    stream = None

    def handle_response(response):

        nonlocal stream

        if ".m3u8" in response.url:
            stream = response.url

    page.on("response", handle_response)

    try:

        page.goto(url, timeout=60000)
        page.wait_for_timeout(12000)

    except Exception as e:

        print("⚠️ Page error:", e)

    page.remove_listener("response", handle_response)

    if stream:
        stream = convert_to_master(stream)

    return stream


def update_playlist(channels, streams):

    if not Path(PLAYLIST_FILE).exists():
        print("⚠️ TCL.m3u niet gevonden")
        return

    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_lines = []
    skip = 0

    for line in lines:

        if skip > 0:
            skip -= 1
            continue

        replaced = False

        for ch in channels:

            if line.startswith(ch["extinf"]):

                stream = streams.get(ch["extinf"], FALLBACK)

                new_lines.append(ch["extinf"])
                new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
                new_lines.append(stream)

                skip = 2
                replaced = True
                break

        if not replaced:
            new_lines.append(line)

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
