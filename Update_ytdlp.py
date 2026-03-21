import subprocess
import json
import os

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

# 👉 lokaal yt-dlp pad
YTDLP_PATH = "./yt-dlp.exe"

USER_AGENT_LINE = "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0"


def to_master_url(url):
    if "chunklist.m3u8" in url and "/avc/" in url:
        return url.split("/avc/")[0] + "/master.m3u8"
    return url


def normalize_url(url):
    return url.split("~")[0]


def get_stream(page_url, name):
    print(f"⏳ Sniffen: {page_url}")

    # 🔍 check of lokale yt-dlp bestaat
    if not os.path.exists(YTDLP_PATH):
        print("❌ yt-dlp.exe niet gevonden in root!")
        return None

    try:
        result = subprocess.run(
            [
                YTDLP_PATH,
                "-J",
                "--user-agent", "Mozilla/5.0",
                page_url
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if not result.stdout:
            print("❌ Lege output van yt-dlp")
            return None

        data = json.loads(result.stdout)
        formats = data.get("formats", [])

        # 🎯 SPECIFIEK: GBC TV debug
        if "GBC TV" in name:
            print(f"🔍 GBC formats gevonden: {len(formats)}")

        # ✅ eerst master proberen
        for f in formats:
            url = f.get("url", "")
            if "master.m3u8" in url:
                print("🎯 MASTER gevonden:", url)
                return url

        # ✅ fallback → beste kwaliteit
        formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

        for f in formats:
            url = f.get("url", "")
            if "m3u8" in url:
                master = to_master_url(url)
                print("🎯 fallback (→ master):", master)
                return master

    except Exception as e:
        print("❌ yt-dlp fout:", e)

    return None


def update_channel(lines, name, new_url):
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and name in line:
            print(f"🎯 Match gevonden voor: {name}")

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
                    print("🔁 URL geüpdatet!")
                    return True
            else:
                lines.insert(url_index, new_url + "\n")
                print("⚠️ URL ontbrak → toegevoegd")
                return True

        i += 1

    print(f"❌ Geen match in M3U voor: {name}")
    return False


def main():
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        channels = f.readlines()

    updated_any = False

    for ch in channels:
        ch = ch.strip()

        if not ch or "|" not in ch:
            continue

        parts = ch.rsplit("|", 1)
        name = parts[0].strip()
        url = parts[1].strip()

        print("\n======================")
        print("📺 Kanaal:", name)

        stream = get_stream(url, name)

        if stream:
            success = update_channel(lines, name, stream)
            if success:
                updated_any = True
        else:
            print("❌ Geen stream gevonden")

    if updated_any:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("\n💾 TCL.m3u succesvol geüpdatet!")
    else:
        print("\n⚠️ Geen updates gedaan")


if __name__ == "__main__":
    main()
