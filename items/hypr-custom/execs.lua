-- Commands executed once at Hyprland startup (not on config reload).
-- Feature-specific startup hooks live in ~/.config/hypr/custom/execs.d/*.lua
-- and are installed as part of their parent feature in dotsync.

hl.on("hyprland.start", function ()
    for _, name in ipairs({ "bootsplash", "startup-apps", "personal" }) do
        local p = HOME .. "/.config/hypr/custom/execs.d/" .. name .. ".lua"
        if is_file_exists(p) then
            dofile(p)
        end
    end

    -- Focus configured default monitor (or largest resolution monitor) on startup
    hl.exec_cmd("bash -c 'sleep 0.4; mon=$(python3 -c \"import json,os,subprocess; cfg=json.load(open(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\"))) if os.path.exists(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\")) else {}; pref=cfg.get(\\\"bar\\\",{}).get(\\\"workspaces\\\",{}).get(\\\"defaultMonitor\\\",\\\"\\\"); ms=json.loads(subprocess.check_output([\\\"hyprctl\\\",\\\"monitors\\\",\\\"-j\\\"])); names={m[\\\"name\\\"] for m in ms}; print(pref if pref and pref in names else max(ms, key=lambda m: m[\\\"width\\\"]*m[\\\"height\\\"])[\\\"name\\\"])\" 2>/dev/null); [ -n \"$mon\" ] && hyprctl dispatch \"hl.dsp.focus({monitor = \\\"$mon\\\"})\"'")
end)
