if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/everything-query.py") then
    -- Everything-style file search: Super+B opens Super menu with # prefix (AI sidebar already uses Super+A)
    hl.unbind("SUPER + B")
    hl.bind("SUPER + B", hl.dsp.global("quickshell:overviewFilesToggle"), { description = "Search: Files (Everything)" })

    -- All installed apps (A-Z): Super+P opens Super menu with ! prefix
    hl.unbind("SUPER + P")
    hl.bind("SUPER + P", hl.dsp.global("quickshell:overviewAllAppsToggle"), { description = "Search: All apps (A-Z)" })
end
