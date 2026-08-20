#!/usr/bin/env python3

from __future__ import annotations

import concurrent.futures
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote

import requests


# ==================================================
# CONFIGURATIE
# ==================================================

ROOT = Path(__file__).resolve().parent

CFG = json.loads(
    (ROOT / "settings.json").read_text(
        encoding="utf-8"
    )
)

SOURCES = json.loads(
    (ROOT / CFG["sources_file"]).read_text(
        encoding="utf-8"
    )
)

PLAYLIST = ROOT / CFG["playlist_file"]

STATE_FILE = ROOT / CFG["state_file"]


SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "TCL-M3U-Generator/1.0"
})


# ==================================================
# HTTP
# ==================================================

def http_get(url, timeout=None, **kwargs):

    return SESSION.get(
        url,
        timeout=timeout or CFG[
            "request_timeout_seconds"
        ],
        **kwargs
    )


# ==================================================
# M3U PARSER
# ==================================================

def parse_attrs(line):

    return dict(
        re.findall(
            r'([\w-]+)="([^"]*)"',
            line
        )
    )


def parse_m3u(text):

    entries = []

    current = None

    lines = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .splitlines()
    )

    for raw in lines:

        line = raw.strip()

        if not line:
            continue

        # Nieuwe EXTINF entry.

        if line.startswith("#EXTINF:"):

            current = {
                "extinf": line,
                "attrs": parse_attrs(line),
                "name": line.rsplit(
                    ",",
                    1
                )[-1].strip(),
                "directives": [],
                "url": None
            }

            continue

        if current is None:
            continue

        # Extra directives bewaren.
        # Bijvoorbeeld EXTVLCOPT.

        if line.startswith("#"):

            current["directives"].append(
                line
            )

        # Stream URL.

        elif re.match(
            r"^https?://",
            line,
            re.I
        ):

            current["url"] = line

            entries.append(
                current
            )

            current = None

    return entries


# ==================================================
# LANDVOLGORDE UIT TCL.M3U
# ==================================================
#
# Het script zoekt bijvoorbeeld:
#
# # --- 🇧🇪 België ---
# # --- 🇳🇱 Nederland ---
# # --- 🇫🇷 Frankrijk ---
#
# De volgorde in TCL.m3u blijft behouden.
# ==================================================

def country_order(text):

    result = []

    for line in text.splitlines():

        line = line.strip()

        for code, data in SOURCES.items():

            flag = data.get("flag")

            name = data.get("name")

            # Header moet vlag én landnaam bevatten.

            if (
                flag
                and name
                and flag in line
                and name.casefold()
                in line.casefold()
            ):

                if code not in result:

                    result.append(
                        code
                    )

                break

    return result


# ==================================================
# AUTO STATE
# ==================================================
#
# Dit bestand wordt automatisch aangemaakt:
#
# .tcl-auto.json
#
# Alles wat daar NIET in staat maar wel in TCL.m3u
# wordt beschouwd als handmatig toegevoegd.
# ==================================================

def load_state():

    if not STATE_FILE.exists():

        return {
            "version": 1,
            "auto": {},
            "failures": {}
        }

    try:

        data = json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

        data.setdefault(
            "auto",
            {}
        )

        data.setdefault(
            "failures",
            {}
        )

        return data

    except Exception:

        return {
            "version": 1,
            "auto": {},
            "failures": {}
        }


def save_state(state):

    STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
            sort_keys=True
        ) + "\n",
        encoding="utf-8"
    )


# ==================================================
# NAAM NORMALISEREN
# ==================================================

def normalize(value):

    value = unquote(
        value or ""
    )

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(
            char
        )
    )

    value = value.casefold()

    return re.sub(
        r"[^a-z0-9]+",
        "",
        value
    )


def clean_name(name):

    name = unquote(
        name or ""
    ).strip()

    # Verwijder bestaande vlag + scheiding.
    #
    # Bijvoorbeeld:
    #
    # 🇧🇪 | VRT 1
    #
    # wordt:
    #
    # VRT 1

    name = re.sub(
        r"^\s*[\U0001F1E6-\U0001F1FF]{2}"
        r"\s*\|\s*",
        "",
        name
    )

    return re.sub(
        r"\s+",
        " ",
        name
    ).strip()


# ==================================================
# LOGO INDEX LADEN
# ==================================================

