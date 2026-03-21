import subprocess
import json
from urllib.parse import urlparse

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT = "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"


# 🔄 update yt-dlp
def update_ytdlp():
    print("🔄 yt-dlp updaten...")
    try:
        result = subprocess.run(
            ["yt-dlp", "-U"],
            capture_output=True,
            text=True
        )
        print(result.stdout.strip())
    except Exception as e:
        print("⚠️ Update mislukt:", e)


# 🌍 automatische referer per kanaal
def get_referer(page_url):
    try:
        parsed = urlparse(page_url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except:
        return page_url


# 🎯 stream ophalen (chunklist prioriteit)
def get_stream(page_url):
    print(f"⏳ Sniffen: {page_url}")

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "-J",
                "--user-agent", "Mozilla/5.0",
                page_url
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if not result.stdout:
            print("❌ Lege output")
            return None

        data = json.loads(result.stdout)
        formats = data.get("formats", [])

        # beste kwaliteit eerst
        formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

        # chunklist eerst
        for f in formats:
            url = f.get("url", "")
            if "chunklist.m3u8" in url:
                print("🎯 chunklist gevonden")
                return url

        # fallback
        for f in formats:
            url = f.get("url", "")
            if "m3u8" in url:
                print("⚠️ fallback m3u8")
                return url

    except Exception as e:
        print("❌ yt-dlp fout:", e)

    return None


# 🔥 CLEAN REWRITE met exact-match
def update_channel(lines, name, new_url, referer):
    """
    Vervang alleen de URL van het kanaal exact zoals in de kanalenlijst,
    voeg headers toe indien nodig, voorkom duplicaten.
    """
    i = 0
    REFERRER = f"#EXTVLCOPT:http-referrer={referer}"

    while i < len(lines):
        line = lines[i].strip()

        # exact match op naam uit kanalenlijst
        if line.startswith("#EXTINF") and name in line:
            print(f"🎯 Match gevonden voor kanaal: {name}")

            # zoek einde blok
            j = i + 1
            while j < len(lines) and not lines[j].startswith("#EXTINF"):
                j += 1

            # clean block: alleen headers + URL
            new_block = [
                USER_AGENT,
                REFERRER,
                new_url
            ]

            print("🔁 Blok herschreven (exact match)")

            # vervang alles tussen EXTINF en volgende kanaal
            lines[i + 1:j] = [l + "\n" for l in new_block]

            return True

        i += 1

    print(f"❌ Geen match voor kanaal: {name}")
    return False


# 🚀 main
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

        # exact wat in kanalenlijst staat
        name, url = ch.rsplit("|", 1)
        name = name.strip()
        url = url.strip()

        print("\n======================")
        print("📺", name)

        stream = get_stream(url)
        if stream:
            referer = get_referer(url)
            if update_channel(lines, name, stream, referer):
                updated_any = True
        else:
            print("❌ Geen stream gevonden")

    if updated_any:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("\n💾 TCL.m3u geüpdatet")
    else:
        print("\n⚠️ Geen wijzigingen")


if __name__ == "__main__":
    main()
