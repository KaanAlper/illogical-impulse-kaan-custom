#!/usr/bin/env bash
# Re-apply the custom bar widgets after an end-4 / illogical-impulse dots update.
#
# Widgets restored here:
#   - AudioMonoToggle    — mono/stereo output downmix toggle (uses scripts/audio-mono-toggle.sh)
#   - AudioOutputSwitcher — pick the default output device from a hover popup (pure QML)
#   - SleepInhibitToggle  — moon icon: block sleep/idle/lid-close (uses scripts/sleep-inhibit-toggle.sh)
#   - AppVolumeMixer      — per-app volume mixer popup, EarTrumpet-style (pure QML)
#
# The dots updater overwrites tracked files (notably BarContent.qml, which IS in
# ~/.config/illogical-impulse/installed_listfile) and may delete untracked files,
# so the customizations can be lost on update. Run this once after every dots update:
#
#     ~/.config/quickshell-custom/apply.sh
#
# It is idempotent: safe to run any number of times.
set -u

CUSTOM_DIR="$HOME/.config/quickshell-custom"
II="$HOME/.config/quickshell/ii"
BAR="$II/modules/ii/bar"

if [ ! -d "$II" ]; then
    echo "✗ $II yok — quickshell ii config bulunamadı." >&2
    exit 1
fi

# 1) Restore the toggle script and the bar widgets into the dots tree.
mkdir -p "$II/scripts" "$BAR"
cp "$CUSTOM_DIR/audio-mono-toggle.sh" "$II/scripts/audio-mono-toggle.sh"
chmod +x "$II/scripts/audio-mono-toggle.sh"
cp "$CUSTOM_DIR/AudioMonoToggle.qml" "$BAR/AudioMonoToggle.qml"
cp "$CUSTOM_DIR/AudioOutputSwitcher.qml" "$BAR/AudioOutputSwitcher.qml"
cp "$CUSTOM_DIR/sleep-inhibit-toggle.sh" "$II/scripts/sleep-inhibit-toggle.sh"
chmod +x "$II/scripts/sleep-inhibit-toggle.sh"
cp "$CUSTOM_DIR/everything-update.sh" "$II/scripts/everything-update.sh"
chmod +x "$II/scripts/everything-update.sh"
cp "$CUSTOM_DIR/everything-query.py" "$II/scripts/everything-query.py"
chmod +x "$II/scripts/everything-query.py"
cp "$CUSTOM_DIR/FileSearch.qml" "$II/services/FileSearch.qml"
cp "$CUSTOM_DIR/EverythingToolbar.qml" "$II/modules/ii/overview/EverythingToolbar.qml"
cp "$CUSTOM_DIR/EverythingMenus.qml" "$II/modules/ii/overview/EverythingMenus.qml"
mkdir -p "$II/scripts/ai" "$II/modules/ii/sidebarLeft"
cp "$CUSTOM_DIR/fetch-agy-models.py" "$II/scripts/ai/fetch-agy-models.py"
chmod +x "$II/scripts/ai/fetch-agy-models.py"
cp "$CUSTOM_DIR/fetch-agy-commands.py" "$II/scripts/ai/fetch-agy-commands.py"
chmod +x "$II/scripts/ai/fetch-agy-commands.py"
cp "$CUSTOM_DIR/AgyModelPicker.qml" "$II/modules/ii/sidebarLeft/AgyModelPicker.qml"
cp "$CUSTOM_DIR/SleepInhibitToggle.qml" "$BAR/SleepInhibitToggle.qml"
cp "$CUSTOM_DIR/AppVolumeMixer.qml" "$BAR/AppVolumeMixer.qml"

# 2) Idempotently insert each widget into BarContent.qml (right section, before SysTray).
#    Order ends up: ... SleepInhibitToggle, AudioMonoToggle, AudioOutputSwitcher, AppVolumeMixer, SysTray ...
python3 - "$BAR/BarContent.qml" <<'PY'
import sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    src = f.read()

