if is_file_exists("/usr/bin/flameshot") then
    -- Screenshot: PrintScreen → Flameshot GUI
    hl.unbind("Print")
    hl.bind("Print", hl.dsp.exec_cmd("flameshot gui"), { description = "Screenshot: Flameshot GUI" })
end
