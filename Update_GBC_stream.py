import requests

M3U_FILE = "TCL.m3u"
TARGET_NAME = "🇬🇮 | GBC TV"

CONFIG_URL = "https://player.vimeo.com/video/1174762515/config?autoplay=1&badge=0&byline=0&chromecast=1&collections=0&color=00adef&colors=000000%2C00adef%2Cffffff&context=embed_playlist.4156460&default_to_hd=0&external_embed=0&force_embed=1&fullscreen=1&h=4e063155ba&like=0&logo=0&play_button_position=auto&playbar=1&portrait=0&privacy_banner=0&quality_selector=1&referrer=https%3A%2F%2Fvimeo.com%2Fevent%2F4156460%2Fembed%2Finteraction&responsive=1&responsive_width=1&share=0&title=0&transcript=1&transparent=0&volume=1&watch_later=0&s=73fde10d8becda09f33e75462d8b393c208cd989_1774091160"


def get_stream():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://vimeo.com/"
    }

    print("⏳ Fetch GBC Vimeo config...")
    r = requests.get(CONFIG_URL, headers=headers, timeout=10)

    if r.status_code != 200:
        print("❌ Config fetch failed:", r.status_code)
        return None

    data = r.json()

    try:
        # 🔥 HLS streams
        cdns = data["request"]["files"]["hls"]["cdns"]

        print("📡 Beschikbare CDN's:", list(cdns.keys()))

        # pak eerste werkende
        for name, cdn in cdns.items():
            url = cdn.get("url")

            if url and "m3u8" in url:
                print(f"✅ GBC stream via {name}: {url}")
                return url

    except Exception as e:
        print("❌ Parsing error:", e)

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
        print("❌ Geen GBC stream gevonden")
    else:
        print("\n🚀 FINAL URL:", url)
        update_m3u(url)
