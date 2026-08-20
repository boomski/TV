import subprocess
import json
import time
from urllib.parse import urlparse


# ==================================================
# INSTELLINGEN
# ==================================================

M3U_FILE = "TCL.m3u"
INPUT_FILE = "yt-dlp_kanaallijst.txt"

USER_AGENT = (
    "#EXTVLCOPT:http-user-agent="
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
)


# ==================================================
# 🔄 UPDATE YT-DLP
# ==================================================

def update_ytdlp():

    print("🔄 yt-dlp updaten...")

    try:

        subprocess.run(
            ["yt-dlp", "-U"],
            capture_output=True,
            text=True
        )

    except Exception as e:

        print("⚠️ Update mislukt:", e)


# ==================================================
# 🌍 REFERER OPHALEN
# ==================================================

def get_referer(page_url):

    try:

        p = urlparse(page_url)

        return (
            f"{p.scheme}://"
            f"{p.netloc}"
            f"{p.path}"
        )

    except Exception:

        return page_url


# ==================================================
# 🛑 CONTROLEREN OF EEN REGEL EEN LANDHEADER IS
# ==================================================
#
# Voorbeeld:
#
# # --- 🇧🇪 België ---
#
# Deze headers mogen NOOIT verwijderd worden.
# ==================================================

def is_country_header(line):

    stripped = line.strip()

    return (
        stripped.startswith("# ---")
        and stripped.endswith("---")
    )


# ==================================================
# 🎯 ULTRA ROBUUSTE STREAM FETCH
# ==================================================

def get_stream(page_url, retries=3):

    for attempt in range(retries):

        print(
            f"⏳ Sniffen "
            f"({attempt + 1}/{retries}): "
            f"{page_url}"
        )

        try:

            result = subprocess.run(
                [
                    "yt-dlp",
                    "-J",
                    "--no-warnings",
                    "--user-agent",
                    "Mozilla/5.0",
                    page_url
                ],
                capture_output=True,
                text=True,
                timeout=30
            )


            # ------------------------------------------
            # GEEN OUTPUT
            # ------------------------------------------

            if not result.stdout:

                print("❌ Lege output")

                time.sleep(2)

                continue


            data = json.loads(
                result.stdout
            )


            # ------------------------------------------
            # DIRECTE URL
            # ------------------------------------------

            if "url" in data:

                u = data["url"]

                if (
                    u
                    and "m3u8" in u
                ):

                    print(
                        "🎯 Directe m3u8"
                    )

                    return u


            # ------------------------------------------
            # FORMATEN
            # ------------------------------------------

            formats = data.get(
                "formats",
                []
            )


            # Sorteer op hoogste hoogte

            formats = sorted(
                formats,
                key=lambda x: (
                    x.get("height") or 0
                ),
                reverse=True
            )


            # ------------------------------------------
            # CHUNKLIST EERST
            # ------------------------------------------

            for f in formats:

                u = f.get("url")

                if (
                    u
                    and "chunklist.m3u8" in u
                ):

                    print(
                        "🎯 Chunklist gevonden"
                    )

                    return u


            # ------------------------------------------
            # FALLBACK M3U8
            # ------------------------------------------

            for f in formats:

                u = f.get("url")

                if (
                    u
                    and "m3u8" in u
                ):

                    print(
                        "⚠️ Fallback m3u8"
                    )

                    return u


            print(
                "❌ Geen m3u8 gevonden"
            )


        except Exception as e:

            print(
                "❌ Fout:",
                e
            )


        time.sleep(2)


    return None


# ==================================================
# 🔍 EXACT KANAAL ZOEKEN
# ==================================================

def get_channel_name_from_extinf(line):

    """
    Haalt alleen de zichtbare kanaalnaam
    uit een EXTINF-regel.

    Voorbeeld:

    #EXTINF:-1 tvg-logo="...",🇫🇷 | Le Figaro

    wordt:

    🇫🇷 | Le Figaro
    """

    stripped = line.strip()


    if not stripped.startswith("#EXTINF"):
        return None


    if "," not in stripped:
        return None


    return (
        stripped
        .rsplit(",", 1)[-1]
        .strip()
    )


# ==================================================
# 🔥 VEILIGE KANAAL UPDATE
# ==================================================
#
# BELANGRIJK:
#
# Stopt bij:
#
# - volgende #EXTINF
# - volgende landheader
#
# Daardoor kunnen lege landen nooit verdwijnen.
# ==================================================

