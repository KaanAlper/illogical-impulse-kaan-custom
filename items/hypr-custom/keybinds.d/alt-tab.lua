if is_file_exists(HOME .. "/.config/quickshell/ii/modules/ii/altSwitcher/AltSwitcher.qml") then
    -- Alt+Tab window switcher (built into the shell): hold Alt, Tab moves forward, Shift+Tab back,
    -- releasing Alt switches to the selection. Alt itself is bound transparently, so applications still get it.
    hl.bind("ALT + Tab", hl.dsp.global("quickshell:altSwitcherNext"), { description = "Shell: Alt+Tab window switcher" })
    hl.bind("ALT + SHIFT + Tab", hl.dsp.global("quickshell:altSwitcherPrev"), { description = "Shell: Alt+Tab window switcher (back)" })
    hl.bind("ALT_L", hl.dsp.global("quickshell:altSwitcherAlt"), { ignore_mods = true, transparent = true })
    hl.bind("ALT_R", hl.dsp.global("quickshell:altSwitcherAlt"), { ignore_mods = true, transparent = true })
end
