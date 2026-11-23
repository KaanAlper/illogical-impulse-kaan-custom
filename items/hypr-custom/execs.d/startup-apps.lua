-- Run XDG autostart apps (AsenaDPI, Discord, Flameshot, etc.) after tray is ready
if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/startup-apps.py") then
    hl.exec_cmd("bash -c 'sleep 3 && python3 $HOME/.config/quickshell/ii/scripts/startup-apps.py run-autostart'")
end