def update_channel(
    lines,
    name,
    new_url,
    referer
):


    # ----------------------------------------------
    # URL CONTROLEREN
    # ----------------------------------------------

    if (
        not new_url
        or not new_url.startswith("http")
    ):

        print(
            "❌ Ongeldige URL → "
            "update overgeslagen"
        )

        return False


    # ----------------------------------------------
    # EXACTE KANAALNAAM
    # ----------------------------------------------

    target_name = name.strip()


    i = 0


    while i < len(lines):


        current_line = lines[i]


        # Alleen EXTINF vergelijken

        if current_line.startswith("#EXTINF"):


            current_name = (
                get_channel_name_from_extinf(
                    current_line
                )
            )


            # --------------------------------------
            # ALLEEN EXACTE MATCH
            # --------------------------------------

            if current_name == target_name:


                print(
                    f"🎯 Exacte match: "
                    f"{target_name}"
                )


                # ----------------------------------
                # EINDE VAN HET KANAALBLOK ZOEKEN
                # ----------------------------------
                #
                # Stop bij:
                #
                # 1. volgende EXTINF
                # 2. landheader
                #
                # De landheaders blijven dus staan.
                # ----------------------------------

                j = i + 1


                while j < len(lines):


                    candidate = (
                        lines[j].strip()
                    )


                    # ------------------------------
                    # VOLGENDE KANAAL
                    # ------------------------------

                    if candidate.startswith(
                        "#EXTINF"
                    ):

                        break


                    # ------------------------------
                    # VOLGEND LAND
                    # ------------------------------
                    #
                    # HIER ZAT DE FOUT
                    # IN JE OUDE SCRIPT.
                    #
                    # Deze break voorkomt dat:
                    #
                    # # --- 🇲🇰 Noord-Macedonië ---
                    #
                    # wordt verwijderd.
                    # ------------------------------

                    if is_country_header(
                        candidate
                    ):

                        break


                    j += 1


                # ----------------------------------
                # NIEUW BLOK
                # ----------------------------------
                #
                # EXTINF blijft onaangeraakt.
                #
                # Alleen de regels ONDER EXTINF
                # worden vervangen.
                # ----------------------------------

                new_block = [

                    USER_AGENT,

                    (
                        "#EXTVLCOPT:http-referrer="
                        f"{referer}"
                    ),

                    new_url

                ]


                # ----------------------------------
                # OUDE STREAMBLOK VERVANGEN
                # ----------------------------------
                #
                # i+1 tot j
                #
                # Landheaders worden niet meegenomen
                # omdat j ervoor stopt.
                # ----------------------------------

                lines[i + 1:j] = [

                    line + "\n"
                    for line in new_block

                ]


                print(
                    "🔁 Streamblok veilig "
                    "geüpdatet"
                )


                return True


        i += 1


    print(
        f"❌ Geen exacte match voor: "
        f"{target_name}"
    )


    return False


# ==================================================
# 🚀 MAIN
# ==================================================

def main():


    # ----------------------------------------------
    # YT-DLP UPDATEN
    # ----------------------------------------------

    update_ytdlp()


    # ----------------------------------------------
    # TCL.M3U INLADEN
    # ----------------------------------------------

    with open(
        M3U_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        lines = f.readlines()


    # ----------------------------------------------
    # KANALENLIJST INLADEN
    # ----------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        channels = f.readlines()


    updated_any = False


    # ==============================================
    # ALLE KANALEN VERWERKEN
    # ==============================================

    for ch in channels:


        ch = ch.strip()


        # ------------------------------------------
        # LEGE OF ONGELDIGE REGEL
        # ------------------------------------------

        if (
            not ch
            or "|" not in ch
        ):

            continue


        # ------------------------------------------
        # SPLITS OP LAATSTE |
        # ------------------------------------------
        #
        # Bijvoorbeeld:
        #
        # 🇫🇷 | Le Figaro | https://...
        #
        # Dit wordt:
        #
        # name = 🇫🇷 | Le Figaro
        # url  = https://...
        # ------------------------------------------

        name, url = ch.rsplit(
            "|",
            1
        )


        name = name.strip()

        url = url.strip()


        print(
            "\n======================"
        )

        print(
            "📺",
            name
        )


        # ------------------------------------------
        # STREAM ZOEKEN
        # ------------------------------------------

        stream = get_stream(
            url
        )


        # ------------------------------------------
        # ALLEEN UPDATEN BIJ GELDIGE STREAM
        # ------------------------------------------

        if (
            stream
            and stream.startswith("http")
        ):


            referer = get_referer(
                url
            )


            if update_channel(
                lines,
                name,
                stream,
                referer
            ):

                updated_any = True


        else:

            print(
                "❌ Geen geldige stream "
                "→ niets aangepast"
            )


    # ==============================================
    # PLAYLIST OPSLAAN
    # ==============================================

    if updated_any:


        with open(
            M3U_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            f.writelines(
                lines
            )


        print(
            "\n💾 TCL.m3u veilig geüpdatet"
        )


    else:

        print(
            "\n⚠️ Geen wijzigingen"
        )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    main()
