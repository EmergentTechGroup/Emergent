#!/usr/bin/env bash
# Build media/preview.gif from media/demo.mp4 with a two-pass ffmpeg palettegen.
# 12× speed, 8 fps, 720 px wide — keeps the file well under GitHub's 10 MB image limit.
set -euo pipefail
cd "$(dirname "$0")/.."
IN="${1:-media/demo.mp4}"
OUT="${2:-media/preview.gif}"
PALETTE="$(mktemp --suffix=.png)"
cleanup() { rm -f "$PALETTE"; }
trap cleanup EXIT

# Pass 1: build an optimal palette from the sped-up frames.
ffmpeg -y -i "$IN" \
  -vf "setpts=PTS/12,fps=8,scale=720:-1:flags=lanczos,palettegen=stats_mode=diff:max_colors=128" \
  -update 1 "$PALETTE"

# Pass 2: apply the palette with bayer dithering.
ffmpeg -y -i "$IN" -i "$PALETTE" \
  -filter_complex "[0:v]setpts=PTS/12,fps=8,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
  -loop 0 "$OUT"

echo "wrote $OUT ($(wc -c < "$OUT") bytes)"
