import subprocess
import json
from urllib.parse import urlparse

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT = "#EXTVLCOPT:http-user-agent=Mozilla/5.0"


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


# 🌍 automatische referer
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

        # 🔥 beste kwaliteit eerst
        formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

        # 🎯 chunklist eerst
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


# 🧠 slimme M3U update (GEEN duplicaten)
def update_channel(lines, name, new_url, referer):
    i = 0

    REFERRER = f"#EXTVLCOPT:http-referrer={referer}"

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and name in line:
            print(f"🎯 Match: {name}")

            # blok verzamelen
            j = i + 1
            block = []

            while j < len(lines) and not lines[j].startswith("#EXTINF"):
                block.append(lines[j].strip())
                j += 1

            # bestaande headers detecteren
            has_ua = any("http-user-agent" in l for l in block)
            has_ref = any("http-referrer" in l for l in block)

            # ❌ verwijder oude URLs
            block = [l for l in block if not l.startswith("http")]

            # ❌ dedupe headers
            new_block = []
            seen_ua = False
            seen_ref = False

            for l in block:
                if "http-user-agent" in l:
                    if not seen_ua:
                        new_block.append(USER_AGENT)
                        seen_ua = True
                elif "http-referrer" in l:
                    if not seen_ref:
                        new_block.append(REFERRER)
                        seen_ref = True
                else:
                    new_block.append(l)

            block = new_block

            # ➕ headers toevoegen indien nodig
            if not has_ua:
                print("⚠️ UA toegevoegd")
                block.insert(0, USER_AGENT)

            if not has_ref:
                print("⚠️ Referer toegevoegd")
                block.insert(1, REFERRER)

            # ➕ altijd nieuwe URL
            block.append(new_url)

            print("🔁 URL vernieuwd")

            # 🔥 terugschrijven
            lines[i+1:j] = [l + "\n" for l in block]

            return True

        i += 1

    print(f"❌ Geen match: {name}")
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
            print("❌ Geen stream")

    if updated_any:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("\n💾 M3U geüpdatet")
    else:
        print("\n⚠️ Geen wijzigingen")


if __name__ == "__main__":
    main()
