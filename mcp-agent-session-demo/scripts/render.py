#!/usr/bin/env python3
"""
Render media/demo.mp4 from the raw x11grab recording
and the real step log. Captions are taken only from recorded results.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path("/workspace/mcp-demo")
MEDIA = ROOT / "media"
ASSETS = MEDIA
CAPTIONS = MEDIA / "captions"
RAW = MEDIA / "raw" / "session-raw.mp4"
LOG = ROOT / "logs" / "steps.json"
DEMO = MEDIA / "demo.mp4"
POSTER = MEDIA / "poster.png"
WORK = Path("/tmp/mcp-demo-render")

W, H = 1280, 800
FPS = 30
TZ = ZoneInfo("America/New_York")
# Exact x11grab start from the ffmpeg log (STREAM start timestamp).
REC_START = datetime(2026, 11, 13, 12, 12, 54, 333529, tzinfo=TZ)

BG = (11, 16, 32, 255)
INK = (232, 237, 248, 255)
MUTED = (139, 151, 184, 255)
ACCENT = (129, 140, 248, 255)
OK = (52, 211, 153, 255)
LINE = (36, 48, 86, 255)

FONTS = {
    "outfit": "/usr/share/fonts/truetype/sand-box/google/Outfit/Outfit-VariableFont_wght.ttf",
    "ibm": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Sans/IBMPlexSans-VariableFont_wdth,wght.ttf",
    "mono": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-Regular.ttf",
    "monomed": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-Medium.ttf",
}

# Short, factual captions taken from the live step log (no invented data).
CAPTION_TEXT = {
    0: ("SESSION", "Live dashboard is up · four connectors ready · read-only policy in effect"),
    1: ("GITHUB  ·  get_me", "Connected as EmergentTechGroup · 1 public repository · email not present"),
    2: ("GITHUB  ·  list_my_repositories", "1 public repo: EmergentTechGroup/Emergent · visibility public · 0 stars"),
    3: ("GITHUB  ·  search_repositories", "5,620 public MCP repos · top: python-sdk 24,848 stars, mcp-for-beginners 17,644 stars"),
    4: ("GITHUB  ·  get_repository", "modelcontextprotocol/python-sdk · Python, MIT, 24,848 stars, 4,124 forks"),
    5: ("GITHUB  ·  get_file_contents", "README: official Python MCP SDK · Python 3.11+ · uv add \"mcp[cli]\" · MIT"),
    6: ("GITHUB  ·  get_latest_release", "Latest release v2.3.0 · published 2026-10-02 6:02 PM EDT · mostly fixes"),
    7: ("X  ·  get_trends_by_woeid", "15 worldwide trends · including Friday the 13th, Microsoft, ChatGPT Wallet"),
    8: ("X  ·  search_news", "5 AI-agent stories · coding harnesses, Coinbase CEO workflow, trading scores"),
    9: ("X  ·  get_users_by_username", "@github · 2,738,534 followers · verified business · 11,071 posts"),
    10: ("X  ·  get_posts_counts_recent", "74,791 original MCP posts in 7 days · peak 12,911 on 11 Nov 2026 (UTC)"),
    11: ("EULER  ·  euler_help", "3 public help articles on submitting a referral · portal and Slack /referral"),
    12: ("EULER  ·  ping", "pong=true, echo matched · authenticated partner-scoped Cursor client · IDs omitted"),
    13: ("ORIGIN  ·  list_namespaces", "1 team namespace visible · slug and id omitted · create capability unused"),
    14: ("ORIGIN  ·  list_repositories", "0 repositories in that namespace · get_repository skipped · nothing created"),
    15: ("COMPLETE", "14 of 14 steps succeeded · 0 writes on any connector · no remote repo created"),
}


def font(family: str, size: int, variation: str | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONTS[family], size)
    if variation and hasattr(f, "set_variation_by_name"):
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    return f


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s.replace(" EST", "").replace(" EDT", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def offset(s: str) -> float:
    return (parse_ts(s) - REC_START).total_seconds()


def rounded_rect(draw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def paint_bg(im: Image.Image):
    """Dark radial-ish background matching the live dashboard."""
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            # two soft glows
            dx1 = (x - 160) / 700
            dy1 = (y + 80) / 500
            g1 = max(0.0, 1.0 - (dx1 * dx1 + dy1 * dy1))
            dx2 = (x - 1180) / 600
            dy2 = (y - 80) / 450
            g2 = max(0.0, 1.0 - (dx2 * dx2 + dy2 * dy2))
            r = int(11 + 18 * g1 + 6 * g2)
            g = int(16 + 16 * g1 + 22 * g2)
            b = int(32 + 36 * g1 + 14 * g2)
            px[x, y] = (min(r, 40), min(g, 55), min(b, 80), 255)


def make_title() -> Image.Image:
    im = Image.new("RGBA", (W, H), BG)
    paint_bg(im)
    d = ImageDraw.Draw(im)
    kicker = font("ibm", 18, "Medium")
    title = font("outfit", 72, "SemiBold")
    sub = font("ibm", 26, "Regular")
    pill = font("ibm", 16, "Medium")
    foot = font("mono", 16)

    d.text((80, 150), "READ-ONLY MCP WALKTHROUGH", font=kicker, fill=ACCENT)
    d.text((80, 200), "MCP Agent Session Demo", font=title, fill=INK)
    d.text(
        (80, 300),
        "A long-running agent session across four connected MCP connectors.\n"
        "Every call in this recording is a read. Nothing was posted, opened,\n"
        "commented on, or written, and no remote GitHub repository was created.",
        font=sub,
        fill=MUTED,
        spacing=8,
    )

    pills = [
        ("cursor-github", "READY", (88, 166, 255), (16, 28, 52, 255)),
        ("x", "READY", (17, 17, 17, 255), (231, 233, 234, 255)),
        ("user-Euler", "READY", (94, 234, 212), (12, 40, 38, 255)),
        ("cursor-origin", "READY", (196, 181, 253), (32, 26, 52, 255)),
    ]
    x = 80
    for name, st, fg, bg in pills:
        label = f"{name}  ·  {st}"
        bbox = d.textbbox((0, 0), label, font=pill)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        rounded_rect(d, (x, 470, x + tw + 36, 470 + th + 20), 16, bg, fg[:3] + (255,), 2)
        d.text((x + 18, 478), label, font=pill, fill=fg)
        x += tw + 48

    d.text((80, 700), "Friday 13 November 2026  ·  America/New_York  ·  14 steps  ·  0 writes", font=foot, fill=MUTED)
    return im


def make_end() -> Image.Image:
    im = Image.new("RGBA", (W, H), BG)
    paint_bg(im)
    d = ImageDraw.Draw(im)
    kicker = font("ibm", 18, "Medium")
    title = font("outfit", 64, "SemiBold")
    body = font("ibm", 24, "Regular")
    mono = font("monomed", 20)
    foot = font("mono", 16)

    d.text((80, 120), "SESSION COMPLETE", font=kicker, fill=OK)
    d.text((80, 165), "14 of 14 steps succeeded", font=title, fill=INK)

    facts = [
        ("Connectors used", "GitHub, X, Euler, Origin  —  all four were ready"),
        ("GitHub", "EmergentTechGroup · python-sdk 24,848 stars · latest release v2.3.0"),
        ("X", "Worldwide trends + 74,791 MCP posts in 7 days · @github 2.74M followers"),
        ("Euler", "3 public help articles on referrals · ping returned pong=true"),
        ("Origin", "1 team namespace · 0 repositories (none created)"),
        ("Policy", "Writes issued: 0    Remote repo created: no"),
    ]
    y = 280
    for k, v in facts:
        d.text((80, y), k, font=mono, fill=ACCENT)
        d.text((340, y), v, font=body, fill=INK)
        y += 52

    d.text(
        (80, 720),
        "Suggested repo name: mcp-agent-session-demo   ·   prepared locally, not published",
        font=foot,
        fill=MUTED,
    )
    return im


def make_caption(kicker: str, text: str) -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # lower-third bar, leaves the dashboard readable
    bar_top = 690
    d.rectangle((0, bar_top, W, H), fill=(8, 12, 24, 230))
    d.rectangle((0, bar_top, W, bar_top + 2), fill=ACCENT)
    kf = font("ibm", 14, "Medium")
    tf = font("ibm", 22, "Regular")
    d.text((36, bar_top + 12), kicker, font=kf, fill=ACCENT)
    d.text((36, bar_top + 36), text, font=tf, fill=INK)
    return im


def ff(*args, check=True):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", *args]
    print("+", " ".join(cmd[:12]), "..." if len(cmd) > 12 else "")
    subprocess.run(cmd, check=check)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        text=True,
    ).strip()
    return float(out)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    CAPTIONS.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    data = json.loads(LOG.read_text())
    raw_dur = probe_duration(RAW)
    print(f"raw duration {raw_dur:.3f}s  rec start {REC_START}")

    # Caption windows, in seconds from the start of the raw recording.
    windows = []
    t0 = 0.0
    windows.append((0, CAPTION_TEXT[0], t0, offset(data["steps"][0]["started_at"])))
    for i, s in enumerate(data["steps"]):
        start = offset(s["started_at"])
        if i + 1 < len(data["steps"]):
            end = offset(data["steps"][i + 1]["started_at"])
        else:
            # hold the last step caption until the session is marked complete,
            # then switch to the COMPLETE card for the remaining tail.
            end = offset(s["finished_at"]) + 3.0
        windows.append((s["n"], CAPTION_TEXT[s["n"]], start, end))
    windows.append((15, CAPTION_TEXT[15], windows[-1][3], raw_dur))
    # clamp
    cleaned = []
    for n, cap, a, b in windows:
        a = max(0.0, min(a, raw_dur))
        b = max(a + 0.05, min(b, raw_dur))
        cleaned.append((n, cap, a, b))
        print(f"  caption {n:2}  {a:7.2f}–{b:7.2f}  {cap[0]}")

    title = make_title()
    end = make_end()
    title.save(ASSETS / "title.png")
    end.save(ASSETS / "end.png")
    for n, cap, *_ in cleaned:
        make_caption(*cap).save(CAPTIONS / f"{n:02d}.png")

    # Title / end videos (5.5s + 0.5s fade)
    for name, src, dur in (("title", ASSETS / "title.png", 6.0), ("end", ASSETS / "end.png", 6.0)):
        ff(
            "-loop", "1", "-framerate", str(FPS), "-i", str(src),
            "-t", str(dur),
            "-vf", f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4}:d=0.4",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-an",
            "-r", str(FPS), "-movflags", "+faststart",
            str(WORK / f"{name}.mp4"),
        )

    # Build the filter for cropping the raw recording and overlaying captions.
    # Crop off the XFCE title (24px) and the bottom panel (~41px) → 1920x1135,
    # scale to 1280-wide, pad to 1280x800 with the dashboard background color.
    # Then overlay each caption PNG in its time window.
    inputs = ["-i", str(RAW)]
    n_caps = len(cleaned)
    for n, cap, a, b in cleaned:
        inputs += ["-i", str(CAPTIONS / f"{n:02d}.png")]

    filt = [
        f"[0:v]fps=15,crop=1920:1135:0:24,scale=1280:756:flags=lanczos,"
        f"pad=1280:800:0:22:color=0x0b1020,setsar=1,fps={FPS}[base]"
    ]
    last = "base"
    for i, (n, cap, a, b) in enumerate(cleaned, start=1):
        out = f"v{i}"
        filt.append(
            f"[{last}][{i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[{out}]"
        )
        last = out
    filt.append(f"[{last}]fade=t=in:st=0:d=0.3,fade=t=out:st={raw_dur-0.4}:d=0.4[vout]")
    filter_complex = ";".join(filt)

    body = WORK / "body.mp4"
    ff(
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-t", f"{raw_dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an",
        "-r", str(FPS), "-movflags", "+faststart",
        str(body),
    )

    # Concat title + body + end (re-encode to a single clean timeline)
    concat_list = WORK / "concat.txt"
    concat_list.write_text(
        f"file '{WORK / 'title.mp4'}'\nfile '{body}'\nfile '{WORK / 'end.mp4'}'\n"
    )
    ff(
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        str(DEMO),
    )

    # Poster: a frame from the completed-dashboard tail of the body,
    # composited under a slim label, taken ~4s before the raw ends
    # (the COMPLETE caption is on screen). Also save a clean still.
    still = WORK / "poster_frame.png"
    ff(
        "-ss", f"{raw_dur - 6:.2f}", "-i", str(body),
        "-frames:v", "1",
        str(still),
    )
    frame = Image.open(still).convert("RGBA")
    # Prefer a frame from the finished demo (title-less), just the body still.
    frame.convert("RGB").save(POSTER, "PNG", optimize=True)

    dur = probe_duration(DEMO)
    size = DEMO.stat().st_size
    print(f"DEMO {DEMO}  duration={dur:.2f}s  size={size} ({size/1e6:.2f} MB)")
    print(f"POSTER {POSTER}  size={POSTER.stat().st_size}")


if __name__ == "__main__":
    sys.exit(main())
