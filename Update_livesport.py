import requests
import re

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"


# -----------------------------
# 🧠 EMOJI ENGINE (ULTIMATE FOOTBALL EDITION)
# -----------------------------
def detect_emoji(name):
    n = name.lower()

    # 🥋 Vecht- & combat sports
    if any(x in n for x in ["ufc", "mma", "fight" , "pfl"]):
        return "🥋"
    if "boxing" in n or "kickboxing" in n or "fighting" in n:
        return "🥊"

    # 🏀 Basketbal
    if any(x in n for x in ["nba", "lakers", "celtics", "warriors", "bucks", "bulls" , "ncaa"]):
        return "🏀"

    # 🏈 American Football
    if any(x in n for x in ["nfl", "super bowl", "college football"]):
        return "🏈"

    # 🏒 Hockey
    if any(x in n for x in ["nhl", "stanley cup"]):
        return "🏒"

    # ⚾ Baseball
    if any(x in n for x in ["mlb", "world series"]):
        return "⚾"

    # 🏎️ Motorsport
    if any(x in n for x in ["f1", "formula 1", "grand prix", "motogp", "nascar"]):
        return "🏎️"

    # 🎾 Tennis
    if any(x in n for x in ["tennis", "atp", "wta", "grand slam"]):
        return "🎾"

    # ⚽ Voetbal wereldwijd
    football_competitions = {
        # Europa
        "champions league": "🇪🇺⚽",
        "uefa europa league": "🇪🇺⚽",
        "premier league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽",
        "england championship": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽",
        "england league one": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽",
        "la liga": "🇪🇸⚽",
        "liga bbva": "🇪🇸⚽",
        "serie a": "🇮🇹⚽",
        "bundesliga": "🇩🇪⚽",
        "bundesliga 2": "🇩🇪⚽",
        "ligue 1": "🇫🇷⚽",
        "eredivisie": "🇳🇱⚽",
        "jupiler pro league": "🇧🇪⚽",
        "scottish premiership": "🏴󠁧󠁢󠁳󠁣󠁴󠁿⚽",
        "scotland championship": "🏴󠁧󠁢󠁳󠁣󠁴󠁿⚽",
        "primeira liga": "🇵🇹⚽",
        "super lig": "🇹🇷⚽",
        "superligaen": "🇩🇰⚽",
        "a-league": "🇦🇺⚽",
        "championship argentina": "🇦🇷⚽",
        "argentina primera division": "🇦🇷⚽",
        "argentina liga profesional": "🇦🇷⚽",
        "colombia primera a": "🇨🇴⚽",
        # Amerika
        "mls": "🇺🇸⚽",
        "liga mx": "🇲🇽⚽",
        "brasileirao": "🇧🇷⚽",
        "peru liga 1 apertura": "🇵🇪⚽",
        "chile primera division": "🇨🇱⚽",
        "uruguay primera division": "🇺🇾⚽",
        "paraguay primera division": "🇵🇾⚽",
        "ecuador serie a": "🇪🇨⚽",
        "bolivia primera division": "🇧🇴⚽",
        "venezuela primera division": "🇻🇪⚽",
        "canada premier league": "🇨🇦⚽",
        # Overige populaire competities
        "j-league": "🇯🇵⚽",
        "k-league": "🇰🇷⚽",
        "super league": "🇨🇭⚽",
    }
    for key, emoji in football_competitions.items():
        if key in n:
            return emoji

    # 🏐 Andere populaire sporten
    if "cricket" in n:
        return "🏏"
    if "rugby" in n:
        return "🏉"
    if "golf" in n:
        return "⛳"
    if "cycling" in n or "tour de france" in n:
        return "🚴"
    if "darts" in n:
        return "🎯"
    if "snooker" in n or "pool" in n:
        return "🎱"
    if "olympics" in n or "olympic" in n:
        return "🏅"

    # 🕹️ eSports
    if any(x in n for x in ["league of legends", "lol", "dota 2", "cs:go", "overwatch"]):
        return "🕹️"

    # ⚽ fallback voor "team vs team"
    if " vs " in n:
        return "⚽"

    # 📺 default
    return "📺"