def load_logo_index():

    try:

        response = http_get(
            CFG["logo_api"],
            timeout=45
        )

        response.raise_for_status()

        tree = response.json().get(
            "tree",
            []
        )

    except Exception as exc:

        print(
            "WARNING: "
            f"logo index unavailable: {exc}"
        )

        return {}

    index = {}

    for item in tree:

        if item.get("type") != "blob":

            continue

        path = item.get(
            "path",
            ""
        )

        if not re.search(
            r"\.(png|jpe?g|webp|svg)$",
            path,
            re.I
        ):

            continue

        key = normalize(
            Path(path).stem
        )

        if (
            key
            and key not in index
        ):

            index[key] = (
                CFG["logo_repo_raw"]
                .rstrip("/")
                + "/"
                + quote(
                    path,
                    safe="/"
                )
            )

    return index


# ==================================================
# LOGO ZOEKEN
# ==================================================
#
# Prioriteit:
#
# 1. Jouw TV-LOGO repository
# 2. tvg-logo uit bron
# 3. Leeg
# ==================================================

def find_logo(
    name,
    source_logo,
    index
):

    key = normalize(
        name
    )

    # Exacte match.

    if key in index:

        return index[key]

    # Varianten zonder HD/FHD/UHD/4K.

    variants = [

        normalize(
            re.sub(
                r"\b(HD|FHD|UHD|4K)\b",
                "",
                name,
                flags=re.I
            )
        ),

        normalize(
            name.replace(
                "&",
                "and"
            )
        )

    ]

    for variant in variants:

        if (
            variant
            and variant in index
        ):

            return index[variant]

    # Geen match in jouw logo repository.
    # Gebruik dan logo uit bron.

    if source_logo:

        return source_logo

    # Anders leeg.

    return ""


# ==================================================
# STREAM CONTROLEREN
# ==================================================

def check_url(url):

    try:

        with SESSION.get(

            url,

            timeout=CFG[
                "check_timeout_seconds"
            ],

            stream=True,

            allow_redirects=True,

            headers={
                "Range": "bytes=0-1023",
                "Accept": "*/*"
            }

        ) as response:

            return (
                200
                <= response.status_code
                < 400
            )

    except requests.RequestException:

        return False


# ==================================================
# BESTAANDE ENTRIES PER URL
# ==================================================

def existing_by_url(text):

    return {

        entry["url"]: entry

        for entry in parse_m3u(text)

        if entry.get("url")

    }


# ==================================================
# AUTOMATISCHE OUTPUT
# ==================================================
#
# Exact gewenst formaat:
#
# #EXTINF:-1 tvg-logo="...",🇧🇪 | Kanaalnaam
# https://stream...
# ==================================================

def render_auto(
    country,
    item,
    logos
):

    name = clean_name(
        item["name"]
    )

    logo = find_logo(
        name,
        item["attrs"].get(
            "tvg-logo",
            ""
        ),
        logos
    )

    lines = [

        f'#EXTINF:-1 tvg-logo="{logo}",'
        f'{country["flag"]} | {name}'

    ]

    # Extra directives behouden.

    lines.extend(
        item.get(
            "directives",
            []
        )
    )

    lines.append(
        item["url"]
    )

    return lines


# ==================================================
# HANDMATIGE OUTPUT
# ==================================================

def render_manual(item):

    return [

        item["extinf"],

        *item.get(
            "directives",
            []
        ),

        item["url"]

    ]


# ==================================================
# HOOFDPROGRAMMA
# ==================================================

