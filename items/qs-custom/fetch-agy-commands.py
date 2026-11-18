#!/usr/bin/env python3
"""Fetch live slash commands directly from `agy -p /help --output-format stream-json`."""

import json
import os
import subprocess


def main() -> int:
    agy_bin = os.path.expanduser("~/.local/bin/agy")
    if not os.path.exists(agy_bin):
        agy_bin = "agy"

    res = subprocess.run(
        [agy_bin, "-p", "/help", "--output-format", "stream-json"],
        capture_output=True,
        text=True,
        check=False,
    )

    commands = []
    seen = set()
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("event") == "command_result":
            raw_cmds = ev.get("command", {}).get("data", {}).get("commands", [])
            for c in raw_cmds:
                name = c.get("name", "")
                if not name or name in seen:
                    continue
                seen.add(name)
                commands.append({
                    "name": name,
                    "description": c.get("description", ""),
                    "instant": name in ("model", "help", "usage", "credits", "agents", "skills", "changelog"),
                })

    # Sidebar-specific helpers (login in terminal, clear local conversation)
    for extra in (
        {"name": "login", "description": "Sign in / authenticate Antigravity CLI", "instant": True},
        {"name": "clear", "description": "Start a new conversation", "instant": True},
    ):
        if extra["name"] not in seen:
            commands.append(extra)

    print(json.dumps(commands, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
