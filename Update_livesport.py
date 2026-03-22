import requests
import re

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"

# Map categorie-tags naar emoji
EMOJI_MAP = {
    "Boxing": "🥊",
    "Soccer": "⚽",
    "Basketball": "🏀",
    "Tennis": "🎾",
    "MMA": "🥋",
    "Football": "🏈",
    "Hockey": "🏒",
}

def is_working(url):
    try:
        r = requests.get(url, timeout=6, stream=True)
        return r.status_code == 200
    except:
        return False

def load_main():
    try:
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except:
        return ["#EXTM3U"]

def remove_old_events(lines):
    new_lines = []
    skip = False
    for line in lines:
        if line.startswith("#EXTINF") and "group-title=\"Live Events\"" in line:
            skip = True
            continue
        if skip:
            skip = False
            continue
        new_lines.append(line)
    return new_lines

def format_extinf(name_line):
    """
    Zet een EXTINF regel om naar jouw formaat:
    - logo behouden
    - tag vervangen door emoji
    - naam opgeschoond
    """
    # Pak logo
    logo_match = re.search(r'tvg-logo="([^"]+)"', name_line)
    logo = logo_match.group(1) if logo_match else ""

    # Pak originele naam na laatste komma
    if "," in name_line:
        orig_name = name_line.split(",")[-1].strip()
    else:
        orig_name = name_line.strip()

    # Zoek categorie tag [XYZ] en vervang door emoji
    tag_match = re.match(r"\[(.*?)\]\s*(.*)", orig_name)
    if tag_match:
        tag = tag_match.group(1)
        rest_name = tag_match.group(2)
        emoji = EMOJI_MAP.get(tag, "")  # lege string als geen mapping
        new_name = f"{emoji} {rest_name}".strip()
    else:
        new_name = orig_name

    # Bouw nieuwe EXTINF regel
    if logo:
        return f'#EXTINF:-1 tvg-logo="{logo}",{new_name}'
    else:
        return f'#EXTINF:-1,{new_name}'

def fetch_events():
    print("📡 Fetching events...")

    try:
        res = requests.get(INPUT_URL, timeout=10)
        lines = res.text.splitlines()
    except:
        print("❌ Failed to fetch events list")
        return []

    result = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            name = lines[i]
            extra_lines = []
            i += 1

            # Verzamel alle tussenliggende lijnen (zoals VLCOPT)
            while i < len(lines) and not lines[i].startswith("#EXTINF") and not lines[i].startswith("http"):
                extra_lines.append(lines[i])
                i += 1

            url = lines[i] if i < len(lines) else ""

            # Alleen echte URLs testen
            if url.startswith("http") and is_working(url):
                formatted_name = format_extinf(name)
                result.append(formatted_name)

                # Voeg VLCOPT terug toe (optioneel)
                for extra in extra_lines:
                    if extra.startswith("#EXTVLCOPT"):
                        result.append(extra)

                result.append(url)
                print("✔ WORKING:", url)
            else:
                print("✖ DEAD:", url)

            i += 1
        else:
            i += 1
    return result

def update_playlist():
    print("⏳ Updating TCL.m3u...")

    base = load_main()
    base = remove_old_events(base)

    events = fetch_events()

    final = base + [""] + events

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final))

    print("✅ TCL.m3u updated!\n")

if __name__ == "__main__":
    update_playlist()
