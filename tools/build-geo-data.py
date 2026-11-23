#!/usr/bin/env python3
"""Build the compact per-country location files used by the weather location picker.

Source: dr5hn/countries-states-cities-database (ODbL 1.0), https://github.com/dr5hn/countries-states-cities-database
Output: data/geo/countries.json  -> [{"c": "TR", "n": "Turkey", "t": {"tr": "Türkiye", ...}}, ...]
        data/geo/<CC>.json       -> {"s": [{"n": "Istanbul", "t": {...}, "c": [["Kadikoy", 40.9903, 29.0275], ...]}]}
Usage: tools/build-geo-data.py <countries+states+cities.json> <out-dir>
"""
import json
import sys
from pathlib import Path

LANGS = {"tr": "tr", "de": "de", "es": "es", "fr": "fr", "ja": "ja", "it": "it", "pt-BR": "pt-BR", "ru": "ru", "uk": "uk", "cn": "zh-CN"}


def short_tr(translations: dict | None) -> dict:
    out = {}
    for src, dst in LANGS.items():
        v = (translations or {}).get(src)
        if v:
            out[dst] = v
    return out


def coord(v):
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads(src.read_text(encoding="utf-8"))
    countries = []
    for c in data:
        cc = c.get("iso2")
        if not cc:
            continue
        countries.append({"c": cc, "n": c["name"], "t": short_tr(c.get("translations"))})
        states = []
        for s in c.get("states") or []:
            cities = []
            for ci in s.get("cities") or []:
                lat, lon = coord(ci.get("latitude")), coord(ci.get("longitude"))
                if lat is None or lon is None:
                    continue
                cities.append([ci["name"], lat, lon])
            cities.sort(key=lambda x: x[0].lower())
            slat, slon = coord(s.get("latitude")), coord(s.get("longitude"))
            states.append({"n": s["name"], "t": short_tr(s.get("translations")), "lat": slat, "lon": slon, "c": cities})
        states.sort(key=lambda x: x["n"].lower())
        (out / f"{cc}.json").write_text(json.dumps({"s": states}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    countries.sort(key=lambda x: x["n"].lower())
    (out / "countries.json").write_text(json.dumps(countries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(countries)} countries written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
