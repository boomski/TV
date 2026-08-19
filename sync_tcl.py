#!/usr/bin/env python3
"""
Synchronise TCL.m3u with IPTV-org while preserving all existing/manual entries.

Rules:
- Existing TCL.m3u entries are never removed just because they are absent from IPTV-org.
- Only URLs recorded in .tcl-auto.json are eligible for automatic removal.
- IPTV-org URLs already present in TCL.m3u are never duplicated.
- New IPTV-org streams are tested before being added.
- tvg-country is converted to a flag emoji.
- Logos are resolved from boomski/TV-LOGO when a matching file can be found.
- Auto entries are written in the user's preferred format.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import requests

TCL_FILE = Path(os.getenv("TCL_FILE", "TCL.m3u"))
STATE_FILE = Path(os.getenv("STATE_FILE", ".tcl-auto.json"))

IPTV_URL = os.getenv(
    "IPTV_URL",
    "https://iptv-org.github.io/iptv/index.m3u",
)
LOGO_REPO = os.getenv(
    "LOGO_REPO",
    "https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main",
)
LOGO_API = os.getenv(
    "LOGO_API",
    "https://api.github.com/repos/boomski/TV-LOGO/git/trees/main?recursive=1",
)

CHECK_STREAMS = os.getenv("CHECK_STREAMS", "true").lower() not in {
    "0", "false", "no", "off"
}
CHECK_WORKERS = int(os.getenv("CHECK_WORKERS", "24"))
CHECK_TIMEOUT = float(os.getenv("CHECK_TIMEOUT", "8"))
MAX_NEW_STREAMS = int(os.getenv("MAX_NEW_STREAMS", "500"))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/131 Safari/537.36 "
    "TCL-IPTV-Sync/1.0"
)

COUNTRY_NAMES = {
    # Common names used by IPTV-org / ISO-style data.
    "BE": "België", "NL": "Nederland", "FR": "Frankrijk",
    "DE": "Duitsland", "GB": "Verenigd Koninkrijk", "UK": "Verenigd Koninkrijk",
    "IE": "Ierland", "ES": "Spanje", "IT": "Italië", "PT": "Portugal",
    "AT": "Oostenrijk", "CH": "Zwitserland", "LU": "Luxemburg",
    "US": "Verenigde Staten", "CA": "Canada", "AU": "Australië",
    "NZ": "Nieuw-Zeeland", "SE": "Zweden", "NO": "Noorwegen",
    "DK": "Denemarken", "FI": "Finland", "IS": "IJsland",
    "PL": "Polen", "CZ": "Tsjechië", "SK": "Slowakije",
    "HU": "Hongarije", "RO": "Roemenië", "BG": "Bulgarije",
    "GR": "Griekenland", "TR": "Turkije", "UA": "Oekraïne",
    "RU": "Rusland", "ZA": "Zuid-Afrika", "IN": "India",
    "JP": "Japan", "KR": "Zuid-Korea", "CN": "China",
    "TW": "Taiwan", "HK": "Hongkong", "SG": "Singapore",
    "MY": "Maleisië", "ID": "Indonesië", "TH": "Thailand",
    "PH": "Filipijnen", "BR": "Brazilië", "MX": "Mexico",
    "AR": "Argentinië", "CL": "Chili", "CO": "Colombia",
    "PE": "Peru", "AE": "Verenigde Arabische Emiraten",
    "SA": "Saoedi-Arabië", "IL": "Israël", "EG": "Egypte",
}

def flag(code: str) -> str:
    code = (code or "").strip().upper()
    # Handle "GB" and common IPTV-org alternatives.
    if code == "UK":
        code = "GB"
    if len(code) == 2 and code.isalpha():
        return "".join(chr(127397 + ord(c)) for c in code)
    return "🌐"

def parse_attrs(extinf: str) -> dict[str, str]:
    # Attribute parser for quoted M3U attributes.
    return dict(
        (k, v)
        for k, v in re.findall(r'([\w-]+)="([^"]*)"', extinf)
    )

def display_name(extinf: str) -> str:
    # IPTV-org's channel title is the text after the last comma.
    if "," in extinf:
        return extinf.rsplit(",", 1)[1].strip()
    return ""

def normalize_name(name: str) -> str:
    name = unquote(name or "")
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\s*\[[^\]]*\]\s*$", "", name).strip()
    return name.casefold()

def url_key(url: str) -> str:
    return url.strip()

def parse_tcl_entries(text: str) -> list[list[str]]:
    """
    Parse TCL into logical entries. An entry starts at #EXTINF and includes
    following directive lines / URL lines until the next #EXTINF.
    Blank lines outside an entry are preserved as separate blocks.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("#EXTINF:") and current:
            blocks.append(current)
            current = [line]
        elif line.startswith("#EXTINF:"):
            current = [line]
        elif current:
            current.append(line)
        else:
            if line == "":
                continue
            blocks.append([line])

    if current:
        blocks.append(current)

    return blocks

