from playwright.sync_api import sync_playwright
import re

M3U_FILE = "TCL.m3u"
TARGET_NAME = "🇲🇩 | TV8"

def get_stream():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        stream_url = None

        def handle_response(response):
            nonlocal stream_url
            url = response.url
            if "tv8.md" in url and "index.m3u8" in url:
                stream_url = url

        page.on("response", handle_response)

        page.goto("https://tv8.md/live", wait_until="domcontentloaded")
        page.wait_for_timeout(15000)

        browser.close()
        return stream_url


def update_m3u(new_url):
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False

    for i in range(len(lines)):
        if "#EXTINF" in lines[i] and TARGET_NAME in lines[i]:
            lines[i + 1] = new_url + "\n"
            updated = True
            break

    if updated:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("✅ TV8 updated")
    else:
        print("❌ TV8 EXTINF niet gevonden")


if __name__ == "__main__":
    url = get_stream()

    if not url:
        print("❌ Geen TV8 stream gevonden")
    else:
        print("🎯 TV8:", url)
        update_m3u(url)
