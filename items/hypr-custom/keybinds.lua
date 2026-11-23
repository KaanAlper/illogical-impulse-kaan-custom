-- This file will not be overwritten across dots-hyprland updates.
-- The file name is for the sake of organization and does not matter
-- See the corresponding files in ~/.config/hypr/hyprland for examples
-- Each block only applies when the feature it belongs to is installed (its files exist).

if is_file_exists("/usr/bin/flameshot") then
    -- Screenshot: PrintScreen → Flameshot GUI
    hl.unbind("Print")
    hl.bind("Print", hl.dsp.exec_cmd("flameshot gui"), { description = "Screenshot: Flameshot GUI" })
end

if is_file_exists(HOME .. "/.config/quickshell/ii/modules/ii/altSwitcher/AltSwitcher.qml") then
    -- Alt+Tab window switcher (built into the shell): hold Alt, Tab moves forward, Shift+Tab back,
    -- releasing Alt switches to the selection. Alt itself is bound transparently, so applications still get it.
    hl.bind("ALT + Tab", hl.dsp.global("quickshell:altSwitcherNext"), { description = "Shell: Alt+Tab window switcher" })
    hl.bind("ALT + SHIFT + Tab", hl.dsp.global("quickshell:altSwitcherPrev"), { description = "Shell: Alt+Tab window switcher (back)" })
    hl.bind("ALT_L", hl.dsp.global("quickshell:altSwitcherAlt"), { ignore_mods = true, transparent = true })
    hl.bind("ALT_R", hl.dsp.global("quickshell:altSwitcherAlt"), { ignore_mods = true, transparent = true })
end

if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/apply-workspace-split.py") then
    -- Global workspace navigation across monitors (Ctrl+Super+Left/Right steps -1/+1 instead of monitor-locked r-1/r+1)
    hl.unbind("CTRL + SUPER + Left")
    hl.unbind("CTRL + SUPER + Right")
    hl.bind("CTRL + SUPER + Left", hl.dsp.focus({ workspace = "-1" }), { description = "Workspace: Focus prev (cross-monitor)" })
    hl.bind("CTRL + SUPER + Right", hl.dsp.focus({ workspace = "+1" }), { description = "Workspace: Focus next (cross-monitor)" })

    -- Move focused window across workspaces & monitors (Ctrl+Super+Shift+Left/Right steps -1/+1)
    hl.unbind("CTRL + SUPER + SHIFT + Left")
    hl.unbind("CTRL + SUPER + SHIFT + Right")
    hl.bind("CTRL + SUPER + SHIFT + Left", hl.dsp.window.move({ workspace = "-1" }), { description = "Window: Move to prev workspace (cross-monitor)" })
    hl.bind("CTRL + SUPER + SHIFT + Right", hl.dsp.window.move({ workspace = "+1" }), { description = "Window: Move to next workspace (cross-monitor)" })
end

if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/everything-query.py") then
    -- Everything-style file search: Super+B opens Super menu with # prefix (AI sidebar already uses Super+A)
    hl.unbind("SUPER + B")
    hl.bind("SUPER + B", hl.dsp.global("quickshell:overviewFilesToggle"), { description = "Search: Files (Everything)" })

    -- All installed apps (A-Z): Super+P opens Super menu with ! prefix
    hl.unbind("SUPER + P")
    hl.bind("SUPER + P", hl.dsp.global("quickshell:overviewAllAppsToggle"), { description = "Search: All apps (A-Z)" })
end
