import requests

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"

# -----------------------------
# CHECK OF STREAM WERKT
# -----------------------------
def is_working(url):
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
# VERWIJDER OUDE EVENTS
# -----------------------------
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


# -----------------------------
# HAAL + FILTER EVENTS (FIXED)
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
    i = 0

    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            name = lines[i]
            extra_lines = []
            i += 1

            # Verzamel alles tussen EXTINF en URL (zoals VLCOPT)
            while i < len(lines) and not lines[i].startswith("#EXTINF") and not lines[i].startswith("http"):
                extra_lines.append(lines[i])
                i += 1

            # Pak URL
            url = lines[i] if i < len(lines) else ""

            # Alleen echte streams testen
            if url.startswith("http") and is_working(url):

                # Forceer group-title
                if "group-title" not in name:
                    name = name.replace("#EXTINF:-1", '#EXTINF:-1 group-title="Live Events"')

                result.append(name)

                # Voeg VLC headers terug toe (BELANGRIJK)
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


# -----------------------------
# UPDATE TCL.M3U
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
