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

    CURRENT_URL=$(sed -n "/#EXTINF:-1,$SAFE_NAME/{n;p;}" "$CENTRAL_PLAYLIST")

    if [ "$CURRENT_URL" = "$URL" ]; then
      echo "⏩ Ongewijzigd: $NAME" >> "$LOG_FILE"
    else
      sed -i "/#EXTINF:-1,$SAFE_NAME/{n;s#.*#$URL#;}" "$CENTRAL_PLAYLIST"
      echo "🔄 Updated: $NAME" >> "$LOG_FILE"
    fi

  else
    echo "⚠️ Niet gevonden in playlist: $NAME" >> "$LOG_FILE"
  fi
}

detect_web_stream() {
  local URL="$1"
  local STREAM=""
  local PAGE

  # Haal pagina op
  PAGE=$(curl -L -s --max-time 15 "$URL")

  # Verzamel alle streams uit HTML
  ALL_STREAMS=$(echo "$PAGE" | grep -Eo 'https://[^"]+\.(m3u8|mpd)')

  # Zoek JSON configs
  JSON_URL=$(echo "$PAGE" | grep -Eo 'https://[^"]+\.json' | head -n1)
  if [ -n "$JSON_URL" ]; then
    JSON_DATA=$(curl -s "$JSON_URL")
    ALL_STREAMS="$ALL_STREAMS"$'\n'"$(echo "$JSON_DATA" | grep -Eo 'https://[^"]+\.(m3u8|mpd)')"
  fi

  # JS scan
  JS_STREAMS=$(echo "$PAGE" | tr '"' '\n' | grep -E '\.(m3u8|mpd)')
  ALL_STREAMS="$ALL_STREAMS"$'\n'"$JS_STREAMS"

  # Verwijder lege regels en duplicaten
  ALL_STREAMS=$(echo "$ALL_STREAMS" | grep -v '^$' | sort -u)

  # 🔎 Beste kwaliteit kiezen
  STREAM=$(echo "$ALL_STREAMS" | grep -Ei '1080|1920x1080' | head -n1)

  if [ -z "$STREAM" ]; then
    STREAM=$(echo "$ALL_STREAMS" | grep -Ei '720|1280x720' | head -n1)
  fi

  if [ -z "$STREAM" ]; then
    STREAM=$(echo "$ALL_STREAMS" | grep -Ei '480|854x480' | head -n1)
  fi

  # Fallback = eerste gevonden
  if [ -z "$STREAM" ]; then
    STREAM=$(echo "$ALL_STREAMS" | head -n1)
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
