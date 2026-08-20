#!/usr/bin/env bash

# ==================================================
# INSTELLINGEN
# ==================================================

# Input bestand met kanalen
INPUT_FILE="channels.txt"

# Centrale playlist in hoofdmap
CENTRAL_PLAYLIST="TCL.m3u"

# Fallback stream als yt-dlp niets vindt
FALLBACK="https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ==================================================
# CONTROLE
# ==================================================

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "❌ Bestand niet gevonden: $INPUT_FILE"
    exit 1
fi

if [[ ! -f "$CENTRAL_PLAYLIST" ]]; then
    echo "❌ Bestand niet gevonden: $CENTRAL_PLAYLIST"
    exit 1
fi


# ==================================================
# FUNCTIE:
# ZOEK EXACT KANAAL EN VERVANG ALLEEN ZIJN URL
# ==================================================

update_central_playlist() {

    NAME="$1"
    URL="$2"

    TEMP_FILE=$(mktemp)

    NAME="$NAME" \
    URL="$URL" \
    CENTRAL_PLAYLIST="$CENTRAL_PLAYLIST" \
    python3 << 'PYTHON' > "$TEMP_FILE"

import os

name = os.environ["NAME"]
new_url = os.environ["URL"]
playlist = os.environ["CENTRAL_PLAYLIST"]


with open(
    playlist,
    "r",
    encoding="utf-8"
) as file:

    lines = file.readlines()


found = False


# ==========================================
# LOOP DOOR BESTAANDE PLAYLIST
# ==========================================

i = 0

while i < len(lines):

    line = lines[i]

    # Alleen EXTINF-regels controleren

    if line.startswith("#EXTINF:"):

        # Alles na de laatste komma is de kanaalnaam

        channel_name = (
            line
            .rstrip("\r\n")
            .rsplit(",", 1)[-1]
            .strip()
        )


        # Exacte kanaalnaam gevonden

        if channel_name == name:

            found = True

            # Zoek de eerste URL onder deze EXTINF

            j = i + 1

            while j < len(lines):

                candidate = lines[j].strip()


                # Stop bij een volgende EXTINF

                if candidate.startswith("#EXTINF:"):
                    break


                # Stop bij een landheader
                #
                # Hierdoor kan het script nooit
                # naar het volgende land springen.

                if (
                    candidate.startswith("# ---")
                    and candidate.endswith("---")
                ):
                    break


                # Eerste URL gevonden:
                # alleen deze regel vervangen

                if (
                    candidate.startswith("http://")
                    or candidate.startswith("https://")
                ):

                    lines[j] = new_url + "\n"

                    break


                j += 1

            break

    i += 1


# ==========================================
# BESTAAND KANAAL
# ==========================================

if found:

    # Alles blijft exact hetzelfde,
    # behalve de vervangen URL.

    print(
        "".join(lines),
        end=""
    )


# ==========================================
# NIEUW KANAAL
# ==========================================

else:

    # Bestaande playlist volledig behouden

    print(
        "".join(lines),
        end=""
    )

    # Zorg voor een lege regel

    if lines and lines[-1].strip():

        print()


    # Nieuw kanaal onderaan toevoegen

    print(
        f"#EXTINF:-1,{name}"
    )

    print(
        new_url
    )

PYTHON


    # Alleen vervangen als de verwerking gelukt is

    if [[ $? -eq 0 ]]; then

        mv "$TEMP_FILE" "$CENTRAL_PLAYLIST"

        echo "   ✓ Playlist bijgewerkt"

    else

        echo "   ❌ Fout bij: $NAME"

        rm -f "$TEMP_FILE"

        return 1
    fi
}


# ==================================================
# LOOP DOOR CHANNELS.TXT
# ==================================================

