#!/bin/bash

# Input bestand met kanalen
INPUT_FILE="channels.txt"

# Centrale playlist in hoofdmap
CENTRAL_PLAYLIST="TCL.m3u"

# Fallback stream als scraping faalt
FALLBACK="https://raw.githubusercontent.com/USERNAME/AUTOTV/main/assets/moose_na.m3u"

########################################
# Functie: kanaal URL vervangen in centrale playlist
########################################
update_central_playlist() {
  NAME="$1"
  URL="$2"

  # Zoek kanaal in playlist en vervang alleen de regel onder EXTINF
  if grep -q "$NAME" "$CENTRAL_PLAYLIST"; then
    sed -i "/$NAME/{n;s#.*#$URL#;}" "$CENTRAL_PLAYLIST"
  else
    # Optioneel: voeg nieuw kanaal toe onderaan
    echo "" >> "$CENTRAL_PLAYLIST"
    echo "#EXTINF:-1,$NAME" >> "$CENTRAL_PLAYLIST"
    echo "$URL" >> "$CENTRAL_PLAYLIST"
  fi
}

########################################
# Loop door alle kanalen in channels.txt
########################################
while IFS='|' read -r NAME URL
do
  echo "Scrapen: $NAME"

  # Haal de stream op met yt-dlp
  BASE_STREAM=$(yt-dlp -g "$URL" 2>/dev/null | head -n 1)

  # Gebruik fallback als niets gevonden
  FINAL_STREAM="${BASE_STREAM:-$FALLBACK}"

  # Speciale regels per kanaal
  if [ "$NAME" = "Le Figaro" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720@60/g')
  fi
  if [ "$NAME" = "Télénantes" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-480/g')
  fi

  # Algemene vervangingen
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-720/g')
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720/g')

  # Update centrale playlist TCL.m3u
  update_central_playlist "$NAME" "$FINAL_STREAM"

done < "$INPUT_FILE"

echo "✅ TCL.m3u bijgewerkt met actuele stream links, handmatige EXTINF-posities blijven intact."
