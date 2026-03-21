import subprocess
import json

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT_LINE = "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"


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


def normalize_url(url):
    return url.split("~")[0]


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

        # 🎯 pak beste chunklist
        formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

        for f in formats:
            url = f.get("url", "")
            if "chunklist.m3u8" in url:
                print("🎯 chunklist gevonden:", url)
                return url

        # fallback → eender welke m3u8
        for f in formats:
            url = f.get("url", "")
            if "m3u8" in url:
                print("⚠️ fallback m3u8:", url)
                return url

    except Exception as e:
        print("❌ yt-dlp fout:", e)

    return None


def update_channel(lines, name, new_url):
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and name in line:
            print(f"🎯 Match: {name}")

            next_is_ua = (i + 1 < len(lines) and "#EXTVLCOPT:http-user-agent" in lines[i + 1])

            if next_is_ua:
                url_index = i + 2
            else:
                lines.insert(i + 1, USER_AGENT_LINE + "\n")
                print("⚠️ User-Agent toegevoegd")
                url_index = i + 2

            if url_index < len(lines) and lines[url_index].strip().startswith("http"):
                old_url = lines[url_index].strip()

                if normalize_url(old_url) == normalize_url(new_url):
                    print("⚠️ Zelfde stream → skip")
                    return False
                else:
                    lines[url_index] = new_url + "\n"
                    print("🔁 Updated!")
                    return True
            else:
                lines.insert(url_index, new_url + "\n")
                print("⚠️ URL toegevoegd")
                return True

        i += 1

    print(f"❌ Geen match: {name}")
    return False


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
            if update_channel(lines, name, stream):
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
