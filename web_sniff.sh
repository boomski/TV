#!/bin/bash

INPUT_FILE="webpages.txt"
CENTRAL_PLAYLIST="TCL.m3u"
FALLBACK="https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"
LOG_FILE="web_sniff.log"

echo "🕒 $(date) Web sniff gestart" >> "$LOG_FILE"

update_central_playlist() {
  local NAME="$1"
  local URL="$2"

  local SAFE_NAME
  SAFE_NAME=$(printf '%s\n' "$NAME" | sed 's/[\/&]/\\&/g')

  if grep -q "#EXTINF:-1,$NAME" "$CENTRAL_PLAYLIST"; then
    sed -i "/#EXTINF:-1,$SAFE_NAME/{n;s#.*#$URL#;}" "$CENTRAL_PLAYLIST"
    echo "🔄 Updated: $NAME" >> "$LOG_FILE"
  else
    echo "⚠️ Niet gevonden in playlist: $NAME" >> "$LOG_FILE"
  fi
}

detect_web_stream() {
  local URL="$1"
  local STREAM=""
  local PAGE

  PAGE=$(curl -L -s --max-time 15 "$URL")

  STREAM=$(echo "$PAGE" | grep -Eo 'https://[^"]+\.(m3u8|mpd)' | head -n 1)

  if [ -z "$STREAM" ]; then
    JSON_URL=$(echo "$PAGE" | grep -Eo 'https://[^"]+\.json' | head -n 1)
    if [ -n "$JSON_URL" ]; then
      JSON_DATA=$(curl -s "$JSON_URL")
      STREAM=$(echo "$JSON_DATA" | grep -Eo 'https://[^"]+\.(m3u8|mpd)' | head -n 1)
    fi
  fi

  if [ -z "$STREAM" ]; then
    STREAM=$(echo "$PAGE" | tr '"' '\n' | grep -E '\.(m3u8|mpd)' | head -n 1)
  fi

  echo "$STREAM"
}

while IFS='|' read -r NAME URL
do
  [ -z "$NAME" ] && continue
  [[ "$NAME" =~ ^# ]] && continue

  echo "🌐 $NAME scannen" >> "$LOG_FILE"

  BASE_STREAM=$(detect_web_stream "$URL")
  FINAL_STREAM="${BASE_STREAM:-$FALLBACK}"

  echo "➡️ $FINAL_STREAM" >> "$LOG_FILE"

  update_central_playlist "$NAME" "$FINAL_STREAM"

done < "$INPUT_FILE"

echo "✅ $(date) Web sniff klaar" >> "$LOG_FILE"
