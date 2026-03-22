import requests
import time

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"

def is_working(url):
    try:
        r = requests.get(url, timeout=6, stream=True)
        return r.status_code == 200
    except:
        return False

def load_main_playlist():
    try:
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return ["#EXTM3U"]

def remove_old_events(lines):
    cleaned = []
    skip = False

    for i in range(len(lines)):
        line = lines[i]

        if line.startswith("#EXTINF") and "group-title=\"Live Events\"" in line:
            skip = True
            continue

        if skip:
            skip = False
            continue

        cleaned.append(line)

    return cleaned

def fetch_and_filter_events():
    res = requests.get(INPUT_URL, timeout=10)
    lines = res.text.splitlines()

    new_entries = []
    i = 0

    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            name = lines[i]
            url = lines[i+1] if i+1 < len(lines) else ""

            if is_working(url):
                # Zorg dat group-title correct is
                if "group-title" not in name:
                    name = name.replace("#EXTINF:-1", '#EXTINF:-1 group-title="Live Events"')

                new_entries.append(name)
                new_entries.append(url)
                print("✔", url)
            else:
                print("✖", url)

            i += 2
        else:
            i += 1

    return new_entries

def update_playlist():
    print("⏳ Updating TCL.m3u...")

    main_lines = load_main_playlist()
    main_lines = remove_old_events(main_lines)

    events = fetch_and_filter_events()

    updated = main_lines + [""] + events

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated))

    print("✅ TCL.m3u updated!\n")

if __name__ == "__main__":
    while True:
        update_playlist()
        time.sleep(1800)  # 30 min
