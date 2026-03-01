#!/bin/bash

INPUT_FILE="channels.txt"
OUTPUT_DIR="outputs"
FALLBACK="https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

mkdir -p "$OUTPUT_DIR"

while IFS='|' read -r NAME URL
do
  echo "Scrapen: $NAME"

  BASE_STREAM=$(yt-dlp -g "$URL" 2>/dev/null | head -n 1)

  if [ -z "$BASE_STREAM" ]; then
    FINAL_STREAM="${FALLBACK}${HEADERS}"
  else
    FINAL_STREAM="$BASE_STREAM"

    # 🔹 Speciale regel voor Le Figaro
    if [ "$NAME" = "Le Figaro" ]; then
      FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720@60/g')
    fi

    # 🔹 Speciale regel voor Télénantes
    if [ "$NAME" = "Télénantes" ]; then
      FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-480/g')
    fi

    # 🔹 Algemene regel voor alle kanalen
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-240/live-720/g')
    FINAL_STREAM=$(echo "$FINAL_STREAM" | sed 's/live-380/live-720/g')

    # 🔹 Headers toevoegen
    FINAL_STREAM="${FINAL_STREAM}${HEADERS}"
  fi

  OUTPUT_FILE="$OUTPUT_DIR/$NAME.m3u8"

  # 🔥 BELANGRIJK: overschrijf file i.p.v. append
  echo "$FINAL_STREAM" > "$OUTPUT_FILE"

done < "$INPUT_FILE"