# Each widget: name used for the "already patched?" guard, and the block to insert.
widgets = [
    ("SleepInhibitToggle",
     "            SleepInhibitToggle {\n"
     "                visible: root.useShortenedForm < 2\n"
     "                Layout.alignment: Qt.AlignVCenter\n"
     "                Layout.leftMargin: 4\n"
     "                Layout.rightMargin: 4\n"
     "            }\n"
     "\n"),
    ("AudioMonoToggle",
     "            AudioMonoToggle {\n"
     "                visible: root.useShortenedForm < 2\n"
     "                Layout.alignment: Qt.AlignVCenter\n"
     "                Layout.leftMargin: 4\n"
     "                Layout.rightMargin: 4\n"
     "            }\n"
     "\n"),
    ("AudioOutputSwitcher",
     "            AudioOutputSwitcher {\n"
     "                visible: root.useShortenedForm < 2\n"
     "                Layout.alignment: Qt.AlignVCenter\n"
     "                Layout.leftMargin: 4\n"
     "                Layout.rightMargin: 4\n"
     "            }\n"
     "\n"),
    ("AppVolumeMixer",
     "            AppVolumeMixer {\n"
     "                visible: root.useShortenedForm < 2\n"
     "                Layout.alignment: Qt.AlignVCenter\n"
     "                Layout.leftMargin: 4\n"
     "                Layout.rightMargin: 4\n"
     "            }\n"
     "\n"),
]

inserted, skipped, missing = [], [], False
for name, block in widgets:
    if name in src:
        skipped.append(name)
        continue
    lines = src.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.strip() == "SysTray {":
            lines.insert(i, block)
            src = "".join(lines)
            inserted.append(name)
            break
    else:
        sys.stderr.write(
            f"  UYARI: BarContent.qml icinde 'SysTray {{' bulunamadi. "
            f"{name} blogunu sag bolume elle ekleyin.\n"
        )
        missing = True

if inserted:
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("  BarContent.qml: eklendi -> " + ", ".join(inserted))
if skipped:
    print("  BarContent.qml: zaten yamalı -> " + ", ".join(skipped))

