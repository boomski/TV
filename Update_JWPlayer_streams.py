import re
from pathlib import Path
from playwright.sync_api import sync_playwright

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


def read_channels():

    channels = []

    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:

        lines = [l.strip() for l in f if l.strip()]

    for line in lines:

        if line.startswith("#EXTINF") and "|" in line:

            parts = line.split("|")

            extinf = "|".join(parts[:-1]).strip()
            url = parts[-1].strip()

            channels.append({
                "extinf": extinf,
                "url": url
            })

    return channels


def convert_to_master(url):

    url = re.sub(r"(chunklist|chunks)[^/]*\.m3u8", "playlist.m3u8", url)

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

        page.wait_for_timeout(8000)

    except Exception as e:

        print("⚠️ Page error:", e)

    page.remove_listener("response", handle_response)

    if stream:

        stream = convert_to_master(stream)

    return stream


def write_block(extinf, referrer, stream):

    if stream is None:

        stream = FALLBACK

    block = [extinf]

    block.append(f"#EXTVLCOPT:http-referrer={referrer}")

    if "yayin" in stream:

        block.append("#EXTVLCOPT:http-origin=https://canlitv.com")
        block.append("#EXTVLCOPT:http-user-agent=Mozilla/5.0")
        block.append("#EXTVLCOPT:http-header=Accept:*/*")

    block.append(stream)

    return block


def update_playlist(lines, channels, streams):

    new_lines = []
    i = 0

    while i < len(lines):

        line = lines[i]

        ch = next((c for c in channels if c["extinf"] == line), None)

        if ch:

            stream = streams.get(ch["extinf"], FALLBACK)

            block = write_block(line, ch["url"], stream)

            new_lines.extend(block)

            i += 1

            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                i += 1

            continue

        new_lines.append(line)
        i += 1

    existing = [l for l in new_lines if l.startswith("#EXTINF")]

    for ch in channels:

        if ch["extinf"] not in existing:

            stream = streams.get(ch["extinf"], FALLBACK)

            block = write_block(ch["extinf"], ch["url"], stream)

            new_lines.append("")
            new_lines.extend(block)

    return new_lines


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

                print("✅ Stream gevonden")

                streams[ch["extinf"]] = stream

            else:

                print("⚠️ fallback gebruikt")

                streams[ch["extinf"]] = FALLBACK

        browser.close()

    lines = []

    if Path(PLAYLIST_FILE).exists():

        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:

            lines = f.read().splitlines()

    lines = update_playlist(lines, channels, streams)

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:

        f.write("\n".join(lines))

    print("🎵 TCL.m3u opgeslagen")


if __name__ == "__main__":
    main()
