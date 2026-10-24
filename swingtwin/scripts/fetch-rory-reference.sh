#!/usr/bin/env bash
# Re-download Rory DTL reference from PGA Tour Brightcove and bake a 3:4 portrait file.
# Concatenates address → takeaway → downswing → finish from the DRIVER-BACK analysis.
set -euo pipefail

PK="BCpkADawqM0vwoTnlGSUgP84xuQaUJJUF2Hp1MT2MbyDvrD8DfnRNr57b3W-SnGPIUswIm1LLqO6pEdQf6lVX8bADNuaxAT-Lodzt2GSUUZRoUQMsUfgTuy1NYQxkKwXKRfSmCdrRF-dmXGa"
ACC="6082840763001"
VID="6314012785112"
OUT_DIR="$(cd "$(dirname "$0")/../public/reference" && pwd)"
TMP="$(mktemp /tmp/rory-full.XXXXXX.mp4)"
PARTS="$(mktemp -d /tmp/rory-parts.XXXXXX)"
VF="crop=360:480:250:220,scale=540:720"

curl -fsSL \
  "https://edge.api.brightcove.com/playback/v1/accounts/${ACC}/videos/${VID}" \
  -H "Accept: application/json;pk=${PK}" \
  | python3 -c "
import json, sys, subprocess
d=json.load(sys.stdin)
mp4=[s for s in d['sources'] if s.get('container')=='MP4' and s.get('height')==720]
url=sorted(mp4,key=lambda s:s.get('size',0),reverse=True)[0]['src']
subprocess.run(['curl','-fsSL',url,'-o','${TMP}'], check=True)
"

encode_part() {
  local start="$1" dur="$2" out="$3"
  ffmpeg -y -ss "$start" -t "$dur" -i "$TMP" \
    -vf "$VF" -an -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -r 30 \
    "$out"
}

encode_part 60.5 2.8 "${PARTS}/01-addr.mp4"
encode_part 90.0 3.2 "${PARTS}/02-take.mp4"
encode_part 115.6 10.4 "${PARTS}/03-swing.mp4"
encode_part 214.0 3.2 "${PARTS}/04-finish.mp4"

cat > "${PARTS}/list.txt" << EOF
file '${PARTS}/01-addr.mp4'
file '${PARTS}/02-take.mp4'
file '${PARTS}/03-swing.mp4'
file '${PARTS}/04-finish.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i "${PARTS}/list.txt" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart \
  "${OUT_DIR}/rory-mcilroy-dtl.mp4"

ffmpeg -y -ss 0.4 -i "${OUT_DIR}/rory-mcilroy-dtl.mp4" -frames:v 1 -q:v 3 \
  "${OUT_DIR}/rory-mcilroy-dtl.jpg"

rm -rf "$TMP" "$PARTS"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 \
  "${OUT_DIR}/rory-mcilroy-dtl.mp4"
echo "Wrote ${OUT_DIR}/rory-mcilroy-dtl.mp4"
