#!/usr/bin/env python3
"""Generate README graphics from the real session log: banner, timeline, caption bars."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/workspace/mcp-demo")
MEDIA = ROOT / "media"
LOG = ROOT / "logs" / "steps.json"
TZ = ZoneInfo("America/New_York")

FONTS = {
    "outfit": "/usr/share/fonts/truetype/sand-box/google/Outfit/Outfit-VariableFont_wght.ttf",
    "ibm": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Sans/IBMPlexSans-VariableFont_wdth,wght.ttf",
    "mono": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-Regular.ttf",
    "monomed": "/usr/share/fonts/truetype/sand-box/google/IBM Plex Mono/IBMPlexMono-Medium.ttf",
}

CONN_COLOR = {
    "GitHub": (88, 166, 255),
    "X": (231, 233, 234),
    "Euler": (94, 234, 212),
    "Origin": (196, 181, 253),
}
CONN_BG = {
    "GitHub": (16, 28, 52),
    "X": (40, 42, 48),
    "Euler": (12, 40, 38),
    "Origin": (32, 26, 52),
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
    return datetime.strptime(
        s.replace(" EST", "").replace(" EDT", ""), "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=TZ)


def paint_bg(im: Image.Image):
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            dx1 = (x - 200) / (w * 0.55)
            dy1 = (y + 40) / (h * 0.9)
            g1 = max(0.0, 1.0 - (dx1 * dx1 + dy1 * dy1))
            dx2 = (x - w + 80) / (w * 0.5)
            dy2 = (y - 20) / (h * 0.85)
            g2 = max(0.0, 1.0 - (dx2 * dx2 + dy2 * dy2))
            r = int(11 + 18 * g1 + 6 * g2)
            g = int(16 + 16 * g1 + 22 * g2)
            b = int(32 + 36 * g1 + 14 * g2)
            px[x, y] = (min(r, 42), min(g, 56), min(b, 82), 255)


def make_banner():
    W, H = 2560, 720
    im = Image.new("RGBA", (W, H), (11, 16, 32, 255))
    paint_bg(im)
    d = ImageDraw.Draw(im)
    kicker = font("ibm", 36, "Medium")
    title = font("outfit", 148, "SemiBold")
    sub = font("ibm", 42, "Regular")
    pillf = font("ibm", 32, "Medium")
    foot = font("mono", 30)

    d.text((120, 90), "READ-ONLY MCP WALKTHROUGH", font=kicker, fill=(129, 140, 248, 255))
    d.text((120, 160), "MCP Agent Session Demo", font=title, fill=(232, 237, 248, 255))
    d.text(
        (120, 350),
        "A long-running agent session that chains GitHub, X, Euler, and Origin — reads only.",
        font=sub,
        fill=(139, 151, 184, 255),
    )

    pills = [
        ("cursor-github", (88, 166, 255), (16, 28, 52)),
        ("x", (17, 17, 17), (231, 233, 234)),
        ("user-Euler", (94, 234, 212), (12, 40, 38)),
        ("cursor-origin", (196, 181, 253), (32, 26, 52)),
    ]
    x = 120
    y = 450
    for name, fg, bg in pills:
        label = f"{name}  ·  READY"
        bbox = d.textbbox((0, 0), label, font=pillf)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.rounded_rectangle((x, y, x + tw + 64, y + th + 36), 28, fill=bg, outline=fg, width=3)
        d.text((x + 32, y + 14), label, font=pillf, fill=fg)
        x += tw + 88

    d.text(
        (120, 620),
        "14 steps  ·  4 connectors  ·  0 writes  ·  3 min 8 s video  ·  13 Nov 2026, America/New_York",
        font=foot,
        fill=(139, 151, 184, 255),
    )
    out = MEDIA / "banner.png"
    im.convert("RGB").save(out, "PNG", optimize=True)
    print(f"wrote {out} {out.stat().st_size}")


def make_timeline(data: dict):
    steps = data["steps"]
    starts = [parse_ts(s["started_at"]) for s in steps]
    ends = [parse_ts(s["finished_at"]) for s in steps]
    t0 = min(starts)
    t1 = max(ends)
    span = (t1 - t0).total_seconds()  # should be 12:12:57 to 12:15:30 = 153s

    W, H = 2400, 1480
    left, right = 420, W - 80
    top, bottom = 200, H - 120
    row_h = (bottom - top) / len(steps)

    im = Image.new("RGBA", (W, H), (11, 16, 32, 255))
    paint_bg(im)
    d = ImageDraw.Draw(im)
    title = font("outfit", 64, "SemiBold")
    sub = font("ibm", 30, "Regular")
    lab = font("ibm", 26, "Medium")
    mono = font("mono", 22)
    tiny = font("mono", 20)

    d.text((80, 40), "Session timeline", font=title, fill=(232, 237, 248, 255))
    d.text(
        (80, 120),
        f"Durations are finished_at − started_at from logs/steps.json  ·  "
        f"{t0.strftime('%H:%M:%S')}–{t1.strftime('%H:%M:%S')} EST  ·  America/New_York  ·  13 Nov 2026",
        font=sub,
        fill=(139, 151, 184, 255),
    )

    # vertical grid every 30s
    def x_at(dt: datetime) -> float:
        return left + ((dt - t0).total_seconds() / span) * (right - left)

    t = t0.replace(microsecond=0)
    # align to next :00 or :30
    sec = t.second
    add = (30 - sec % 30) % 30
    from datetime import timedelta

    mark = t + timedelta(seconds=add)
    if add == 0:
        mark = t
    while mark <= t1 + timedelta(seconds=1):
        x = x_at(mark)
        d.line((x, top - 10, x, bottom + 10), fill=(36, 48, 86, 255), width=2)
        d.text((x - 40, bottom + 18), mark.strftime("%H:%M:%S"), font=tiny, fill=(139, 151, 184, 255))
        mark += timedelta(seconds=30)

    d.line((left, bottom + 10, right, bottom + 10), fill=(80, 96, 140, 255), width=2)

    for i, s in enumerate(steps):
        y = top + i * row_h
        cy = y + row_h * 0.22
        ch = row_h * 0.50
        col = CONN_COLOR[s["connector"]]
        bg = CONN_BG[s["connector"]]
        x1, x2 = x_at(starts[i]), x_at(ends[i])
        # minimum visible width
        if x2 - x1 < 12:
            x2 = x1 + 12
        dur = (ends[i] - starts[i]).total_seconds()
        # label on the left
        d.text((80, y + 18), f"{s['n']:02d}  {s['connector']}", font=lab, fill=col)
        d.text((80, y + 52), s["tool"], font=mono, fill=(139, 151, 184, 255))
        # bar
        text_fill = (17, 17, 17, 255) if s["connector"] == "X" else (11, 16, 32, 255)
        d.rounded_rectangle((x1, cy, x2, cy + ch), 8, fill=col)
        # duration to the right of the bar
        label = f"{dur:.0f}s"
        d.text((x2 + 14, cy + 6), label, font=lab, fill=(232, 237, 248, 255))

    # legend
    lx = 80
    ly = H - 70
    d.text((lx, ly), "Connector", font=tiny, fill=(139, 151, 184, 255))
    lx += 140
    for name, col in CONN_COLOR.items():
        d.rounded_rectangle((lx, ly, lx + 28, ly + 22), 4, fill=col)
        d.text((lx + 38, ly - 2), name, font=lab, fill=(232, 237, 248, 255))
        lx += 200

    out = MEDIA / "timeline.png"
    im.convert("RGB").save(out, "PNG", optimize=True)
    print(f"wrote {out} {out.stat().st_size}")

    # Also a compact SVG (same data, scalable in the README as a fallback/companion)
    # Written as a simple, font-safe SVG.
    sw, sh = 1200, 740
    sl, sr, st, sb = 210, sw - 40, 100, sh - 60
    srow = (sb - st) / len(steps)

    def sx(dt):
        return sl + ((dt - t0).total_seconds() / span) * (sr - sl)

    def rgb(c):
        return f"rgb({c[0]},{c[1]},{c[2]})"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sw} {sh}" role="img" '
        f'aria-label="Session timeline of 14 MCP steps from {t0.strftime("%H:%M:%S")} to {t1.strftime("%H:%M:%S")} EST">',
        '<rect width="100%" height="100%" fill="#0b1020"/>',
        '<text x="40" y="42" fill="#e8edf8" font-family="ui-sans-serif, Helvetica, Arial, sans-serif" font-size="26" font-weight="600">Session timeline</text>',
        f'<text x="40" y="70" fill="#8b97b8" font-family="ui-sans-serif, Helvetica, Arial, sans-serif" font-size="13">'
        f'Durations are finished_at − started_at from logs/steps.json · {t0.strftime("%H:%M:%S")}–{t1.strftime("%H:%M:%S")} EST · America/New_York · 13 Nov 2026</text>',
    ]
    mark = t0.replace(microsecond=0)
    sec = mark.second
    add = (30 - sec % 30) % 30
    mark = mark + timedelta(seconds=add)
    while mark <= t1 + timedelta(seconds=1):
        x = sx(mark)
        parts.append(f'<line x1="{x:.1f}" y1="{st-4}" x2="{x:.1f}" y2="{sb+6}" stroke="#243056" stroke-width="1"/>')
        parts.append(
            f'<text x="{x-28:.1f}" y="{sb+24}" fill="#8b97b8" font-family="ui-monospace, monospace" font-size="11">{mark.strftime("%H:%M:%S")}</text>'
        )
        mark += timedelta(seconds=30)
    parts.append(f'<line x1="{sl}" y1="{sb+6}" x2="{sr}" y2="{sb+6}" stroke="#50608c" stroke-width="1.2"/>')
    for i, s in enumerate(steps):
        y = st + i * srow
        col = CONN_COLOR[s["connector"]]
        x1, x2 = sx(starts[i]), sx(ends[i])
        if x2 - x1 < 6:
            x2 = x1 + 6
        dur = (ends[i] - starts[i]).total_seconds()
        parts.append(
            f'<text x="40" y="{y+16:.1f}" fill="{rgb(col)}" font-family="ui-sans-serif, Helvetica, Arial, sans-serif" font-size="12" font-weight="600">{s["n"]:02d}  {s["connector"]}</text>'
        )
        parts.append(
            f'<text x="40" y="{y+32:.1f}" fill="#8b97b8" font-family="ui-monospace, monospace" font-size="11">{s["tool"]}</text>'
        )
        parts.append(
            f'<rect x="{x1:.1f}" y="{y+8:.1f}" width="{x2-x1:.1f}" height="{srow*0.42:.1f}" rx="4" fill="{rgb(col)}"/>'
        )
        parts.append(
            f'<text x="{x2+6:.1f}" y="{y+26:.1f}" fill="#e8edf8" font-family="ui-sans-serif, Helvetica, Arial, sans-serif" font-size="12">{dur:.0f}s</text>'
        )
    parts.append("</svg>\n")
    svg = MEDIA / "timeline.svg"
    svg.write_text("\n".join(parts))
    print(f"wrote {svg} {svg.stat().st_size}")


def crop_caption_bars():
    """Crop each 1280x800 caption overlay to its lower-third bar on a solid background."""
    outdir = MEDIA / "caption-bars"
    outdir.mkdir(exist_ok=True)
    for p in sorted((MEDIA / "captions").glob("*.png")):
        im = Image.open(p).convert("RGBA")
        # bar starts around y=690; keep a little padding
        bar = im.crop((0, 686, im.width, im.height))
        bg = Image.new("RGB", bar.size, (8, 12, 24))
        bg.paste(bar, (0, 0), bar)
        dest = outdir / p.name
        bg.save(dest, "PNG", optimize=True)
    print(f"wrote {len(list(outdir.glob('*.png')))} caption bars to {outdir}")


def main():
    data = json.loads(LOG.read_text())
    make_banner()
    make_timeline(data)
    crop_caption_bars()


if __name__ == "__main__":
    main()
