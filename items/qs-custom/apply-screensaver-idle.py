#!/usr/bin/env python3
"""Sync screensaver idle listener in ~/.config/hypr/custom/hypridle.conf and reload hypridle."""

import os
import re
import subprocess
import sys

HYPRIDLE_CONF = os.path.expanduser("~/.config/hypr/custom/hypridle.conf")
START_MARK = "# --- quickshell screensaver start ---"
END_MARK = "# --- quickshell screensaver end ---"


def main() -> int:
    if len(sys.argv) < 3:
        return 1
    enabled = sys.argv[1] in ("1", "true", "True")
    try:
        minutes = max(1, min(60, int(float(sys.argv[2]))))
    except ValueError:
        minutes = 3

    if not os.path.exists(HYPRIDLE_CONF):
        return 0

    src = open(HYPRIDLE_CONF, encoding="utf-8").read()
    pattern = re.compile(rf"\n?{re.escape(START_MARK)}.*?{re.escape(END_MARK)}\n?", re.S)
    src = pattern.sub("\n", src).rstrip() + "\n"

    if enabled:
        secs = minutes * 60
        block = (
            f"\n{START_MARK}\n"
            f"listener {{\n"
            f"    timeout = {secs}\n"
            f"    on-timeout = qs ipc -c ii call screensaver show\n"
            f"    on-resume = qs ipc -c ii call screensaver hide\n"
            f"}}\n"
            f"{END_MARK}\n"
        )
        src += block

    with open(HYPRIDLE_CONF, "w", encoding="utf-8") as f:
        f.write(src)

    # Restart hypridle if currently running so the new timeout takes effect
    if subprocess.run(["pgrep", "-x", "hypridle"], stdout=subprocess.DEVNULL).returncode == 0:
        subprocess.run(["pkill", "-x", "hypridle"], check=False)
        subprocess.Popen(["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
