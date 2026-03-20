#!/bin/bash

# Input bestand met kanalen
INPUT_FILE="channels.txt"

# Centrale playlist in hoofdmap
CENTRAL_PLAYLIST="TCL.m3u"

# Fallback stream als scraping faalt
FALLBACK="https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

########################################
# Functie: kanaal URL vervangen in centrale playlist
########################################
update_central_playlist() {
  NAME="$1"
  URL="$2"

  # Zoek kanaal in playlist en vervang alleen de regel onder EXTINF
  if grep -q "$NAME" "$CENTRAL_PLAYLIST"; then
    # Vervang de regel direct na EXTINF met de nieuwe URL
    sed -i "/$NAME/{n;s#.*#$URL#;}" "$CENTRAL_PLAYLIST"
  else
    # Voeg nieuw kanaal toe onderaan
    echo "" >> "$CENTRAL_PLAYLIST"
    echo "#EXTINF:-1,$NAME" >> "$CENTRAL_PLAYLIST"
    echo "$URL" >> "$CENTRAL_PLAYLIST"
  fi
}

########################################
# Loop door alle kanalen in yt-dlp_kanaallijst.txt
########################################
while IFS= read -r line
do
  # Skip lege regels of commentaar
  [[ -z "$line" || "$line" =~ ^# ]] && continue

  # Haal naam en URL, URL is alles na de laatste '|'
  NAME=$(echo "$line" | rev | cut -d'|' -f2- | rev | sed 's/ *$//g')  # naam
  URL=$(echo "$line" | rev | cut -d'|' -f1 | rev | sed 's/^ *//g')     # url

  echo "Scrapen: $NAME"

  # Haal de stream op met yt-dlp
  BASE_STREAM=$(yt-dlp -g "$URL" 2>/dev/null | head -n 1)

  # Gebruik fallback als niets gevonden
  FINAL_STREAM="${BASE_STREAM:-$FALLBACK}"

  # Algemene vervangingen
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-720/g')
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720/g')

  # Speciale regels per kanaal
  if [ "$NAME" = "Le Figaro" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-720@60/g')
  fi
  if [ "$NAME" = "Télénantes" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-480/g')
  fi
  if [ "$NAME" = "Men's UP TV" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-480/g')
  fi

  # Update centrale playlist TCL.m3u
  update_central_playlist "$NAME" "$FINAL_STREAM"

done < "$INPUT_FILE"

echo "✅ TCL.m3u bijgewerkt met actuele stream links, handmatige EXTINF-posities blijven intact."
