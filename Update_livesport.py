import requests
import re

INPUT_URL = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/events.m3u8"
MAIN_FILE = "TCL.m3u"

# -----------------------------
# 🧠 EMOJI ENGINE (ULTIMATE FOOTBALL EDITION)
# -----------------------------
def detect_emoji(name):
    n = name.lower()
    if any(x in n for x in ["ufc", "mma", "fight", "pfl"]): return "🥋"
    if "boxing" in n or "kickboxing" in n: return "🥊"
    if any(x in n for x in ["nba", "lakers", "celtics", "warriors", "bucks", "bulls"]): return "🏀"
    if any(x in n for x in ["nfl", "super bowl", "college football"]): return "🏈"
    if any(x in n for x in ["nhl", "stanley cup"]): return "🏒"
    if any(x in n for x in ["mlb", "world series"]): return "⚾"
    if any(x in n for x in ["f1", "formula 1", "grand prix", "motogp", "nascar"]): return "🏎️"
    if any(x in n for x in ["tennis", "atp", "wta", "grand slam"]): return "🎾"
    if "cricket" in n: return "🏏"
    if "rugby" in n: return "🏉"
    if "golf" in n: return "⛳"
    if "cycling" in n or "tour de france" in n: return "🚴"
    if "darts" in n: return "🎯"
    if "snooker" in n or "pool" in n: return "🎱"
    if "olympics" in n or "olympic" in n: return "🏅"
    if any(x in n for x in ["league of legends", "lol", "dota 2", "cs:go", "overwatch"]): return "🕹️"
    
    football_competitions = {
        "champions league": "🇪🇺⚽", "uefa europa league": "🇪🇺⚽", "premier league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽",
        "england championship": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽", "england league one": "🏴󠁧󠁢󠁥󠁮󠁧󠁿⚽", "la liga": "🇪🇸⚽",
        "liga bbva": "🇪🇸⚽", "serie a": "🇮🇹⚽", "bundesliga": "🇩🇪⚽", "bundesliga 2": "🇩🇪⚽",
        "ligue 1": "🇫🇷⚽", "eredivisie": "🇳🇱⚽", "jupiler pro league": "🇧🇪⚽",
        "scottish premiership": "🏴󠁧󠁢󠁳󠁣󠁴󠁿⚽", "primeira liga": "🇵🇹⚽", "super lig": "🇹🇷⚽",
        "superligaen": "🇩🇰⚽", "a-league": "🇦🇺⚽", "championship argentina": "🇦🇷⚽",
        "argentina primera division": "🇦🇷⚽", "argentina liga profesional": "🇦🇷⚽",
        "colombia primera a": "🇨🇴⚽", "mls": "🇺🇸⚽", "liga mx": "🇲🇽⚽", "brasileirao": "🇧🇷⚽",
        "peru liga 1 apertura": "🇵🇪⚽", "chile primera division": "🇨🇱⚽",
        "uruguay primera division": "🇺🇾⚽", "paraguay primera division": "🇵🇾⚽",
        "ecuador serie a": "🇪🇨⚽", "bolivia primera division": "🇧🇴⚽",
        "venezuela primera division": "🇻🇪⚽", "canada premier league": "🇨🇦⚽",
        "j-league": "🇯🇵⚽", "k-league": "🇰🇷⚽", "super league": "🇨🇭⚽",
    }
    for key, emoji in football_competitions.items():
        if key in n: return emoji
    if " vs " in n: return "⚽"
    return "📺"

# -----------------------------
# 🧹 CLEAN MATCH NAME
# -----------------------------
def clean_name(name):
    name = name.replace(" vs ", " VS ")
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

# -----------------------------
# 🔑 MATCH KEY (voor dedupe)
# -----------------------------
def match_key(name):
    return clean_name(name).lower()

# -----------------------------
# 📡 CHECK STREAM (optioneel)
# -----------------------------
def is_working(url):
    try:
        return url.endswith(".m3u8")
    except:
        return False

# -----------------------------
# 📥 LOAD TCL
# -----------------------------
def load_main():
    # Full cleanup: start always with fresh M3U
    return ["#EXTM3U"]

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
# 🚀 FETCH EVENTS FROM SOURCE
# -----------------------------
def fetch_events():
    print("📡 Fetching streams...")
    res = requests.get(INPUT_URL, timeout=15)
    lines = res.text.splitlines()
    events = []

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            raw_name = lines[i]
            logo_match = re.search(r'tvg-logo="([^"]+)"', raw_name)
            logo = logo_match.group(1) if logo_match else ""

            name = raw_name.split(",")[-1].strip() if "," in raw_name else raw_name

            i += 1
            extra = []
            while i < len(lines) and not lines[i].startswith("#EXTINF") and not lines[i].startswith("http"):
                extra.append(lines[i])
                i += 1

            url = lines[i] if i < len(lines) else ""

            if is_working(url):
                entry = {
                    "name": name,
                    "logo": logo,
                    "extra": extra,
                    "url": url
                }
                events.append(entry)
        else:
            i += 1
    return events

# -----------------------------
# 📝 BUILD FINAL OUTPUT
# -----------------------------
def build_output(events):
    output = []
    for e in events:
        output.append(format_extinf(e["name"], e["logo"]))
        for line in e["extra"]:
            output.append(line)
        output.append(e["url"])
    return output

# -----------------------------
# 🔄 UPDATE PLAYLIST
# -----------------------------
def update_playlist():
    base = load_main()  # fresh start
    events = fetch_events()
    final_entries = build_output(events)
    final = base + [""] + final_entries
    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final))
    print("✅ GOD MODE UPDATE COMPLETE: all old entries removed, new emoji streams added!")

# -----------------------------
# ▶ RUN
# -----------------------------
if __name__ == "__main__":
    update_playlist()
