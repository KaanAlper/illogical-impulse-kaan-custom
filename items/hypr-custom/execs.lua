-- Commands executed once at Hyprland startup (not on config reload)
hl.on("hyprland.start", function ()
    -- Instant XANA Wayland curtain matching Plymouth until LockScreen (WlSessionLock) takes over
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/bootsplash/shell.qml")

    -- Alt+Tab window switcher daemon
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/alttab/shell.qml")

    -- AsenaDPI tray (Hyprland doesn't run ~/.config/autostart/*.desktop without dex)
    hl.exec_cmd("bash -c '[ -x /usr/local/bin/asena-dpi-tray ] && /usr/local/bin/asena-dpi-tray'")
end)
