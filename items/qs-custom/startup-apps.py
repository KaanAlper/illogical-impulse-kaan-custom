#!/usr/bin/env python3
"""Manage startup applications from ~/.config/autostart, /etc/xdg/autostart, and ~/.config/hypr/custom/execs.lua."""

import json
import os
import pathlib
import re
import sys

USER_AUTOSTART = pathlib.Path.home() / ".config/autostart"
SYS_AUTOSTART = pathlib.Path("/etc/xdg/autostart")
HYPR_EXECS = pathlib.Path.home() / ".config/hypr/custom/execs.lua"

EXEC_RE = re.compile(r'^(\s*)(--\s*\[disabled\]\s*)?hl\.exec_cmd\((["\'])(.+)\3\)\s*$')


def _parse_desktop(path: pathlib.Path) -> dict[str, str]:
    data: dict[str, str] = {}
    in_entry = False
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("["):
                in_entry = (line == "[Desktop Entry]")
                continue
            if in_entry and "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    except OSError:
        pass
    return data


def _friendly_hypr_name(cmd: str) -> tuple[str, str]:
    low = cmd.lower()
    if "asena-dpi-tray" in low:
        return ("AsenaDPI Tray", "preferences-desktop-display")
    if "alttab/shell.qml" in low:
        return ("Alt+Tab Switcher", "view_carousel")
    if "bootsplash/shell.qml" in low:
        return ("XANA Bootsplash", "wallpaper")
    if "hl.dsp.focus" in low:
        return ("Default Monitor Focus", "desktop_windows")
    parts = cmd.strip().split()
    base = os.path.basename(parts[0]) if parts else cmd
    return (base, "terminal")


def list_apps() -> list[dict]:
    items: list[dict] = []

    # 1. Hyprland custom execs.lua entries
    hypr_asena_enabled = None
    hypr_mtime = HYPR_EXECS.stat().st_mtime if HYPR_EXECS.exists() else 0
    if HYPR_EXECS.exists():
        for idx, line in enumerate(HYPR_EXECS.read_text(encoding="utf-8", errors="replace").splitlines()):
            m = EXEC_RE.match(line)
            if not m:
                continue
            disabled = bool(m.group(2))
            cmd = m.group(4)
            if "hl.dsp.focus" in cmd:
                continue
            if "asena-dpi-tray" in cmd.lower():
                hypr_asena_enabled = not disabled
                continue
            name, icon = _friendly_hypr_name(cmd)
            items.append({
                "id": f"hypr:{idx}",
                "name": name,
                "cmd": cmd,
                "icon": icon,
                "source": "Hypr",
                "enabled": not disabled,
                "removable": False,
                "mtime": hypr_mtime,
            })

    # 2. XDG autostart entries (user overrides system)
    seen_files: dict[str, tuple[pathlib.Path, bool]] = {}
    if SYS_AUTOSTART.is_dir():
        for p in sorted(SYS_AUTOSTART.glob("*.desktop")):
            if p.name in ("org.kde.plasmashell.desktop",):
                continue
            seen_files[p.name] = (p, False)
    if USER_AUTOSTART.is_dir():
        for p in sorted(USER_AUTOSTART.glob("*.desktop")):
            seen_files[p.name] = (p, True)

    for fname, (p, is_user) in sorted(seen_files.items()):
        d = _parse_desktop(p)
        if not d:
            continue
        name = d.get("Name") or p.stem
        cmd = d.get("Exec") or ""
        icon = d.get("Icon") or "application-x-executable"
        hidden = d.get("Hidden", "").lower() == "true"
        gnome_en = d.get("X-GNOME-Autostart-enabled", "true").lower() != "false"
        enabled = (not hidden) and gnome_en
        if fname == "asena-dpi-tray.desktop" and hypr_asena_enabled is not None:
            enabled = enabled and hypr_asena_enabled
        try:
            mtime = p.stat().st_mtime
        except OSError:
            mtime = 0
        items.append({
            "id": f"xdg:{fname}",
            "name": name,
            "cmd": cmd,
            "icon": icon,
            "source": "Autostart",
            "enabled": enabled,
            "removable": is_user and not (SYS_AUTOSTART / fname).exists(),
            "mtime": mtime,
        })

    if hypr_asena_enabled is not None and "asena-dpi-tray.desktop" not in seen_files:
        items.append({
            "id": "asena:tray",
            "name": "AsenaDPI",
            "cmd": "/usr/local/bin/asena-dpi-tray",
            "icon": "preferences-desktop-display",
            "source": "Hypr",
            "enabled": hypr_asena_enabled,
            "removable": False,
            "mtime": hypr_mtime,
        })

    items.sort(key=lambda x: (0 if x["enabled"] else 1, 0 if "asena" in x["name"].lower() else 1, x["name"].lower()))
    return items


