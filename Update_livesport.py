import requests
import re

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"

# -----------------------------
# EMOJI MAPPING
# -----------------------------
EMOJI_MAP = {
    "Boxing": "🥊",
    "Soccer": "⚽",
    "Basketball": "🏀",
    "Tennis": "🎾",
    "MMA": "🥋",
    "Football": "🏈",
    "Hockey": "🏒",
}

# -----------------------------
# CHECK OF STREAM WERKT
# -----------------------------
def is_working(url):
    # alleen echte m3u8 streams
    if not url.startswith("http") or ".m3u8" not in url:
        return False

    try:
        r = requests.get(url, timeout=6, stream=True)
        return r.status_code == 200
    except:
        return False


# -----------------------------
# LAAD BESTAANDE TCL
# -----------------------------
def load_main():
    try:
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except:
        return ["#EXTM3U"]


# -----------------------------
# VERWIJDER OUDE EVENTS (FIXED)
# -----------------------------
def remove_old_events(lines):
    new_lines = []
    skipping = False

    for line in lines:

        # Start event blok
        if line.startswith("#EXTINF") and "Live Events" in line:
            skipping = True
            continue

        if skipping:
            # Stop als nieuwe EXTINF start
            if line.startswith("#EXTINF"):
                skipping = False
                new_lines.append(line)
            else:
                continue
        else:
            new_lines.append(line)

    return new_lines


# -----------------------------
# FORMAT EXTINF NAAR JOUW STIJL
# -----------------------------
def format_extinf(name_line):
    # logo pakken
    logo_match = re.search(r'tvg-logo="([^"]+)"', name_line)
    logo = logo_match.group(1) if logo_match else ""

    # naam pakken
    if "," in name_line:
        orig_name = name_line.split(",")[-1].strip()
    else:
        orig_name = name_line.strip()

    # tag -> emoji
    tag_match = re.match(r"\[(.*?)\]\s*(.*)", orig_name)
    if tag_match:
        tag = tag_match.group(1)
        rest = tag_match.group(2)
        emoji = EMOJI_MAP.get(tag, "")
        new_name = f"{emoji} {rest}".strip()
    else:
        new_name = orig_name

    # nieuwe EXTINF
    if logo:
        return f'#EXTINF:-1 tvg-logo="{logo}",{new_name}'
    else:
        return f'#EXTINF:-1,{new_name}'


# -----------------------------
# FETCH + FILTER EVENTS
# -----------------------------
def fetch_events():
    print("📡 Fetching events...")

    try:
        res = requests.get(INPUT_URL, timeout=10)
        lines = res.text.splitlines()
    except:
        print("❌ Failed to fetch events list")
        return []

    result = []
    seen_urls = set()  # dedupe

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            name = lines[i]
            extra_lines = []
            i += 1

            # verzamel VLCOPT etc
            while i < len(lines) and not lines[i].startswith("#EXTINF") and not lines[i].startswith("http"):
                extra_lines.append(lines[i])
                i += 1

            url = lines[i] if i < len(lines) else ""

            # check stream
            if url.startswith("http") and is_working(url) and url not in seen_urls:

                seen_urls.add(url)

                formatted_name = format_extinf(name)
                result.append(formatted_name)

                # VLC headers behouden
                for extra in extra_lines:
                    if extra.startswith("#EXTVLCOPT"):
                        result.append(extra)

                result.append(url)

                print("✔ WORKING:", url)
            else:
                print("✖ SKIP:", url)

            i += 1
        else:
            i += 1

    return result


# -----------------------------
# UPDATE TCL
# -----------------------------
def update_playlist():
    print("⏳ Updating TCL.m3u...")

    base = load_main()
    base = remove_old_events(base)

    events = fetch_events()

    final = base + [""] + events

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final))

    print("✅ TCL.m3u updated!\n")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    update_playlist()
