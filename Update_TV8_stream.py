from playwright.sync_api import sync_playwright

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

        print("⏳ Open TV8...")
        page.goto("https://tv8.md/live", wait_until="domcontentloaded")

        # kleine delay voor stabiliteit
        page.wait_for_timeout(3000)

        # ▶️ probeer playback te starten
        try:
            page.click("video", timeout=5000)
            print("▶️ Play geklikt")
        except:
            print("⚠️ Geen klik nodig")

        try:
            # 🔥 RESOLVER: wacht op echte stream request
            response = page.wait_for_response(
                lambda r: (
                    r.status == 200
                    and "cdn.tv8.md" in r.url
                    and "index.m3u8" in r.url
                    and "token=" in r.url
                ),
                timeout=20000
            )

            stream_url = response.url
            print("✅ RESOLVED STREAM:", stream_url)

        except:
            print("❌ Geen stream gevonden (timeout)")
            stream_url = None

        browser.close()
        return stream_url


def update_m3u(new_url):
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False

    for i in range(len(lines)):
        line = lines[i].strip()

        # 🎯 exact match op jouw kanaal
        if line.startswith("#EXTINF") and line.endswith("," + TARGET_NAME):
            print("🎯 Match gevonden:", line)

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
        print("❌ Geen geldige TV8 stream")
    else:
        print("🚀 FINAL URL:", url)
        update_m3u(url)
