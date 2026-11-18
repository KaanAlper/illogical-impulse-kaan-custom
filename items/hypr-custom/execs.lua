-- Commands executed once at Hyprland startup (not on config reload)
hl.on("hyprland.start", function ()
    -- When SDDM is disabled (tty1 autologin), lock immediately into the Super+L screen on boot
    hl.exec_cmd("bash -c 'if ! systemctl is-active --quiet sddm; then for i in $(seq 1 40); do pidof qs >/dev/null && sleep 0.4 && loginctl lock-session && break; sleep 0.2; done; fi'")
end)