def block_urls(block: list[str]) -> list[str]:
    return [
        line.strip()
        for line in block
        if line.strip()
        and not line.lstrip().startswith("#")
        and re.match(r"^https?://", line.strip(), re.I)
    ]

def fetch_text(url: str) -> str:
    r = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=45,
    )
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    return r.text

def parse_iptv_org(text: str) -> list[dict]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    result = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF:"):
            attrs = parse_attrs(line)
            current = {
                "extinf": line,
                "attrs": attrs,
                "name": display_name(line),
                "url": None,
            }
            continue

        if current and re.match(r"^https?://", line, re.I):
            current["url"] = line
            result.append(current)
            current = None

    return result

def github_logo_index() -> dict[str, str]:
    """
    Build a normalized basename -> raw logo URL index from TV-LOGO.
    Failure is non-fatal: IPTV-org logo is used as fallback.
    """
    try:
        r = requests.get(
            LOGO_API,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        r.raise_for_status()
        tree = r.json().get("tree", [])
    except Exception as exc:
        print(f"Logo index unavailable, using IPTV-org logos: {exc}")
        return {}

    index = {}
    for item in tree:
        path = item.get("path", "")
        if item.get("type") != "blob":
            continue
        if not re.search(r"\.(png|jpg|jpeg|webp|svg)$", path, re.I):
            continue
        basename = Path(path).stem
        key = normalize_logo_key(basename)
        if key and key not in index:
            index[key] = f"{LOGO_REPO}/{quote(path, safe='/')}"
    return index

def normalize_logo_key(value: str) -> str:
    value = unquote(value or "")
    value = value.casefold()
    value = re.sub(r"\b(tv|hd|fhd|uhd|4k)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value

def find_logo(name: str, iptv_logo: str, logo_index: dict[str, str]) -> str:
    key = normalize_logo_key(name)
    if key in logo_index:
        return logo_index[key]

    # Some channel names contain punctuation / country suffixes.
    candidates = sorted(
        ((k, v) for k, v in logo_index.items() if k),
        key=lambda kv: len(kv[0]),
        reverse=True,
    )
    for k, v in candidates:
        if len(k) >= 5 and (k in key or key in k):
            return v

    return iptv_logo or ""

def build_extinf(item: dict, logo_index: dict[str, str]) -> str:
    attrs = item["attrs"]
    name = item["name"]
    countries = attrs.get("tvg-country", "")
    first_country = re.split(r"[;,]", countries)[0].strip().upper()
    emoji = flag(first_country)
    logo = find_logo(name, attrs.get("tvg-logo", ""), logo_index)

    if logo:
        return f'#EXTINF:-1 tvg-logo="{logo}",{emoji} | {name}'
    return f"#EXTINF:-1,{emoji} | {name}"

def is_working(url: str) -> bool:
    """
    A stream endpoint is considered alive if it returns a normal HTTP response
    or a partial-content response. Some providers reject HEAD, so GET with a
    tiny Range is used first.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Range": "bytes=0-1023",
        "Accept": "*/*",
    }
    try:
        with requests.get(
            url,
            headers=headers,
            timeout=CHECK_TIMEOUT,
            stream=True,
            allow_redirects=True,
        ) as r:
            if r.status_code in {200, 206, 301, 302, 303, 307, 308}:
                return True
            if 200 <= r.status_code < 400:
                return True
    except requests.RequestException:
        pass
    return False

def load_state() -> set[str]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {str(x) for x in data.get("auto_urls", [])}
    except Exception as exc:
        print(f"WARNING: cannot read {STATE_FILE}: {exc}")
        return set()

def save_state(urls: set[str]) -> None:
    STATE_FILE.write_text(
        json.dumps(
            {"version": 1, "auto_urls": sorted(urls)},
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

def render_blocks(blocks: list[list[str]]) -> str:
    out = ["#EXTM3U"]
    for block in blocks:
        # Remove leading/trailing blank lines in logical blocks.
        cleaned = block[:]
        while cleaned and cleaned[0] == "":
            cleaned.pop(0)
        while cleaned and cleaned[-1] == "":
            cleaned.pop()
        if cleaned:
            out.extend(cleaned)
    return "\n".join(out) + "\n"

def main() -> int:
    if not TCL_FILE.exists():
        print(f"ERROR: {TCL_FILE} not found")
        return 1

    original = TCL_FILE.read_text(encoding="utf-8-sig")
    blocks = parse_tcl_entries(original)

    # Every URL already in TCL is protected from duplicate insertion.
    existing_urls = set()
    for block in blocks:
        existing_urls.update(block_urls(block))

    old_auto = load_state()

    print(f"Existing TCL URLs: {len(existing_urls)}")
    print(f"Previously tracked automatic URLs: {len(old_auto)}")

    print(f"Downloading IPTV-org: {IPTV_URL}")
    source = fetch_text(IPTV_URL)
    candidates = parse_iptv_org(source)
    print(f"IPTV-org stream entries: {len(candidates)}")

    # Deduplicate IPTV-org itself by URL.
    unique = {}
    for item in candidates:
        u = item.get("url")
        if u and u not in unique:
            unique[u] = item
    candidates = list(unique.values())

    # Only URLs that were previously auto-added may be removed.
    current_source_urls = {x["url"] for x in candidates if x.get("url")}

    # Remove stale auto blocks, but ONLY blocks containing tracked auto URLs.
    new_blocks = []
    removed = 0
    for block in blocks:
        urls = set(block_urls(block))
        stale_auto = urls & old_auto
        if stale_auto and not (urls - old_auto):
            removed += len(stale_auto)
            continue
        new_blocks.append(block)
    blocks = new_blocks

    # Recompute existing URLs after stale auto removal.
    existing_urls = set()
    for block in blocks:
        existing_urls.update(block_urls(block))

    logo_index = github_logo_index()

    # Candidate URLs that aren't already in TCL.
    new_candidates = [
        x for x in candidates
        if x.get("url") and x["url"] not in existing_urls
    ]

    # Check only new candidates. Previously imported streams are left alone
    # if they are still in the source; stale ones were handled above.
    if CHECK_STREAMS and new_candidates:
        print(
            f"Checking {len(new_candidates)} new streams "
            f"with {CHECK_WORKERS} workers..."
        )
        working = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=CHECK_WORKERS
        ) as pool:
            futures = {
                pool.submit(is_working, item["url"]): item
                for item in new_candidates[:MAX_NEW_STREAMS]
            }
            for future in concurrent.futures.as_completed(futures):
                item = futures[future]
                try:
                    if future.result():
                        working.append(item)
                except Exception:
                    pass
        new_candidates = working
    elif len(new_candidates) > MAX_NEW_STREAMS:
        new_candidates = new_candidates[:MAX_NEW_STREAMS]

    # Deterministic order: country, channel name, URL.
    new_candidates.sort(
        key=lambda x: (
            re.split(r"[;,]", x["attrs"].get("tvg-country", ""))[0].upper(),
            normalize_name(x["name"]),
            x["url"],
        )
    )

    added = 0
    new_auto = set()

    for item in new_candidates:
        url = item["url"]
        if url in existing_urls:
            continue

        extinf = build_extinf(item, logo_index)
        blocks.append([extinf, url])
        existing_urls.add(url)
        new_auto.add(url)
        added += 1

    # Keep old auto URLs only when the URL still exists in IPTV-org AND
    # survived the stale-removal step. Any manually preserved duplicate is
    # deliberately not tracked as auto.
    for url in old_auto & current_source_urls:
        if url in existing_urls:
            new_auto.add(url)

    # Sort ALL entries by country while preserving the order in which
    # countries already occur in the TCL file. New countries are appended.
    #
    # For an entry, first use tvg-country when available. Otherwise infer the
    # country from the leading flag in the display name. This lets manually
    # maintained entries participate in the same country sorting.
    def country_from_block(block: list[str]) -> str:
        for line in block:
            if not line.startswith("#EXTINF:"):
                continue
            attrs = parse_attrs(line)
            countries = attrs.get("tvg-country", "")
            if countries:
                return re.split(r"[;,]", countries)[0].strip().upper()

            name = display_name(line)
            m = re.match(r"^\s*([^\W\d_]{1,2})\s*\|", name, re.UNICODE)
            # Convert regional indicator emoji back to ISO country code.
            emoji = re.match(r"^\s*([\U0001F1E6-\U0001F1FF]{2})\s*\|", name)
            if emoji:
                return "".join(
                    chr(ord(c) - 127397) for c in emoji.group(1)
                ).upper()
            return "ZZ"
        return "ZZ"

    def name_from_block(block: list[str]) -> str:
        for line in block:
            if line.startswith("#EXTINF:"):
                return normalize_name(display_name(line))
        return ""

    # Establish country order from the existing TCL file. This means if the
    # current playlist starts Belgium, Netherlands, France, Germany, that
    # order remains unchanged. Countries never seen before are appended in
    # alphabetical country-code order.
    existing_country_order = []
    seen_countries = set()
    for block in blocks:
        c = country_from_block(block)
        if c not in seen_countries and c != "ZZ":
            existing_country_order.append(c)
            seen_countries.add(c)

    # New automatic entries may introduce new countries.
    all_countries = {country_from_block(b) for b in blocks}
    new_countries = sorted(all_countries - set(existing_country_order) - {"ZZ"})
    country_order = existing_country_order + new_countries

    country_rank = {c: i for i, c in enumerate(country_order)}
    country_rank["ZZ"] = len(country_rank)

    # Sort every actual EXTINF entry. Non-entry header blocks are kept at the
    # beginning. An entry's complete block (EXTINF, URL, EXTHTTP, EXTVLCOPT,
    # etc.) moves together.
    headers = []
    entries = []
    for index, block in enumerate(blocks):
        if any(line.startswith("#EXTINF:") for line in block):
            entries.append((
                country_rank.get(country_from_block(block), len(country_rank)),
                normalize_name(name_from_block(block)),
                index,
                block,
            ))
        else:
            headers.append((index, block))

    entries.sort(key=lambda x: (x[0], x[1], x[2]))

    # Group by country, but do NOT introduce artificial country ordering.
    # Existing countries retain their original relative order.
    sorted_blocks = []
    last_country = None
    for _, _, _, block in entries:
        c = country_from_block(block)
        if c != last_country:
            if sorted_blocks:
                sorted_blocks.append([""])
            label = COUNTRY_NAMES.get(c, c)
            sorted_blocks.append([f"# --- {flag(c)} {label} ---"])
            last_country = c
        sorted_blocks.append(block)

    # Keep non-EXTINF playlist headers/comments at the very top.
    blocks = [b for _, b in headers] + sorted_blocks

    save_state(new_auto)

    result = render_blocks(blocks)
    if result != original.replace("\r\n", "\n").replace("\r", "\n"):
        TCL_FILE.write_text(result, encoding="utf-8")
        print(f"Updated {TCL_FILE}")
    else:
        print("No TCL.m3u content changes.")

    print(f"Added: {added}")
    print(f"Removed stale automatic entries: {removed}")
    print(f"Tracked automatic URLs now: {len(new_auto)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