while IFS= read -r line || [[ -n "$line" ]]
do

    # ----------------------------------------------
    # LEGE REGELS OVERSLAAN
    # ----------------------------------------------

    [[ -z "${line//[[:space:]]/}" ]] && continue


    # ----------------------------------------------
    # COMMENTAAR OVERSLAAN
    # ----------------------------------------------

    [[ "$line" =~ ^[[:space:]]*# ]] && continue


    # ----------------------------------------------
    # CONTROLEREN OF ER EEN | IS
    # ----------------------------------------------

    if [[ "$line" != *"|"* ]]; then

        echo "⚠️ Ongeldige regel overgeslagen:"

        echo "$line"

        continue
    fi


    # ==================================================
    # NAAM EN URL SPLITSEN OP LAATSTE |
    # ==================================================
    #
    # Voorbeeld:
    #
    # 🇫🇷 | Le Figaro | https://youtube.com/...
    #
    # NAME:
    #
    # 🇫🇷 | Le Figaro
    #
    # URL:
    #
    # https://youtube.com/...
    # ==================================================

    NAME="${line%|*}"

    URL="${line##*|}"


    # Spaties voor en achter verwijderen

    NAME=$(
        echo "$NAME" |
        sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
    )

    URL=$(
        echo "$URL" |
        sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
    )


    # ----------------------------------------------
    # ONGELDIGE REGELS OVERSLAAN
    # ----------------------------------------------

    if [[ -z "$NAME" || -z "$URL" ]]; then

        echo "⚠️ Ongeldige regel overgeslagen:"

        echo "$line"

        continue
    fi


    # ==================================================
    # STREAM OPHALEN
    # ==================================================

    echo

    echo "Scrapen: $NAME"


    BASE_STREAM=$(
        yt-dlp \
            -g \
            "$URL" \
            2>/dev/null |
        head -n 1
    )


    # ==================================================
    # FALLBACK
    # ==================================================

    if [[ -z "$BASE_STREAM" ]]; then

        echo "   ⚠️ Geen stream gevonden"

        echo "   ↳ Fallback gebruikt"

        FINAL_STREAM="$FALLBACK"

    else

        echo "   ✓ Stream gevonden"

        FINAL_STREAM="$BASE_STREAM"

    fi


    # ==================================================
    # ALGEMENE URL AANPASSINGEN
    # ==================================================

    FINAL_STREAM=$(
        echo "$FINAL_STREAM" |
        sed 's/live-240/live-720/g'
    )

    FINAL_STREAM=$(
        echo "$FINAL_STREAM" |
        sed 's/live-380/live-720/g'
    )


    # ==================================================
    # SPECIALE REGELS PER KANAAL
    # ==================================================

    case "$NAME" in

        "🇫🇷 | Le Figaro")

            FINAL_STREAM=$(
                echo "$FINAL_STREAM" |
                sed 's/live-720/live-720@60/g'
            )

            ;;


        "🇫🇷 | Télénantes")

            FINAL_STREAM=$(
                echo "$FINAL_STREAM" |
                sed 's/live-720/live-480/g'
            )

            ;;


        "🇫🇷 | Men's UP TV")

            FINAL_STREAM=$(
                echo "$FINAL_STREAM" |
                sed 's/live-720/live-480/g'
            )

            ;;

    esac


    # ==================================================
    # CENTRALE PLAYLIST UPDATEN
    # ==================================================
    #
    # Alleen de URL wordt aangepast.
    #
    # Landheaders worden nooit verwijderd.
    # Andere entries worden nooit verwijderd.
    # Volgorde wordt nooit gewijzigd.
    # ==================================================

    update_central_playlist \
        "$NAME" \
        "$FINAL_STREAM"


done < "$INPUT_FILE"


# ==================================================
# KLAAR
# ==================================================

echo
echo "=============================================="
echo "✅ TCL.m3u succesvol bijgewerkt"
echo "=============================================="

echo
echo "Dit script heeft:"
echo "• Landheaders behouden"
echo "• Lege landen behouden"
echo "• De bestaande volgorde behouden"
echo "• Alleen bestaande kanaal-URL's vervangen"
echo "• Nieuwe kanalen alleen onderaan toegevoegd"
echo "• Geen andere streams verwijderd"
