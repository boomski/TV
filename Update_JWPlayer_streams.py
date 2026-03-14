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
    if "chunklist" in url:
        url = re.sub(r"chunklist[^/]*\.m3u8", "playlist.m3u8", url)
    if "chunks.m3u8" in url:
        url = url.replace("chunks.m3u8", "playlist.m3u8")
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


def update_playlist(lines, channels, streams):
    """
    Vervang de oude stream direct na de EXTINF regel
    """
    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            # vervang oude m3u8-link door nieuwe stream
            extinf_line = lines[i-1]
            ch = next((c for c in channels if c["extinf"] in extinf_line), None)
            if ch:
                stream = streams.get(ch["extinf"], FALLBACK)
                # voeg http-referrer erbij
                new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
                new_lines.append(stream)
            else:
                new_lines.append(line)
            continue

        new_lines.append(line)

        # detecteer kanaal EXTINF-regel
        if any(ch["extinf"] in line for ch in channels):
            skip_next = True

    # voeg ontbrekende kanalen toe (nieuwe) onderaan
    existing_extinfs = [line for line in new_lines if line.startswith("#EXTINF")]
    for ch in channels:
        if ch["extinf"] not in existing_extinfs:
            new_lines.append("")
            new_lines.append(ch["extinf"])
            new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
            new_lines.append(streams.get(ch["extinf"], FALLBACK))

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
                print("✅ Stream:", stream)
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
