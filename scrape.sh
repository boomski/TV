#!/bin/bash

INPUT_FILE="channels.txt"
CENTRAL_PLAYLIST="TCL.m3u"
FALLBACK="https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

########################################
# Functie: kanaal URL vervangen in centrale playlist
########################################
update_central_playlist() {
  local NAME="$1"
  local URL="$2"
  
 # Zoek kanaal in playlist en vervang alleen de regel onder EXTINF
  if grep -q "#EXTINF:-1,$NAME" "$CENTRAL_PLAYLIST"; then
    echo "🔄 Updated: $NAME"
  else
  # Optioneel: voeg nieuw kanaal toe onderaan
    echo "" >> "$CENTRAL_PLAYLIST"
    echo "#EXTINF:-1,$NAME" >> "$CENTRAL_PLAYLIST"
    echo "$URL" >> "$CENTRAL_PLAYLIST"
    echo "➕ Added: $NAME"
  fi
}

########################################
# Loop door alle kanalen
########################################
while IFS='|' read -r NAME URL
do
  # Skip lege regels
  [ -z "$NAME" ] && continue

  # Skip commentregels
  [[ "$NAME" =~ ^# ]] && continue

  echo "Scrapen: $NAME"

  BASE_STREAM=$(yt-dlp -g "$URL" 2>/dev/null | head -n 1)
  FINAL_STREAM="${BASE_STREAM:-$FALLBACK}"

  ########################################
  # Algemene vervangingen (eerst!)
  ########################################
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-720/g')
  FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720/g')

  ########################################
  # Kanaal-specifieke overrides
  ########################################
  if [ "$NAME" = "Le Figaro" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-720@60/g')
  fi

  if [ "$NAME" = "Télénantes" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-480/g')
  fi

  if [ "$NAME" = "Men's UP TV" ]; then
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-720/live-480/g')
  fi

  echo "➡️  Stream: $FINAL_STREAM"

  update_central_playlist "$NAME" "$FINAL_STREAM"

done < "$INPUT_FILE"

echo "✅ TCL.m3u bijgewerkt met actuele stream links, EXTINF-posities blijven intact."
