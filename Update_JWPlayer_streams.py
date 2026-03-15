import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time

CHANNEL_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
             "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def read_channels():
    channels = []
    with open(CHANNEL_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    for line in lines:
        if line.startswith("#EXTINF") and "|" in line:
            parts = line.split("|")
            extinf = "|".join(parts[:-1]).strip()
            url = parts[-1].strip()
            channels.append({"extinf": extinf, "url": url})
    return channels


def convert_to_master(url):
    # behoud chunks-formaat als het yayın is
    if "yayin" not in url:
        url = re.sub(r"(chunklist|chunks)[^/]*\.m3u8", "playlist.m3u8", url)
    return url


def is_valid_stream(url):
    try:
        r = requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=8)
        return r.status_code == 200
    except:
        return False


def capture_stream(driver, url):
    stream = None

    def capture():
        nonlocal stream
        logs = driver.execute_script("return window.performance.getEntries();")
        for log in logs:
            u = log.get("name", "")
            if ".m3u8" in u:
                # prioritize 'yayin' streams if available
                if "yayin" in u or "kuzeykibrissmart" in u or "kibristv" in u:
                    stream = u
                    return
                elif not stream:
                    stream = u

    driver.get(url)
    time.sleep(8)  # laat JS/Player laden
    capture()
    if stream:
        stream = convert_to_master(stream)
        if not is_valid_stream(stream):
            stream = None
    return stream


def write_block(extinf, referrer, stream):
    if not stream:
        stream = FALLBACK
    block = [extinf]
    block.append(f"#EXTVLCOPT:http-referrer={referrer}")
    if "yayin" in stream or "kuzeykibrissmart" in stream:
        block.append("#EXTVLCOPT:http-origin=https://canlitv.com")
        block.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
        block.append("#EXTVLCOPT:http-header=Accept:*/*")
    return block + [stream]


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
                # verwijder oude stream + headers
                if ".m3u8" in lines[i] or "#EXTVLCOPT" in lines[i]:
                    i += 1
                    continue
                new_lines.append(lines[i])
                i += 1
            continue
        new_lines.append(line)
        i += 1

    # nieuwe kanalen toevoegen als nog niet aanwezig
    existing = [l for l in new_lines if l.startswith("#EXTINF")]
    for ch in channels:
        if ch["extinf"] not in existing:
            stream = streams.get(ch["extinf"], FALLBACK)
            block = write_block(ch["extinf"], ch["url"], stream)
            new_lines.append("")
            new_lines.extend(block)

    return new_lines


def main():
    print("🚀 JWPlayer Selenium scraper gestart")
    channels = read_channels()
    print("📺 Kanalen:", len(channels))

    streams = {}

    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    driver = webdriver.Chrome(options=options)

    for ch in channels:
        print("\n🔎 Scrapen:", ch["extinf"])
        stream = capture_stream(driver, ch["url"])
        if stream:
            print("✅ Stream gevonden:", stream)
            streams[ch["extinf"]] = stream
        else:
            print("⚠️ fallback gebruikt")
            streams[ch["extinf"]] = FALLBACK

    driver.quit()

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
