# Update_JWPlayer_streams.py
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

# Fallback link als stream niet beschikbaar
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

# Bestandspaden
CHANNELS_FILE = "JWPlayer_Channels.txt"
PLAYLIST_FILE = "TCL.m3u"

# Specifieke EXTINF regel waar we de nieuwe streams boven willen zetten
INSERT_ABOVE_EXTINF = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Turkije/Tivibu%20Spor.jpg",🇹🇷 | Tivibu Spor 1'

# Functie om stream te scrapen
def scrape_stream(page_url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(page_url, wait_until="networkidle")
            content = page.content()
            browser.close()

            # Zoek JWPlayer .m3u8 URL in de pagina
            match = re.search(r'https?://[^"\s]+\.m3u8(\?[^"\s]+)?', content)
            if match:
                return match.group(0)
            return None
    except Exception as e:
        print(f"⚠️ Page error: {e}")
        return None

# Lees kanalen
channels = []
if Path(CHANNELS_FILE).exists():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                extinf, url = line.split("|", 1)
                channels.append({"extinf": extinf, "url": url})
else:
    print(f"⚠️ {CHANNELS_FILE} niet gevonden")
    exit(1)

print(f"🚀 JWPlayer scraper gestart\n📺 Kanalen: {len(channels)}\n")

# Lees huidige playlist
playlist_content = ""
if Path(PLAYLIST_FILE).exists():
    with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
        playlist_content = f.read()

new_playlist = playlist_content.splitlines()

for ch in channels:
    print(f"🔎 Scrapen: {ch['extinf']}")
    stream = scrape_stream(ch['url'])
    if stream is None:
        print("⚠️ fallback gebruikt")
        stream = FALLBACK
    else:
        print(f"✅ Stream gevonden: {stream}")

    # Voeg http-referrer toe voor VLC compatibiliteit
    stream = f"#EXTVLCOPT:http-referrer={ch['url']}\n{stream}"

    # Oude entry verwijderen als die er al is
    pattern = re.compile(re.escape(ch['extinf']) + r".*?\n(?:#EXTVLCOPT:[^\n]*\n)?https?://[^\n]+", re.DOTALL)
    new_playlist = [line for line in new_playlist if not pattern.search(line)]

    # Boven de INSERT_ABOVE_EXTINF regel toevoegen
    try:
        index = new_playlist.index(INSERT_ABOVE_EXTINF)
        new_playlist.insert(index, ch['extinf'])
        new_playlist.insert(index + 1, stream)
    except ValueError:
        # Als de INSERT_ABOVE_EXTINF regel niet gevonden is, voeg onderaan toe
        new_playlist.append(ch['extinf'])
        new_playlist.append(stream)

    print(f"🔄 geupdate: {ch['extinf']}\n")

# Schrijf de playlist
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(new_playlist))

print(f"🎵 {PLAYLIST_FILE} opgeslagen")
