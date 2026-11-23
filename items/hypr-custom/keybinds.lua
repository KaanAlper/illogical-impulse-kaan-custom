-- This file will not be overwritten across dots-hyprland updates.
-- Feature-specific keybinds live in ~/.config/hypr/custom/keybinds.d/*.lua
-- and are installed as part of their parent feature in dotsync.

for _, name in ipairs({ "flameshot", "alt-tab", "workspace-split", "everything" }) do
    local p = HOME .. "/.config/hypr/custom/keybinds.d/" .. name .. ".lua"
    if is_file_exists(p) then
        dofile(p)
    end
end
