import subprocess
import json

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT_LINE = "#EXTVLCOPT:http-user-agent=Mozilla/5.0"


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
            print("❌ Lege output van yt-dlp")
            return None

        data = json.loads(result.stdout)
        formats = data.get("formats", [])

        # sorteer op kwaliteit (hoog → laag)
        formats = sorted(formats, key=lambda x: x.get("height", 0), reverse=True)

        for f in formats:
            url = f.get("url", "")
            if "m3u8" in url:
                print("🎯 gevonden:", url)
                return url

    except Exception as e:
        print("❌ yt-dlp fout:", e)

    return None


def update_channel(lines, name, new_url):
    for i in range(len(lines)):
        line = lines[i].strip()

        if line.startswith("#EXTINF") and name in line:
            print(f"🎯 Match gevonden voor: {name}")

            # ✅ Case 1: EXTVLCOPT bestaat al
            if i + 1 < len(lines) and "#EXTVLCOPT:http-user-agent" in lines[i + 1]:
                if i + 2 < len(lines):
                    print("🔁 Oude URL:", lines[i + 2].strip())
                    lines[i + 2] = new_url + "\n"
                    print("✅ Nieuwe URL:", new_url)
                    return True

            # 🔥 Case 2: EXTVLCOPT ontbreekt → toevoegen
            else:
                print("⚠️ User-Agent ontbreekt → toevoegen")

                lines.insert(i + 1, USER_AGENT_LINE + "\n")
                lines.insert(i + 2, new_url + "\n")
                return True

    print(f"❌ Geen match in M3U voor: {name}")
    return False


def main():
    # 📥 lees M3U
    with open(M3U_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 📥 lees kanaallijst
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        channels = f.readlines()

    updated_any = False

    for ch in channels:
        ch = ch.strip()

        if not ch or "|" not in ch:
            continue

        # 🔥 BELANGRIJK: pak URL NA laatste |
        parts = ch.rsplit("|", 1)
        name = parts[0].strip()
        url = parts[1].strip()

        print("\n======================")
        print("📺 Kanaal:", name)

        stream = get_stream(url)

        if stream:
            success = update_channel(lines, name, stream)
            if success:
                updated_any = True
        else:
            print("❌ Geen stream gevonden")

    # 💾 schrijf M3U
    if updated_any:
        with open(M3U_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("\n💾 TCL.m3u succesvol geüpdatet!")
    else:
        print("\n⚠️ Geen updates gedaan")


if __name__ == "__main__":
    main()