# -----------------------------
# 🧹 CLEAN MATCH NAME
# -----------------------------
def clean_name(name):
    name = name.replace(" vs ", " VS ")
    name = re.sub(r"\[.*?\]", "", name)  # remove [tags]
    name = re.sub(r"\s+", " ", name).strip()
    return name


# -----------------------------
# 🔑 MATCH KEY (voor dedupe)
# -----------------------------
def match_key(name):
    return clean_name(name).lower()


# -----------------------------
# 📡 CHECK STREAM
# -----------------------------
def is_working(url):
    if ".m3u8" not in url:
        return False
    try:
        r = requests.get(url, timeout=6, stream=True)
        return r.status_code == 200
    except:
        return False


# -----------------------------
# 📥 LOAD TCL
# -----------------------------
def load_main():
    try:
        with open(MAIN_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except:
        return ["#EXTM3U"]


# -----------------------------
# 🧹 REMOVE OLD LIVESPORT EVENTS
# -----------------------------
def remove_old_livesport_entries(lines):
    """
    Verwijdert alleen de oude entries afkomstig van Update_livesport.py
    Detecteer via emojis in EXTINF: ⚽ 🥊 🏀 🏈 🏒 ⚾ 🏎️ 🎾 etc.
    """
    new_lines = []
    skip = False

    emojis_to_remove = ["⚽", "🥊", "🏀", "🏈", "🏒", "⚾", "🏎️", "🎾", "🏏", "🏉", "⛳", "🚴", "🎯", "🎱", "🏅", "🕹️"]

    for line in lines:
        if line.startswith("#EXTINF"):
            if any(e in line for e in emojis_to_remove):
                skip = True
                continue

        if skip:
            if line.startswith("#EXTINF"):
                skip = False
                new_lines.append(line)
            continue

        new_lines.append(line)

    return new_lines


# -----------------------------
# 🎯 FORMAT EXTINF
# -----------------------------
def format_extinf(name, logo=""):
    emoji = detect_emoji(name)
    clean = clean_name(name)

    if logo:
        return f'#EXTINF:-1 tvg-logo="{logo}",{emoji} {clean}'
    else:
        return f'#EXTINF:-1,{emoji} {clean}'


# -----------------------------
# 🚀 FETCH + GROUP STREAMS
# -----------------------------
def fetch_events():
    print("📡 Fetching & grouping streams...")

    res = requests.get(INPUT_URL, timeout=10)
    lines = res.text.splitlines()

    matches = {}  # {match_key: {name, logo, streams}}

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            raw_name = lines[i]

            logo_match = re.search(r'tvg-logo="([^"]+)"', raw_name)
            logo = logo_match.group(1) if logo_match else ""

            if "," in raw_name:
                name = raw_name.split(",")[-1].strip()
            else:
                name = raw_name

            i += 1

            extra = []
            while i < len(lines) and not lines[i].startswith("#EXTINF") and not lines[i].startswith("http"):
                extra.append(lines[i])
                i += 1

            url = lines[i] if i < len(lines) else ""

            if is_working(url):
                key = match_key(name)

                if key not in matches:
                    matches[key] = {
                        "name": name,
                        "logo": logo,
                        "streams": []
                    }

                matches[key]["streams"].append((extra, url))
                print("✔", name)
            else:
                print("✖", url)

            i += 1
        else:
            i += 1

    return matches


# -----------------------------
# 📝 BUILD FINAL LIST
# -----------------------------
def build_output(matches):
    output = []

    for match in matches.values():
        output.append(format_extinf(match["name"], match["logo"]))

        for extra, url in match["streams"]:
            for e in extra:
                if e.startswith("#EXTVLCOPT"):
                    output.append(e)
            output.append(url)

    return output


# -----------------------------
# 🔄 UPDATE PLAYLIST
# -----------------------------
def update_playlist():
    base = load_main()
    base = remove_old_livesport_entries(base)  # verwijder alleen oude live sport streams

    matches = fetch_events()
    events = build_output(matches)

    final = base + [""] + events

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final))

    print("✅ GOD MODE UPDATE DONE: oude live sport streams verwijderd, nieuwe toegevoegd")


# -----------------------------
# ▶ RUN
# -----------------------------
if __name__ == "__main__":
    update_playlist()
