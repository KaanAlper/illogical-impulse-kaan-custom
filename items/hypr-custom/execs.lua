-- Commands executed once at Hyprland startup (not on config reload).
-- Feature-specific startup hooks live in ~/.config/hypr/custom/execs.d/*.lua
-- and are installed as part of their parent feature in dotsync.

hl.on("hyprland.start", function ()
    for _, name in ipairs({ "bootsplash", "startup-apps" }) do
        local p = HOME .. "/.config/hypr/custom/execs.d/" .. name .. ".lua"
        if is_file_exists(p) then
            dofile(p)
        end
    end

    -- AsenaDPI DPI/DNS-bypass tray (eski zapret-tray kaldirildi)
    hl.exec_cmd("sleep 7 && /usr/local/bin/asena-dpi-tray")
    -- Waydroid tray indicator (launch TFT / show full UI / start/restart/stop session)
    hl.exec_cmd("sleep 4 && $HOME/.local/bin/waydroid-tray")
    -- BT profile tray (A2DP <-> HFP toggle, autoswitch kapalı olduğu için manual)
    hl.exec_cmd("sleep 4 && $HOME/.local/bin/bt-tray")
    -- hypridle'i custom config ile yeniden baslat: suspend timeout 90 dk (end-4 ana hypridle.conf'u ezse bile korunur)
    hl.exec_cmd("sleep 4; pkill -x hypridle; hypridle -c $HOME/.config/hypr/custom/hypridle.conf")
    -- ii kilit ekranı yüz tanıma (Howdy) yaması dots güncellemesinde silinmişse kendiliğinden geri yükle.
    hl.exec_cmd("sleep 3; grep -qs faceState $HOME/.config/quickshell/ii/modules/ii/lock/LockSurface.qml || $HOME/.config/quickshell-custom/apply.sh")
    -- dotsync: GitHub'daki kaan-dots ile yerel ayarları karşılaştırır; yalnızca eksik bir şey varsa pencere açar.
    hl.exec_cmd("sleep 12; $HOME/.local/bin/dotsync boot")
    -- MSI fan/performans kontrolü (MControlCenter), SNI host hazır olsun diye 4sn bekliyor
    hl.exec_cmd("sleep 4 && mcontrolcenter")

    -- Focus configured default monitor (or largest resolution monitor) on startup
    hl.exec_cmd("bash -c 'sleep 0.4; mon=$(python3 -c \"import json,os,subprocess; cfg=json.load(open(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\"))) if os.path.exists(os.path.expanduser(\\\"~/.config/illogical-impulse/config.json\\\")) else {}; pref=cfg.get(\\\"bar\\\",{}).get(\\\"workspaces\\\",{}).get(\\\"defaultMonitor\\\",\\\"\\\"); ms=json.loads(subprocess.check_output([\\\"hyprctl\\\",\\\"monitors\\\",\\\"-j\\\"])); names={m[\\\"name\\\"] for m in ms}; print(pref if pref and pref in names else max(ms, key=lambda m: m[\\\"width\\\"]*m[\\\"height\\\"])[\\\"name\\\"])\" 2>/dev/null); [ -n \"$mon\" ] && hyprctl dispatch \"hl.dsp.focus({monitor = \\\"$mon\\\"})\"'")
end)
