#!/usr/bin/env bash
# Record the box X display with ffmpeg x11grab.
# Usage: record.sh start [outfile] | stop
set -euo pipefail
PIDFILE=/tmp/mcp-demo-ffmpeg.pid
LOG=/tmp/mcp-demo-ffmpeg.log
OUT="${2:-/workspace/mcp-demo/media/raw/session-raw.mp4}"
DISPLAY_NAME="${DISPLAY:-:5}"

# Detect geometry
GEOM=$(xdpyinfo -display "$DISPLAY_NAME" | awk '/dimensions:/{print $2}')
# Prefer full native resolution (this box is 1920x1200; 1280x800 was the
# expected default). Final video is scaled to 1280x800 in render.sh.
SIZE="${GEOM:-1920x1200}"

start() {
  mkdir -p "$(dirname "$OUT")"
  if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "already recording pid $(cat "$PIDFILE")"
    exit 1
  fi
  # -draw_mouse 1 keeps the pointer; low-latency ultrafast for a long take.
  ffmpeg -y -loglevel info \
    -f x11grab -video_size "$SIZE" -framerate 15 -draw_mouse 1 -i "${DISPLAY_NAME}.0" \
    -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p -crf 23 \
    -movflags +faststart \
    "$OUT" >"$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  echo "recording $SIZE from $DISPLAY_NAME -> $OUT (pid $(cat "$PIDFILE"))"
}

stop() {
  if [[ ! -f "$PIDFILE" ]]; then
    echo "no pidfile"; exit 1
  fi
  pid=$(cat "$PIDFILE")
  if kill -0 "$pid" 2>/dev/null; then
    kill -INT "$pid" || true
    for i in $(seq 1 30); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.3
    done
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" || true
      sleep 1
    fi
  fi
  rm -f "$PIDFILE"
  echo "stopped"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  *) echo "usage: $0 start [outfile] | stop"; exit 2 ;;
esac
