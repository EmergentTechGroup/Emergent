#!/usr/bin/env python3
"""Update a step in the live session log (JSON + Markdown)."""
import argparse, json, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LOG = Path("/workspace/mcp-demo/logs/steps.json")
MD = Path("/workspace/mcp-demo/logs/steps.md")
TZ = ZoneInfo("America/New_York")

def now():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--status", choices=["pending","running","ok","error"])
    p.add_argument("--title")
    p.add_argument("--connector")
    p.add_argument("--tool")
    p.add_argument("--summary")
    p.add_argument("--session-status")
    p.add_argument("--duration-ms", type=int)
    args = p.parse_args()

    data = json.loads(LOG.read_text())
    step = next((s for s in data["steps"] if s["n"] == args.n), None)
    if not step:
        raise SystemExit(f"no step {args.n}")
    if args.status:
        step["status"] = args.status
        if args.status == "running":
            step["started_at"] = now()
            step["timestamp"] = now()
        if args.status in ("ok", "error"):
            step["finished_at"] = now()
            step["timestamp"] = now()
    if args.title is not None:
        step["title"] = args.title
    if args.connector is not None:
        step["connector"] = args.connector
    if args.tool is not None:
        step["tool"] = args.tool
    if args.summary is not None:
        step["summary"] = args.summary
    if args.duration_ms is not None:
        step["duration_ms"] = args.duration_ms
    if args.session_status:
        data["status"] = args.session_status
    data["updated_at"] = now()
    LOG.write_text(json.dumps(data, indent=2) + "\n")

    # Refresh markdown
    lines = [
        "# MCP Agent Session — Step Log",
        "",
        f"- Session status: **{data.get('status','')}**",
        f"- Started: {data.get('started_at','')}",
        f"- Updated: {data.get('updated_at','')}",
        f"- Time zone: America/New_York",
        f"- Policy: read-only; no connector writes; no remote repository created.",
        "",
        "| # | Time (America/New_York) | Connector | Tool | Status | Summary |",
        "|---|-------------------------|-----------|------|--------|---------|",
    ]
    for s in data["steps"]:
        summary = (s.get("summary") or "").replace("\n", " / ").replace("|", "/")
        lines.append(
            f"| {s['n']} | {s.get('timestamp') or '—'} | {s.get('connector','')} | `{s.get('tool','')}` | {s.get('status','')} | {summary} |"
        )
    lines.append("")
    MD.write_text("\n".join(lines))

if __name__ == "__main__":
    main()
