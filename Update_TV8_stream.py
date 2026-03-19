from playwright.sync_api import sync_playwright
import requests

M3U_FILE = "TCL.m3u"
TARGET_NAME = "🇲🇩 | TV8"


def is_valid(url):
    try:
        r = requests.get(url, timeout=5)
        return "#EXTM3U" in r.text
    except:
        return False


def get_stream():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            extra_http_headers={
                "Referer": "https://tv8.md/live",
                "User-Agent": "Mozilla/5.0"
            }
        )

        page = context.new_page()

        candidates = []

        def handle_response(response):
            url = response.url

            if (
                response.status == 200
                and "cdn.tv8.md" in url
                and "index.m3u8" in url
                and "token=" in url
            ):
                print("🎯 kandidaat:", url)
                candidates.append(url)

        page.on("response", handle_response)

        print("⏳ Open TV8...")
        page.goto("https://tv8.md/live", wait_until="domcontentloaded")

        # kleine delay voor stabiliteit
        page.wait_for_timeout(3000)

        # ▶️ forceer playback (BELANGRIJK)
        try:
            page.click("video", timeout=5000)
            print("▶️ Play geklikt")
        except:
            print("⚠️ Geen klik nodig")

        # ⏱️ wachten op echte stream
        page.wait_for_timeout(15000)

        browser.close()

        if not candidates:
            return None

        # 🔥 neem laatste (actieve)
        print("\n📋 Alle kandidaten:")
        for c in candidates:
            print(c)

        # probeer van achter naar voor (beste eerst)
        for url in reversed(candidates):
            print("🔎 testen:", url)
            if is_valid(url):
                print("✅ Geldige stream gevonden!")
                return url

        print("❌ Geen geldige stream gevonden")
        return None


def update_m3u(new_url):
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False

    for i in range(len(lines)):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and line.endswith("," + TARGET_NAME):
            print("🎯 Match:", line)

            if i + 1 < len(lines):
                lines[i + 1] = new_url.strip() + "\n"
                updated = True
            break

    if updated:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("💾 M3U geüpdatet!")
    else:
        print("❌ EXTINF niet gevonden")


if __name__ == "__main__":
    url = get_stream()

    if not url:
        print("❌ Geen TV8 stream gevonden")
    else:
        print("\n🚀 FINAL:", url)
        update_m3u(url)