def main():

    # ----------------------------------------------
    # TCL.M3U CONTROLEREN
    # ----------------------------------------------

    if not PLAYLIST.exists():

        print(
            "ERROR: TCL.m3u not found"
        )

        return 1


    # ----------------------------------------------
    # BESTAANDE PLAYLIST LEZEN
    # ----------------------------------------------

    template = PLAYLIST.read_text(
        encoding="utf-8-sig"
    )


    # ----------------------------------------------
    # LANDVOLGORDE LEZEN
    # ----------------------------------------------

    order = country_order(
        template
    )


    if not order:

        print(
            "ERROR: no country headers found."
        )

        print(
            'Expected example:'
        )

        print(
            '# --- 🇧🇪 België ---'
        )

        return 1


    # ----------------------------------------------
    # CONTROLEREN OF ALLE LANDEN EEN BRON HEBBEN
    # ----------------------------------------------

    missing = [

        code

        for code in order

        if code not in SOURCES

    ]


    if missing:

        print(
            "ERROR: countries missing "
            "from countries.json:"
        )

        print(
            ", ".join(missing)
        )

        return 1


    # ----------------------------------------------
    # STATE LADEN
    # ----------------------------------------------

    state = load_state()

    old_auto = state["auto"]

    old_failures = state[
        "failures"
    ]


    # ----------------------------------------------
    # BESTAANDE URL'S
    # ----------------------------------------------

    existing = existing_by_url(
        template
    )


    # ----------------------------------------------
    # HANDMATIGE ENTRIES
    # ----------------------------------------------
    #
    # Een entry is handmatig als hij niet in
    # .tcl-auto.json staat.
    #
    # Handmatige entries worden NOOIT verwijderd.
    # ----------------------------------------------

    manual = {

        url: item

        for url, item in existing.items()

        if url not in old_auto

    }


    print()

    print(
        "Country order:"
    )

    print(
        " -> ".join(order)
    )

    print()

    print(
        "Protected manual URLs:",
        len(manual)
    )


    # ----------------------------------------------
    # LOGO INDEX
    # ----------------------------------------------

    logos = load_logo_index()


    # ----------------------------------------------
    # BRONNEN DOWNLOADEN
    # ----------------------------------------------

    incoming = {}


    for code in order:


        source_url = SOURCES[
            code
        ]["source"]


        print()

        print(
            f"Downloading {code}:"
        )

        print(
            source_url
        )


        try:

            response = http_get(
                source_url
            )

            response.raise_for_status()

        except Exception as exc:

            print(
                f"ERROR downloading "
                f"{code}: {exc}"
            )

            # Stoppen.
            #
            # Hierdoor verwijderen we geen
            # bestaande streams wanneer een
            # bron tijdelijk niet bereikbaar is.

            return 1


        entries = parse_m3u(
            response.text
        )


        print(
            f"Parsed entries: "
            f"{len(entries)}"
        )


        for item in entries:


            if not item.get("url"):

                continue


            # Land komt altijd van de bron.

            item["country"] = code


            # Geen dubbele URL's.
            #
            # De eerste gevonden URL wint.

            incoming.setdefault(

                item["url"],

                item

            )


    print()

    print(
        "Unique source URLs:",
        len(incoming)
    )


    # ----------------------------------------------
    # STREAMS CONTROLEREN
    # ----------------------------------------------

    if CFG.get(
        "check_streams",
        True
    ):


        results = {}


        with concurrent.futures.ThreadPoolExecutor(

            max_workers=int(
                CFG.get(
                    "check_workers",
                    20
                )
            )

        ) as pool:


            futures = {

                pool.submit(
                    check_url,
                    url
                ): url

                for url in incoming

            }


            for future in (
                concurrent.futures.as_completed(
                    futures
                )
            ):


                url = futures[
                    future
                ]


                try:

                    results[
                        url
                    ] = future.result()


                except Exception:

                    results[
                        url
                    ] = False


    else:


        results = {

            url: True

            for url in incoming

        }


    # ----------------------------------------------
    # ENTRIES GROEPEREN PER LAND
    # ----------------------------------------------

    grouped = {

        code: []

        for code in order

    }


    extras = []


    # ----------------------------------------------
    # HANDMATIGE ENTRIES TOEVOEGEN
    # ----------------------------------------------

    for url, item in manual.items():


        assigned = None


        # Bepaal land via vlag
        # in de bestaande entry.

        for code in order:


            flag = SOURCES[
                code
            ]["flag"]


            if flag in item["name"]:


                assigned = code

                break


        row = (

            "manual",

            clean_name(
                item["name"]
            ),

            url,

            item

        )


        if assigned:


            grouped[
                assigned
            ].append(
                row
            )


        else:


            extras.append(
                row
            )


    # ----------------------------------------------
    # AUTOMATISCHE ENTRIES
    # ----------------------------------------------

    new_auto = {}

    new_failures = {}


    grace = int(
        CFG.get(
            "failed_checks_before_remove",
            3
        )
    )


    for url, item in incoming.items():


        # ------------------------------------------
        # HANDMATIGE URL HEEFT VOORRANG
        # ------------------------------------------

        if url in manual:

            continue


        # ------------------------------------------
        # STREAM WERKT
        # ------------------------------------------

        if results.get(
            url,
            False
        ):


            new_auto[url] = {

                "country":
                    item["country"],

                "name":
                    clean_name(
                        item["name"]
                    )

            }


            new_failures[
                url
            ] = 0


            grouped[
                item["country"]
            ].append(

                (

                    "auto",

                    clean_name(
                        item["name"]
                    ),

                    url,

                    item

                )

            )


        # ------------------------------------------
        # STREAM WERKT MOMENTEEL NIET
        # ------------------------------------------
        #
        # Alleen bestaande automatische entries
        # krijgen een tijdelijke grace period.
        # ------------------------------------------

        elif url in old_auto:


            failures = (

                int(
                    old_failures.get(
                        url,
                        0
                    )
                )

                + 1

            )


            # Na 3 mislukte runs verwijderen.

            if failures < grace:


                previous = old_auto[
                    url
                ]


                code = previous.get(
                    "country"
                )


                if code in grouped:


                    name = previous.get(
                        "name",
                        url
                    )


                    placeholder = {

                        "name":
                            name,

                        "attrs":
                            {},

                        "directives":
                            [],

                        "url":
                            url

                    }


                    grouped[
                        code
                    ].append(

                        (

                            "auto",

                            name,

                            url,

                            placeholder

                        )

                    )


                    new_auto[
                        url
                    ] = previous


                    new_failures[
                        url
                    ] = failures


    # ----------------------------------------------
    # VERWIJDERDE STREAMS
    # ----------------------------------------------
    #
    # Automatische URL verdwenen uit de bron?
    #
    # Hij komt niet in incoming voor.
    #
    # Hij wordt dus niet in new_auto gezet.
    #
    # Bij het opnieuw opbouwen van TCL.m3u
    # verdwijnt hij automatisch.
    #
    # Handmatige entries worden hierboven
    # altijd behouden.
    # ----------------------------------------------


    # ----------------------------------------------
    # NIEUWE TCL.M3U OPBOUWEN
    # ----------------------------------------------

    output = [

        "#EXTM3U"

    ]


    for code in order:


        country = SOURCES[
            code
        ]


        # ------------------------------------------
        # SORTEREN
        # ------------------------------------------
        #
        # Handmatige en automatische entries
        # worden samen alfabetisch gesorteerd.
        #
        # Landvolgorde zelf blijft zoals in
        # jouw oorspronkelijke TCL.m3u.
        # ------------------------------------------

        grouped[
            code
        ].sort(

            key=lambda row: (

                normalize(
                    row[1]
                ),

                row[2]

            )

        )


        output.append(
            ""
        )


        # Exact jouw landheader-formaat.

        output.append(

            f'# --- '
            f'{country["flag"]} '
            f'{country["name"]} '
            f'---'

        )


        # ------------------------------------------
        # ENTRIES VAN DIT LAND
        # ------------------------------------------

        for (
            kind,
            _,
            _,
            item
        ) in grouped[code]:


            if kind == "manual":


                output.extend(

                    render_manual(
                        item
                    )

                )


            else:


                output.extend(

                    render_auto(

                        country,

                        item,

                        logos

                    )

                )


    # ----------------------------------------------
    # HANDMATIGE ENTRIES ZONDER HERKENBAAR LAND
    # ----------------------------------------------

    if extras:


        extras.sort(

            key=lambda row: (

                normalize(
                    row[1]
                ),

                row[2]

            )

        )


        output.append(
            ""
        )


        output.append(

            "# --- Handmatig / niet toegewezen ---"

        )


        for (
            _,
            _,
            _,
            item
        ) in extras:


            output.extend(

                render_manual(
                    item
                )

            )


    # ----------------------------------------------
    # TCL.M3U OPSLAAN
    # ----------------------------------------------

    PLAYLIST.write_text(

        "\n".join(output).rstrip()
        + "\n",

        encoding="utf-8"

    )


    # ----------------------------------------------
    # STATE OPSLAAN
    # ----------------------------------------------

    state["auto"] = new_auto

    state["failures"] = new_failures


    save_state(
        state
    )


    # ----------------------------------------------
    # RESULTAAT
    # ----------------------------------------------

    print()

    print(
        "Done"
    )

    print(
        "Automatic URLs:",
        len(new_auto)
    )

    print(
        "Manual URLs:",
        len(manual)
    )

    print(
        "Removed automatic URLs:",
        len(
            set(old_auto)
            - set(new_auto)
        )
    )


    return 0


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
