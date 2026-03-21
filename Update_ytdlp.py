import subprocess
import json
import time
from urllib.parse import urlparse

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT = "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


# 🔄 update yt-dlp
def update_ytdlp():
    print("🔄 yt-dlp updaten...")
    try:
        subprocess.run(["yt-dlp", "-U"], capture_output=True, text=True)
    except Exception as e:
        print("⚠️ Update mislukt:", e)


# 🌍 referer
def get_referer(page_url):
    try:
        p = urlparse(page_url)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except:
        return page_url


# 🎯 ULTRA ROBUUSTE STREAM FETCH
def get_stream(page_url, retries=3):
    for attempt in range(retries):
        print(f"⏳ Sniffen ({attempt+1}/{retries}): {page_url}")

        try:
            result = subprocess.run(
                [
                    "yt-dlp",
                    "-J",
                    "--no-warnings",
                    "--user-agent", "Mozilla/5.0",
                    page_url
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if not result.stdout:
                print("❌ Lege output")
                time.sleep(2)
                continue

            data = json.loads(result.stdout)

            # 🔥 DIRECTE URL
            if "url" in data:
                u = data["url"]
                if u and "m3u8" in u:
                    print("🎯 directe m3u8")
                    return u

            formats = data.get("formats", [])

            # sorteer kwaliteit
            formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

            # 🎯 chunklist eerst
            for f in formats:
                u = f.get("url")
                if u and "chunklist.m3u8" in u:
                    print("🎯 chunklist gevonden")
                    return u

            # 🔁 fallback
            for f in formats:
                u = f.get("url")
                if u and "m3u8" in u:
                    print("⚠️ fallback m3u8")
                    return u

            print("❌ Geen m3u8 gevonden")

        except Exception as e:
            print("❌ fout:", e)

        time.sleep(2)

    return None


# 🔥 CLEAN UPDATE (NOOIT LEGE BLOKKEN)
def update_channel(lines, name, new_url, referer):
    REFERRER = f"#EXTVLCOPT:http-referrer={referer}"

    # pak alleen echte naam
    channel_name = name.split("|")[-1].strip()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and channel_name in line:
            print(f"🎯 Match: {channel_name}")

            # einde blok
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#EXTINF"):
                j += 1

            # 🔥 BELANGRIJK: alleen als URL geldig is
            if not new_url or not new_url.startswith("http"):
                print("❌ Ongeldige URL → skip update")
                return False

            new_block = [
                USER_AGENT,
                REFERRER,
                new_url
            ]

            lines[i+1:j] = [l + "\n" for l in new_block]

            print("🔁 Blok OK geüpdatet")
            return True

        i += 1

    print(f"❌ Geen match voor: {channel_name}")
    return False


# 🚀 MAIN
def main():
    update_ytdlp()

    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        channels = f.readlines()

    updated_any = False

    for ch in channels:
        ch = ch.strip()
        if not ch or "|" not in ch:
            continue

        name, url = ch.rsplit("|", 1)
        name = name.strip()
        url = url.strip()

        print("\n======================")
        print("📺", name)

        stream = get_stream(url)

        # 🔥 HARD CHECK (belangrijk!)
        if stream and stream.startswith("http"):
            referer = get_referer(url)

            if update_channel(lines, name, stream, referer):
                updated_any = True
        else:
            print("❌ Geen geldige stream → niets aangepast")

    if updated_any:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("\n💾 TCL.m3u geüpdatet")
    else:
        print("\n⚠️ Geen wijzigingen")


if __name__ == "__main__":
    main()
