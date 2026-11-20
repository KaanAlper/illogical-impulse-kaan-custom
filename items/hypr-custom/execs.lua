-- Commands executed once at Hyprland startup (not on config reload)
hl.on("hyprland.start", function ()
    -- Alt+Tab window switcher daemon
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/alttab/shell.qml")

    -- AsenaDPI tray (Hyprland doesn't run ~/.config/autostart/*.desktop without dex)
    hl.exec_cmd("bash -c '[ -x /usr/local/bin/asena-dpi-tray ] && /usr/local/bin/asena-dpi-tray'")

    -- When SDDM is disabled (greetd autologin), wait for `qs -c ii` IPC, lock, then release Plymouth splash
    hl.exec_cmd("bash -c 'if ! systemctl is-active --quiet sddm; then for i in $(seq 1 150); do qs ipc -c ii show >/dev/null 2>&1 && sleep 0.25 && loginctl lock-session && sleep 0.3 && { sudo -n /usr/bin/plymouth quit 2>/dev/null || true; } && break; sleep 0.1; done; fi'")
end)
