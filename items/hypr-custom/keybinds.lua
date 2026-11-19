-- This file will not be overwritten across dots-hyprland updates.
-- The file name is for the sake of organization and does not matter
-- See the corresponding files in ~/.config/hypr/hyprland for examples

-- Window close: use Alt+F4 only, remove Super+Q and the "wrong keybind" notify
hl.unbind("SUPER + Q")
hl.unbind("ALT + F4")
hl.bind("ALT + F4", hl.dsp.window.close(), { description = "Window: Close" })

-- Screenshot: PrintScreen → Flameshot GUI
hl.unbind("Print")
hl.bind("Print", hl.dsp.exec_cmd("flameshot gui"), { description = "Screenshot: Flameshot GUI" })

-- Alt+Tab window switcher (custom/alttab/shell.qml): hold Alt, Tab moves forward, Shift+Tab back,
-- releasing Alt switches to the selection. Alt itself is bound transparently, so applications still get it.
hl.bind("ALT + Tab", hl.dsp.global("alttab:next"), { description = "Window: Alt+Tab switcher" })
hl.bind("ALT + SHIFT + Tab", hl.dsp.global("alttab:prev"), { description = "Window: Alt+Tab switcher (back)" })
hl.bind("ALT_L", hl.dsp.global("alttab:alt"), { ignore_mods = true, transparent = true })
hl.bind("ALT_R", hl.dsp.global("alttab:alt"), { ignore_mods = true, transparent = true })

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

-- MSI fan toggle — SUPER+F12 yedek, F12 alone başka uygulamalarda kalabilir
-- (Fn+F12 ve F12 Linux'ta aynı keysym üretiyor — donanım Fn'i yutuyor)
hl.bind("SUPER + F12", hl.dsp.exec_cmd("/home/kaanalper/.local/bin/msi-fan-toggle"), { description = "MSI Fan: Toggle Max/Auto" })

-- Everything-style file search: Super+B opens Super menu with # prefix (AI sidebar already uses Super+A)
hl.unbind("SUPER + B")
hl.bind("SUPER + B", hl.dsp.global("quickshell:overviewFilesToggle"), { description = "Search: Files (Everything)" })

-- All installed apps (A-Z): Super+P opens Super menu with ! prefix
hl.unbind("SUPER + P")
hl.bind("SUPER + P", hl.dsp.global("quickshell:overviewAllAppsToggle"), { description = "Search: All apps (A-Z)" })
