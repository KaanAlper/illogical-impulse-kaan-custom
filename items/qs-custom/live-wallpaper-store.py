#!/usr/bin/env python3
"""Fetch, search, and download live wallpapers from motionbgs.com and apply via switchwall.sh."""

import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
LIVE_DIR = Path.home() / "Pictures/Wallpapers/Live"
SWITCHWALL = Path.home() / ".config/quickshell/ii/scripts/colors/switchwall.sh"


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def list_wallpapers(page: int = 1, query: str = "") -> list[dict]:
    q = query.strip()
    if q:
        url = f"https://motionbgs.com/search?q={urllib.parse.quote_plus(q)}&page={page}"
    else:
        url = f"https://motionbgs.com/?page={page}"
    html = fetch_html(url)

    # Match thumbnail URLs: /i/c/<size>/media/<id>/<slug>.<res>.jpg
    pattern = re.compile(r'/i/c/\d+x\d+/media/(\d+)/([a-z0-9-]+)\.\d+x\d+\.jpg')
    seen: set[str] = set()
    items: list[dict] = []
    for m in pattern.finditer(html):
        wid, slug = m.group(1), m.group(2)
        if wid in seen:
            continue
        seen.add(wid)
        title = slug.replace("-", " ").title()
        items.append({
            "id": wid,
            "slug": slug,
            "title": title,
            "thumb": f"https://motionbgs.com/i/c/546x308/media/{wid}/{slug}.3840x2160.jpg",
            "previewMp4": f"https://motionbgs.com/media/{wid}/{slug}.960x540.mp4",
        })
    return items


def download_and_apply(wid: str, slug: str, monitor: str = "") -> int:
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    safe_slug = re.sub(r"[^A-Za-z0-9._-]", "_", slug) or wid
    out_path = LIVE_DIR / f"{safe_slug}-{wid}.mp4"

    if not out_path.exists() or out_path.stat().st_size < 10000:
        for url in (
            f"https://motionbgs.com/dl/hd/{wid}",
            f"https://motionbgs.com/media/{wid}/{slug}.960x540.mp4",
        ):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = resp.read()
                if len(data) > 10000 and b"<html" not in data[:256].lower():
                    out_path.write_bytes(data)
                    break
            except Exception:
                continue

    if not out_path.exists() or out_path.stat().st_size < 10000:
        return 1

    cmd = ["bash", str(SWITCHWALL), "--image", str(out_path)]
    if monitor:
        cmd += ["--monitor", monitor]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    print(str(out_path))
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        page = int(sys.argv[2]) if len(sys.argv) >= 3 else 1
        query = sys.argv[3] if len(sys.argv) >= 4 else ""
        try:
            print(json.dumps(list_wallpapers(page, query), ensure_ascii=False))
            return 0
        except Exception as e:
            sys.stderr.write(f"ERR: {e}\n")
            print("[]")
            return 1
    if sys.argv[1] == "download" and len(sys.argv) >= 4:
        mon = sys.argv[4] if len(sys.argv) >= 5 else ""
        return download_and_apply(sys.argv[2], sys.argv[3], mon)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
