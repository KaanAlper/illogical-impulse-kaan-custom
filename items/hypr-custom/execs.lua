-- Commands executed once at Hyprland startup (not on config reload)
hl.on("hyprland.start", function ()
    -- Alt+Tab window switcher daemon
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/alttab/shell.qml")

    -- AsenaDPI tray (Hyprland doesn't run ~/.config/autostart/*.desktop without dex)
    hl.exec_cmd("bash -c '[ -x /usr/local/bin/asena-dpi-tray ] && /usr/local/bin/asena-dpi-tray'")

    -- When SDDM is disabled (tty1 autologin), wait for `qs -c ii` IPC (not alttab's qs) and lock immediately
    hl.exec_cmd("bash -c 'if ! systemctl is-active --quiet sddm; then for i in $(seq 1 60); do qs ipc -c ii show >/dev/null 2>&1 && loginctl lock-session && break; sleep 0.1; done; fi'")
end)
