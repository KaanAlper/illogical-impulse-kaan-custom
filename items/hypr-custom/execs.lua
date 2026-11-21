-- Commands executed once at Hyprland startup (not on config reload)
hl.on("hyprland.start", function ()
    -- Instant XANA Wayland curtain matching Plymouth until LockScreen (WlSessionLock) takes over
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/bootsplash/shell.qml")

    -- Alt+Tab window switcher daemon
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/alttab/shell.qml")

    -- AsenaDPI tray (Hyprland doesn't run ~/.config/autostart/*.desktop without dex)
    hl.exec_cmd("bash -c '[ -x /usr/local/bin/asena-dpi-tray ] && /usr/local/bin/asena-dpi-tray'")

    -- Focus configured default monitor (or largest resolution monitor) on startup
    hl.exec_cmd("bash -c 'sleep 0.4; mon=$(python3 -c \"import json,os,subprocess; cfg=json.load(open(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\"))) if os.path.exists(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\")) else {}; pref=cfg.get(\\\"bar\\\",{}).get(\\\"workspaces\\\",{}).get(\\\"defaultMonitor\\\",\\\"\\\"); ms=json.loads(subprocess.check_output([\\\"hyprctl\\\",\\\"monitors\\\",\\\"-j\\\"])); names={m[\\\"name\\\"] for m in ms}; print(pref if pref and pref in names else max(ms, key=lambda m: m[\\\"width\\\"]*m[\\\"height\\\"])[\\\"name\\\"])\" 2>/dev/null); [ -n \"$mon\" ] && hyprctl dispatch \"hl.dsp.focus({monitor = \\\"$mon\\\"})\"'")
end)
