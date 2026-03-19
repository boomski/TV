from playwright.sync_api import sync_playwright
import time

M3U_FILE = "TCL.m3u"
TARGET_NAME = "🇲🇩 | TV8"


def get_stream():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            extra_http_headers={
                "Referer": "https://tv8.md/live",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"
            }
        )

        page = context.new_page()

        stream_url = None

        def handle_response(response):
            nonlocal stream_url
            url = response.url

            # 🔍 Debug (kan je uitzetten later)
            if ".m3u8" in url:
                print("🌐 gevonden:", url)

            # 🎯 pak alleen MASTER playlist
            if "cdn.tv8.md" in url and "index.m3u8" in url and "token=" in url:
                print("✅ MASTER GEVONDEN:", url)
                stream_url = url

        page.on("response", handle_response)

        print("⏳ Open TV8 pagina...")
        page.goto("https://tv8.md/live", wait_until="domcontentloaded")

        # ▶️ probeer player te triggeren
        try:
            page.click("video", timeout=5000)
            print("▶️ Play geklikt")
        except:
            print("⚠️ Geen klik nodig")

        # ⏱️ wacht tot stream geladen is
        page.wait_for_timeout(15000)

        browser.close()

        return stream_url


def update_m3u(new_url):
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False

    for i in range(len(lines)):
        line = lines[i].strip()

        # 🎯 exact match op kanaalnaam
        if line.startswith("#EXTINF") and line.endswith("," + TARGET_NAME):
            print("🎯 Match:", line)

            # ⚠️ check of volgende lijn bestaat
            if i + 1 < len(lines):
                lines[i + 1] = new_url.strip() + "\n"
                updated = True
            else:
                print("❌ Geen URL regel onder EXTINF")

            break

    if updated:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("💾 M3U succesvol geüpdatet!")
    else:
        print("❌ EXTINF niet gevonden of update mislukt")


if __name__ == "__main__":
    url = get_stream()

    if not url:
        print("❌ Geen geldige TV8 stream gevonden")
    else:
        print("🚀 FINAL URL:", url)
        update_m3u(url)
