-- Instant XANA Wayland curtain matching Plymouth until LockScreen (WlSessionLock) takes over
if is_file_exists(HOME .. "/.config/hypr/custom/bootsplash/shell.qml") then
    hl.exec_cmd("qs -p $HOME/.config/hypr/custom/bootsplash/shell.qml")
end
