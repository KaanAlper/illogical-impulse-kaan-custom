-- Commands executed once at Hyprland startup (not on config reload).
-- Each block only runs when the feature it belongs to is installed (its files exist).
hl.on("hyprland.start", function ()
    -- Instant XANA Wayland curtain matching Plymouth until LockScreen (WlSessionLock) takes over
    if is_file_exists(HOME .. "/.config/hypr/custom/bootsplash/shell.qml") then
        hl.exec_cmd("qs -p $HOME/.config/hypr/custom/bootsplash/shell.qml")
    end

    -- Alt+Tab window switcher daemon
    if is_file_exists(HOME .. "/.config/hypr/custom/alttab/shell.qml") then
        hl.exec_cmd("qs -p $HOME/.config/hypr/custom/alttab/shell.qml")
    end

    -- Run XDG autostart apps (AsenaDPI, Discord, Flameshot, etc.) after tray is ready
    if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/startup-apps.py") then
        hl.exec_cmd("bash -c 'sleep 3 && python3 $HOME/.config/quickshell/ii/scripts/startup-apps.py run-autostart'")
    end

    -- Focus configured default monitor (or largest resolution monitor) on startup
    hl.exec_cmd("bash -c 'sleep 0.4; mon=$(python3 -c \"import json,os,subprocess; cfg=json.load(open(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\"))) if os.path.exists(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\")) else {}; pref=cfg.get(\\\"bar\\\",{}).get(\\\"workspaces\\\",{}).get(\\\"defaultMonitor\\\",\\\"\\\"); ms=json.loads(subprocess.check_output([\\\"hyprctl\\\",\\\"monitors\\\",\\\"-j\\\"])); names={m[\\\"name\\\"] for m in ms}; print(pref if pref and pref in names else max(ms, key=lambda m: m[\\\"width\\\"]*m[\\\"height\\\"])[\\\"name\\\"])\" 2>/dev/null); [ -n \"$mon\" ] && hyprctl dispatch \"hl.dsp.focus({monitor = \\\"$mon\\\"})\"'")
end)
