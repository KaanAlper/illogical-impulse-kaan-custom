# Auto-start Hyprland on tty1 login when SDDM is disabled
if status is-login
    if test (tty) = "/dev/tty1"; and not set -q WAYLAND_DISPLAY
        if not systemctl is-active --quiet sddm
            exec /usr/bin/start-hyprland
        end
    end
end
