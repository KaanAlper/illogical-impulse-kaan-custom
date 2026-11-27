-- Commands executed once at Hyprland startup (not on config reload).
-- Feature-specific startup hooks live in ~/.config/hypr/custom/execs.d/*.lua
-- (installed by dotsync features, or add your own: every file there is loaded automatically).

hl.on("hyprland.start", function ()
    -- Load every execs.d/*.lua hook (dotsync features and anything you add yourself).
    -- A file dropped in there starts automatically; a broken one never blocks the rest.
    local ls = io.popen("ls -1 \"" .. HOME .. "/.config/hypr/custom/execs.d/\"*.lua 2>/dev/null")
    if ls then
        for p in ls:lines() do
            local ok, err = pcall(dofile, p)
            if not ok then
                print("execs.d: " .. p .. ": " .. tostring(err))
            end
        end
        ls:close()
    end

    -- Focus configured default monitor (or largest resolution monitor) on startup
    hl.exec_cmd("bash -c 'sleep 0.4; mon=$(python3 -c \"import json,os,subprocess; cfg=json.load(open(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\"))) if os.path.exists(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\")) else {}; pref=cfg.get(\\\"bar\\\",{}).get(\\\"workspaces\\\",{}).get(\\\"defaultMonitor\\\",\\\"\\\"); ms=json.loads(subprocess.check_output([\\\"hyprctl\\\",\\\"monitors\\\",\\\"-j\\\"])); names={m[\\\"name\\\"] for m in ms}; print(pref if pref and pref in names else max(ms, key=lambda m: m[\\\"width\\\"]*m[\\\"height\\\"])[\\\"name\\\"])\" 2>/dev/null); [ -n \"$mon\" ] && hyprctl dispatch \"hl.dsp.focus({monitor = \\\"$mon\\\"})\"'")
end)
