#!/bin/bash

# Input bestand met kanalen
INPUT_FILE="channels.txt"

# Output map voor losse kanaalbestanden
OUTPUT_DIR="outputs"
mkdir -p "$OUTPUT_DIR"

# Fallback stream als scraping faalt
FALLBACK="https://raw.githubusercontent.com/USERNAME/AUTOTV/main/assets/moose_na.m3u"

# Centrale playlist staat in de hoofdmap
CENTRAL_PLAYLIST="TCL.m3u"

########################################
# Functie: kanaal URL vervangen of toevoegen
########################################
update_central_playlist() {
  NAME="$1"
  URL="$2"

  # Controleer of kanaal al bestaat in playlist
  if grep -q "$NAME" "$CENTRAL_PLAYLIST"; then
    # Vervang alleen de regel direct onder de EXTINF
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

  # Schrijf individuele kanaal .m3u8 file in outputs
  echo "$FINAL_STREAM" > "$OUTPUT_DIR/$NAME.m3u8"

  # Update centrale playlist TCL.m3u in hoofdmap
  update_central_playlist "$NAME" "$FINAL_STREAM"

done < "$INPUT_FILE"

echo "✅ TCL.m3u bijgewerkt met actuele stream links, handmatige EXTINF-posities blijven intact."