def toggle_app(item_id: str, enable: bool) -> int:
    if item_id.startswith("hypr:"):
        idx = int(item_id.split(":", 1)[1])
        if not HYPR_EXECS.exists():
            return 1
        lines = HYPR_EXECS.read_text(encoding="utf-8").splitlines(keepends=True)
        if 0 <= idx < len(lines):
            m = EXEC_RE.match(lines[idx].rstrip("\r\n"))
            if m:
                indent, _dis, q, cmd = m.group(1), m.group(2), m.group(3), m.group(4)
                nl = "\n" if lines[idx].endswith("\n") else ""
                prefix = "" if enable else "-- [disabled] "
                lines[idx] = f"{indent}{prefix}hl.exec_cmd({q}{cmd}{q}){nl}"
                HYPR_EXECS.write_text("".join(lines), encoding="utf-8")
                return 0
        return 1

    if item_id.startswith("xdg:"):
        fname = item_id.split(":", 1)[1]
        if fname == "asena-dpi-tray.desktop" and HYPR_EXECS.exists():
            for idx, ln in enumerate(HYPR_EXECS.read_text(encoding="utf-8", errors="replace").splitlines()):
                if "asena-dpi-tray" in ln.lower() and EXEC_RE.match(ln):
                    toggle_app(f"hypr:{idx}", enable)
        USER_AUTOSTART.mkdir(parents=True, exist_ok=True)
        dst = USER_AUTOSTART / fname
        src = dst if dst.exists() else (SYS_AUTOSTART / fname)
        if not src.exists():
            return 1
        lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
        out = []
        saw_hidden = False
        saw_gnome = False
        for ln in lines:
            st = ln.strip()
            if st.startswith("Hidden="):
                out.append(f"Hidden={'false' if enable else 'true'}")
                saw_hidden = True
            elif st.startswith("X-GNOME-Autostart-enabled="):
                out.append(f"X-GNOME-Autostart-enabled={'true' if enable else 'false'}")
                saw_gnome = True
            else:
                out.append(ln)
        if not saw_hidden:
            out.append(f"Hidden={'false' if enable else 'true'}")
        if not saw_gnome:
            out.append(f"X-GNOME-Autostart-enabled={'true' if enable else 'false'}")
        dst.write_text("\n".join(out) + "\n", encoding="utf-8")
        return 0

    return 1


def list_installed_apps() -> list[dict]:
    dirs = [pathlib.Path("/usr/share/applications"), pathlib.Path.home() / ".local/share/applications"]
    by_name: dict[str, dict] = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.desktop")):
            parsed = _parse_desktop(p)
            if not parsed or parsed.get("NoDisplay", "").lower() == "true":
                continue
            name = parsed.get("Name") or p.stem
            raw_exec = parsed.get("Exec") or ""
            clean_exec = re.sub(r"\s+%[fFuUdDnNickvm]", "", raw_exec).strip()
            if not clean_exec:
                continue
            by_name[p.name] = {
                "displayName": name,
                "value": p.name,
                "exec": clean_exec,
                "icon": parsed.get("Icon") or "application-x-executable",
            }
    return sorted(by_name.values(), key=lambda x: x["displayName"].lower())


def add_app(name: str, cmd: str, icon_override: str = "") -> int:
    name = name.strip()
    cmd = cmd.strip()
    if not name or not cmd:
        return 1
    slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-") or "app"
    USER_AUTOSTART.mkdir(parents=True, exist_ok=True)
    dst = USER_AUTOSTART / f"custom-{slug}.desktop"
    n = 1
    while dst.exists():
        n += 1
        dst = USER_AUTOSTART / f"custom-{slug}-{n}.desktop"
    icon = icon_override.strip() or os.path.basename(cmd.split()[0])
    dst.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        f"Exec={cmd}\n"
        f"Icon={icon}\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8",
    )
    return 0


def remove_app(item_id: str) -> int:
    if item_id.startswith("xdg:"):
        fname = item_id.split(":", 1)[1]
        if fname == "asena-dpi-tray.desktop" and HYPR_EXECS.exists():
            lines = HYPR_EXECS.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            kept = [ln for ln in lines if "asena-dpi-tray" not in ln.lower()]
            if len(kept) != len(lines):
                HYPR_EXECS.write_text("".join(kept), encoding="utf-8")
        dst = USER_AUTOSTART / fname
        if dst.exists() and not (SYS_AUTOSTART / fname).exists():
            dst.unlink()
            return 0
    return 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print(json.dumps(list_apps(), ensure_ascii=False))
        return 0
    action = sys.argv[1]
    if action == "apps":
        print(json.dumps(list_installed_apps(), ensure_ascii=False))
        return 0
    if action == "toggle" and len(sys.argv) >= 4:
        return toggle_app(sys.argv[2], sys.argv[3] in ("1", "true", "True"))
    if action == "add" and len(sys.argv) >= 4:
        return add_app(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) >= 5 else "")
    if action == "remove" and len(sys.argv) >= 3:
        return remove_app(sys.argv[2])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
