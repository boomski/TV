# Update_Aftermind_stream.py
import asyncio
from playwright.async_api import async_playwright
import re
from urllib.parse import urljoin

TCL_FILE = "TCL.m3u"
CHANNELS_FILE = "Aftermind_Channels.txt"
FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

async def main():
    print("🚀 Aftermind auto scraper gestart")

    # Lees kanalen
    channels = []
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, url = line.split("|", 1)
            channels.append({"name": name.strip(), "url": url.strip()})

    print(f"📺 Kanalen: {len(channels)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        results = {}
        for ch in channels:
            print(f"🔎 Laden: {ch['url']}")
            try:
                await page.goto(ch['url'], wait_until="networkidle", timeout=30000)

                # Zoek naar m3u8 in <video> of in scripts
                content = await page.content()
                m3u8 = None

                # 1) Kijk in <video> tag
                video_match = re.search(r'src=["\'](.*?\.m3u8[^"\']*)["\']', content)
                if video_match:
                    m3u8 = video_match.group(1)

                # 2) Zoek in scripts als nog niks
                if not m3u8:
                    script_match = re.search(r'(https?://.*?\.m3u8\?token=[^"\']+)', content)
                    if script_match:
                        m3u8 = script_match.group(1)

                if m3u8:
                    print(f"✅ Stream gevonden: {m3u8}")
                    results[ch['name']] = m3u8
                else:
                    print(f"❌ geen stream: {ch['name']}")
                    results[ch['name']] = FALLBACK

            except Exception as e:
                print(f"❌ fout bij laden: {ch['name']} - {e}")
                results[ch['name']] = FALLBACK

        await browser.close()

    # Update TCL.m3u
    with open(TCL_FILE, "r+", encoding="utf-8") as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()

        i = 0
        while i < len(lines):
            line = lines[i]
            updated = False
            for name, url in results.items():
                if name in line:
                    # vervang volgende regel door de nieuwe stream
                    lines[i+1] = url + "\n"
                    updated = True
                    break
            f.writelines([line])
            if updated:
                i += 2
            else:
                i += 1

    print(f"🎵 {TCL_FILE} opgeslagen")

if __name__ == "__main__":
    asyncio.run(main())