# Raise shorten threshold to 1366 so 1280px secondary monitors don't overlap bar icons.
old_thresh = "(Appearance.sizes.barShortenScreenWidthThreshold >= screen?.width) ? 1 : 0"
new_thresh = "(Math.max(Appearance.sizes.barShortenScreenWidthThreshold, 1366) >= screen?.width) ? 1 : 0"
if new_thresh not in src and old_thresh in src:
    src = src.replace(old_thresh, new_thresh, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("  BarContent.qml: kucuk monitor esigi -> 1366px")

sys.exit(1 if missing else 0)
PY
rc=$?

# 2b) Fix an upstream half-finished rename in the pinned dots snapshot:
#     Config.qml declares  notifications.monitor
#     but NotificationPopup.qml / InterfaceConfig.qml read
#     notifications.forceMonitor  -> "TypeError: Cannot read property 'enable'
#     of undefined", and the notification popup's screen selection breaks.
#     Config.qml IS in installed_listfile, so a dots update reverts this.
python3 - "$II/modules/common/Config.qml" "$II" <<'PY_CFG'
import sys, pathlib
cfg = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
if not cfg.exists():
    print("  UYARI: Config.qml yok, forceMonitor yaması atlandı.")
    sys.exit(0)
src = cfg.read_text(encoding="utf-8")
old = "property JsonObject monitor: JsonObject {"
new = "property JsonObject forceMonitor: JsonObject {"
uses_force = any(
    "forceMonitor" in p.read_text(encoding="utf-8", errors="ignore")
    for p in root.rglob("*.qml") if p != cfg
)
if not uses_force:
    print("  Config.qml: forceMonitor okuyan dosya yok -> yama gereksiz (upstream düzeltmiş).")
elif new in src:
    print("  Config.qml: zaten yamalı -> forceMonitor")
elif src.count(old) == 1:
    cfg.write_text(src.replace(old, new), encoding="utf-8")
    print("  Config.qml: notifications.monitor -> forceMonitor")
elif src.count(old) == 0:
    print("  Config.qml: 'JsonObject monitor' yok -> şema değişmiş, elle bakın.")
else:
    sys.stderr.write("  UYARI: 'JsonObject monitor' birden fazla geçiyor, "
                     "otomatik yama güvenli değil. Elle düzeltin.\n")
PY_CFG

# 2c) Howdy face unlock on the lock screen (pam config + LockContext.qml patch).
#     LockContext.qml is in installed_listfile, so a dots update reverts it.
LOCK="$II/modules/common/panels/lock"
if [ -d "$LOCK" ]; then
    mkdir -p "$LOCK/pam"
    cp "$CUSTOM_DIR/pam/howdy.conf" "$LOCK/pam/howdy.conf"
    python3 "$CUSTOM_DIR/patch-lock-howdy.py" "$II" || rc=1
else
    echo "  UYARI: $LOCK yok, howdy yaması atlandı."
fi

# 2d) Everything-style (#) file search in Overview (Super+B / # prefix).
python3 "$CUSTOM_DIR/patch-everything.py" "$II" || rc=1

# 2d-ai) Antigravity (agy) as default no-key AI backend in Super+A sidebar.
python3 "$CUSTOM_DIR/patch-agy-ai.py" "$II" || rc=1
STATES_JSON="$HOME/.local/state/quickshell/states.json"
if [ -f "$STATES_JSON" ]; then
    python3 - "$STATES_JSON" <<'PY_AI'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
try:
    d = json.loads(p.read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
if d.get("ai", {}).get("model") == "gemini-2.5-flash":
    d["ai"]["model"] = "antigravity"
    p.write_text(json.dumps(d, indent=4) + "\n", encoding="utf-8")
    print("  states.json: varsayilan AI modeli -> antigravity")
PY_AI
fi

# 2d-tr) Merge custom multi-language translations into ~/.config/illogical-impulse/translations/*.json
TR_DIR="$HOME/.config/illogical-impulse/translations"
mkdir -p "$TR_DIR"
python3 - "$CUSTOM_DIR/translations" "$TR_DIR" <<'PY_TR'
import json, pathlib, sys
src_dir, dst_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
if not src_dir.is_dir():
    sys.exit(0)
count = 0
for src_p in sorted(src_dir.glob("*.json")):
    dst_p = dst_dir / src_p.name
    src_data = json.loads(src_p.read_text(encoding="utf-8"))
    dst_data = {}
    if dst_p.exists():
        try:
            dst_data = json.loads(dst_p.read_text(encoding="utf-8"))
        except Exception:
            dst_data = {}
    dst_data.update(src_data)
    dst_p.write_text(json.dumps(dst_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count += 1
print(f"  translations: {count} dil dosyasi guncellendi")
PY_TR

# 2e) User systemd timer to keep the plocate Everything index fresh.
SYSTEMD_USER="$HOME/.config/systemd/user"
if command -v systemctl >/dev/null 2>&1; then
    mkdir -p "$SYSTEMD_USER"
    cat > "$SYSTEMD_USER/everything-index.service" <<EOF
[Unit]
Description=Update user plocate database for Everything (#) search

[Service]
Type=oneshot
ExecStart=$II/scripts/everything-update.sh
Nice=19
IOSchedulingClass=idle
EOF
    cat > "$SYSTEMD_USER/everything-index.timer" <<EOF
[Unit]
Description=Periodically update user plocate database for Everything (#) search

[Timer]
OnBootSec=30s
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    systemctl --user enable --now everything-index.timer >/dev/null 2>&1 || true
    if [ ! -s "${XDG_CACHE_HOME:-$HOME/.cache}/everything/plocate.db" ]; then
        systemctl --user start --no-block everything-index.service >/dev/null 2>&1 || true
    fi
fi

# 3) Reload Quickshell.
touch "$II/shell.qml"

if [ "$rc" -eq 0 ]; then
    echo "✓ Custom bar widget'ları uygulandı, bar yeniden yüklendi."
else
    echo "✗ BarContent yaması kısmen başarısız — yukarıdaki uyarıya bakın."
fi
exit "$rc"
