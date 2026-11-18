#!/usr/bin/env python3
"""Dynamically fetch live models & slash commands from `claude` or `codex` CLI."""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys


def fetch_claude() -> dict:
    bin_path = shutil.which("claude")
    if not bin_path:
        return {"installed": False, "models": [], "commands": []}

    # Query claude init event (no LLM turn needed when passing /help or reading init)
    res = subprocess.run(
        [bin_path, "-p", "/help", "--output-format", "stream-json", "--verbose"],
        capture_output=True,
        text=True,
        timeout=12,
        check=False,
    )
    init_ev = {}
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            init_ev = ev
            break

    default_model = init_ev.get("model", "")
    raw_cmds = init_ev.get("slash_commands", [])
    commands = []
    seen = set()
    for name in raw_cmds:
        if not name or name.startswith("__") or name in seen:
            continue
        seen.add(name)
        commands.append({
            "name": "/" + name,
            "description": "",
            "instant": name in ("model", "effort", "clear", "compact", "help", "usage", "credits", "doctor", "agents"),
        })
    for extra in (
        {"name": "/login", "description": "Sign in / authenticate Claude CLI", "instant": True},
        {"name": "/clear", "description": "Start a new conversation", "instant": True},
    ):
        if extra["name"] not in seen and extra["name"].lstrip("/") not in seen:
            commands.append(extra)

    # Extract available claude model aliases/IDs dynamically from settings + init
    models = []
    if default_model:
        models.append({"id": default_model, "name": default_model, "efforts": ["low", "medium", "high", "max"]})
    # Check ~/.claude/cache or claude --help for model aliases, plus standard aliases supported by installed CLI
    for alias in ("sonnet", "opus", "haiku"):
        if alias != default_model and not default_model.startswith(f"claude-{alias}"):
            models.append({"id": alias, "name": alias, "efforts": [] if alias == "haiku" else ["low", "medium", "high", "max"]})
        elif alias != default_model:
            # Keep other families alongside default_model
            continue

    # Ensure opus & haiku are also selectable alongside default sonnet (or vice versa)
    have_families = {m["id"] for m in models}
    for fam in ("opus", "sonnet", "haiku"):
        if not any(fam in x for x in have_families):
            models.append({"id": fam, "name": fam, "efforts": [] if fam == "haiku" else ["low", "medium", "high", "max"]})

    return {"installed": True, "defaultModel": default_model or "sonnet", "models": models, "commands": commands}


def fetch_codex() -> dict:
    bin_path = shutil.which("codex")
    if not bin_path:
        return {"installed": False, "models": [], "commands": []}

    # Read configured model from ~/.codex/config.toml if present
    cfg_path = pathlib.Path.home() / ".codex/config.toml"
    default_model = ""
    if cfg_path.exists():
        m = re.search(r'^model\s*=\s*"([^"]+)"', cfg_path.read_text(encoding="utf-8", errors="ignore"), re.M)
        if m:
            default_model = m.group(1)

    models = []
    if default_model:
        models.append({"id": default_model, "name": default_model, "efforts": ["low", "medium", "high"]})

    # Check codex cache/models if available
    models_cache = pathlib.Path.home() / ".codex/models_cache.json"
    if models_cache.exists():
        try:
            data = json.loads(models_cache.read_text(encoding="utf-8"))
            for item in data.get("models", []):
                slug = item.get("slug") or item.get("id")
                if slug and not any(m["id"] == slug for m in models):
                    models.append({"id": slug, "name": item.get("display_name") or slug, "efforts": ["low", "medium", "high"]})
        except Exception:
            pass

    commands = [
        {"name": "/model", "description": "Select model & reasoning effort", "instant": True},
        {"name": "/effort", "description": "Set reasoning effort", "instant": True},
        {"name": "/login", "description": "Sign in / authenticate Codex CLI", "instant": True},
        {"name": "/clear", "description": "Start a new conversation", "instant": True},
    ]
    return {"installed": True, "defaultModel": default_model or (models[0]["id"] if models else ""), "models": models, "commands": commands}


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    backend = sys.argv[1]
    if backend == "claude":
        print(json.dumps(fetch_claude(), ensure_ascii=False))
    elif backend == "codex":
        print(json.dumps(fetch_codex(), ensure_ascii=False))
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
