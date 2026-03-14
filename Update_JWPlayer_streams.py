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
            channels.append({"extinf": extinf.strip(), "url": url.strip()})
    return channels

def convert_to_master(url):
    # pak master playlist
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
        page.wait_for_timeout(12000)
    except Exception as e:
        print("⚠️ Page error:", e)

    page.remove_listener("response", handle_response)

    if stream:
        stream = convert_to_master(stream)
    return stream

def update_playlist(lines, channels, streams):
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # check of dit een EXTINF regel van een kanaal is
        ch = next((c for c in channels if c["extinf"] == line), None)
        if ch:
            # vervang oude stream + referrer
            new_lines.append(line)
            new_lines.append(f"#EXTVLCOPT:http-referrer={ch['url']}")
            new_lines.append(streams.get(ch["extinf"], FALLBACK))
            # skip de oude stream regel
            i += 2
        else:
            new_lines.append(line)
        i += 1

    # voeg ontbrekende kanalen toe onderaan
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
