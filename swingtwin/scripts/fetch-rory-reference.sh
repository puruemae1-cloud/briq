#!/usr/bin/env bash
# Re-download Rory DTL reference from PGA Tour Brightcove (Swing Theory driver segment).
set -euo pipefail

PK="BCpkADawqM0vwoTnlGSUgP84xuQaUJJUF2Hp1MT2MbyDvrD8DfnRNr57b3W-SnGPIUswIm1LLqO6pEdQf6lVX8bADNuaxAT-Lodzt2GSUUZRoUQMsUfgTuy1NYQxkKwXKRfSmCdrRF-dmXGa"
ACC="6082840763001"
VID="6314012785112"
OUT_DIR="$(cd "$(dirname "$0")/../public/reference" && pwd)"
TMP="$(mktemp /tmp/rory-full.XXXXXX.mp4)"

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

ffmpeg -y -ss 117.2 -t 6.8 -i "$TMP" \
  -an -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -movflags +faststart \
  "${OUT_DIR}/rory-mcilroy-dtl.mp4"

rm -f "$TMP"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 \
  "${OUT_DIR}/rory-mcilroy-dtl.mp4"
echo "Wrote ${OUT_DIR}/rory-mcilroy-dtl.mp4"
