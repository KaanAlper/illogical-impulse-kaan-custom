#!/usr/bin/env python3
"""Location data for the weather settings: weather-geo.py countries | country <CC>

Prints compact JSON built from dr5hn/countries-states-cities-database (see tools/build-geo-data.py).
Lookup order: cache -> a local kaan-dots checkout -> the GitHub repo (cached afterwards).
"""

import os
import re
import sys
import urllib.request
from pathlib import Path

BASE = os.environ.get("WEATHER_GEO_URL", "https://raw.githubusercontent.com/KaanAlper/illogical-impulse-kaan-custom/main/data/geo/")
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ii-weather-geo"
LOCAL = [Path.home() / "kaan-dots/data/geo", Path.home() / ".local/share/dotsync/repo/data/geo"]


def load(name: str) -> str | None:
    cached = CACHE / name
    if cached.exists() and cached.stat().st_size > 2:
        return cached.read_text(encoding="utf-8")
    for d in LOCAL:
        p = d / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    try:
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "ii-weather-geo"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            text = resp.read().decode("utf-8")
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / name).write_text(text, encoding="utf-8")
        return text
    except Exception:
        return None


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    if sys.argv[1] == "countries":
        name = "countries.json"
    elif sys.argv[1] == "country" and len(sys.argv) >= 3 and re.fullmatch(r"[A-Za-z]{2}", sys.argv[2]):
        name = sys.argv[2].upper() + ".json"
    else:
        return 2
    text = load(name)
    if text is None:
        sys.stderr.write("ERR: location data unavailable\n")
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
