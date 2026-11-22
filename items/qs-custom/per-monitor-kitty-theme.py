#!/usr/bin/env python3
"""Generate per-monitor kitty Material You themes and live-switch kitty window colors on monitor move."""

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
CONFIG_FILE = HOME / ".config/illogical-impulse/config.json"
STATE_GEN = HOME / ".local/state/quickshell/user/generated"
TERM_DIR = STATE_GEN / "terminal"
GLOBAL_KITTY_THEME = TERM_DIR / "kitty-theme.conf"
II_COLORS_DIR = HOME / ".config/quickshell/ii/scripts/colors"
TEMPLATE_PATH = II_COLORS_DIR / "terminal/kitty-theme.conf"
GEN_SCRIPT = II_COLORS_DIR / "generate_colors_material.py"


def get_venv_python() -> str:
    venv = os.environ.get("ILLOGICAL_IMPULSE_VIRTUAL_ENV", "~/.local/state/quickshell/.venv")
    cand = Path(os.path.expanduser(venv)) / "bin/python3"
    if cand.exists():
        return str(cand)
    return sys.executable


def read_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def detect_dark_mode() -> str:
    try:
        colors = json.loads((STATE_GEN / "colors.json").read_text(encoding="utf-8"))
        bg = colors.get("background", "#141218").lstrip("#")
        if len(bg) == 6:
            r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return "dark" if lum < 128 else "light"
    except Exception:
        pass
    return "dark"


def theme_path_for(monitor: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", monitor)
    return TERM_DIR / f"kitty-theme-{safe}.conf"


def generate_kitty_theme(monitor: str, image_path: str) -> bool:
    if not monitor or not image_path or not Path(image_path).exists():
        return False
    if not TEMPLATE_PATH.exists() or not GEN_SCRIPT.exists():
        return False

    cfg = read_config()
    app = cfg.get("appearance", {})
    scheme = app.get("palette", {}).get("type", "auto") or "auto"
    term_props = app.get("wallpaperTheming", {}).get("terminalGenerationProps", {})
    mode = detect_dark_mode()

    args = [
        get_venv_python(),
        str(GEN_SCRIPT),
        "--path",
        image_path,
        "--mode",
        mode,
    ]
    if scheme and scheme != "null":
        args += ["--scheme", str(scheme)]
    if term_props.get("harmony") is not None:
        args += ["--harmony", str(term_props["harmony"])]
    if term_props.get("harmonizeThreshold") is not None:
        args += ["--harmonize_threshold", str(term_props["harmonizeThreshold"])]
    if term_props.get("termFgBoost") is not None:
        args += ["--term_fg_boost", str(term_props["termFgBoost"])]

    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return False

    colors_map = {}
    for line in res.stdout.splitlines():
        m = re.match(r"^\s*\$([A-Za-z0-9_]+)\s*:\s*(#[0-9A-Fa-f]{6})\s*;", line)
        if m:
            colors_map[m.group(1)] = m.group(2).lstrip("#")

    if not colors_map:
        return False

    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    for k, v in colors_map.items():
        tpl = tpl.replace(f"${k} #", v)

    TERM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = theme_path_for(monitor)
    out_path.write_text(tpl, encoding="utf-8")
    return True


def get_monitor_map() -> dict[int, str]:
    try:
        out = subprocess.check_output(["hyprctl", "monitors", "-j"], text=True)
        return {m["id"]: m["name"] for m in json.loads(out)}
    except Exception:
        return {}


def get_kitty_clients() -> list[dict]:
    try:
        out = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        return [c for c in json.loads(out) if c.get("class") == "kitty"]
    except Exception:
        return []


def resolve_theme_for_monitor(monitor: str, per_monitor: bool) -> Path | None:
    if per_monitor and monitor:
        p = theme_path_for(monitor)
        if p.exists():
            return p
    if GLOBAL_KITTY_THEME.exists():
        return GLOBAL_KITTY_THEME
    return None


def apply_to_pid(pid: int, theme_file: Path) -> None:
    sock = Path(f"/tmp/kitty-{pid}")
    if not sock.exists():
        return
    subprocess.run(
        ["kitty", "@", "--to", f"unix:{sock}", "set-colors", "--all", "--configured", str(theme_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def apply_all(last_seen: dict[int, tuple[str, str]] | None = None, force: bool = False) -> None:
    cfg = read_config()
    per_mon = bool(cfg.get("background", {}).get("perMonitor", False))
    mon_map = get_monitor_map()
    for client in get_kitty_clients():
        pid = client.get("pid")
        mon_id = client.get("monitor")
        if not pid or mon_id is None:
            continue
        mon_name = mon_map.get(mon_id, "")
        theme = resolve_theme_for_monitor(mon_name, per_mon)
        if not theme:
            continue
        state = (mon_name, str(theme))
        if not force and last_seen is not None and last_seen.get(pid) == state:
            continue
        apply_to_pid(pid, theme)
        if last_seen is not None:
            last_seen[pid] = state


def sync_all() -> None:
    cfg = read_config()
    bg = cfg.get("background", {})
    monitors = bg.get("monitors", {}) or {}
    for mon_name, entry in monitors.items():
        if isinstance(entry, dict):
            path = entry.get("thumbnailPath") or entry.get("wallpaperPath") or ""
            if path and Path(path).exists():
                generate_kitty_theme(mon_name, path)
    apply_all(force=True)


def watch() -> None:
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    sock_path = Path(runtime) / "hypr" / sig / ".socket2.sock"
    last_seen: dict[int, tuple[str, str]] = {}
    apply_all(last_seen, force=True)

    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(str(sock_path))
                buf = ""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buf += chunk.decode("utf-8", errors="ignore")
                    lines = buf.split("\n")
                    buf = lines.pop()
                    relevant = any(
                        ln.startswith(("movewindow>>", "movewindowv2>>", "openwindow>>", "workspacev2>>"))
                        for ln in lines
                    )
                    if relevant:
                        time.sleep(0.05)
                        apply_all(last_seen, force=False)
        except Exception:
            time.sleep(1.0)


def main() -> int:
    if len(sys.argv) < 2:
        return 1
    cmd = sys.argv[1]
    if cmd == "gen" and len(sys.argv) >= 4:
        ok = generate_kitty_theme(sys.argv[2], sys.argv[3])
        if ok:
            apply_all(force=True)
        return 0 if ok else 1
    if cmd == "apply":
        apply_all(force=True)
        return 0
    if cmd == "sync-all":
        sync_all()
        return 0
    if cmd == "watch":
        watch()
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
