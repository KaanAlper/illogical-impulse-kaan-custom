-- Cross-monitor workspace navigation (same rule as the upstream PR): only while the workspaces are split by monitor.
local function workspaces_are_split()
    local f = io.open(HOME .. "/.config/hypr/workspaces.lua", "r")
    if not f then return false end
    local content = f:read("*a")
    f:close()
    return content:find("workspace_rule", 1, true) ~= nil
end

if is_file_exists(HOME .. "/.config/quickshell/ii/scripts/apply-workspace-split.py") and workspaces_are_split() then
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
