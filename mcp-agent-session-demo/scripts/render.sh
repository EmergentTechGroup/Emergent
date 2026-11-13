#!/usr/bin/env bash
# Render demo.mp4 and poster.png from raw/session-raw.mp4 and logs/steps.json.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/render.py
