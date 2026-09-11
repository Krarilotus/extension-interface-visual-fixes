local M = {}

function M.enable()
  -- The existing handler has already computed building size and mouse world XY.
  -- Restrict the added idle path to positive-size building/brush previews; unit,
  -- assembly-point and other special tools retain their original scrolling gate.
  local site = core.AOBScan("39 1D 70 B0 12 01 0F 85 59 15 00 00 8B 3D E0 EB 1A 02") + 6
  if site ~= 0x445263 then
    error("Interface and Visual Fixes: unsupported camera preview layout")
  end
  local resume = site + 6
  local finish = 0x4467C2
  local wrapper = core.allocateCode(39)
  core.writeCode(wrapper, {
    -- Preserve the original scrolling comparison flags and every register.
    0x9C,
    -- Not scrolling: resume the original path immediately.
    0x74, 0x18,
    -- EBX is zero here. Non-building tools keep the original early return.
    0x39, 0x1D, 0xF0, 0x7A, 0xFE, 0x01,
    0x7E, 0x16,
    -- Held and release events retain the original scrolling behavior. A new
    -- left-click already bypasses this gate in the unmodified caller.
    0x39, 0x1D, 0xF0, 0xC9, 0xF2, 0x00,
    0x75, 0x0E,
    0x39, 0x1D, 0xD8, 0xC9, 0xF2, 0x00,
    0x75, 0x06,
    0x9D, core.jmpTo(resume),
    0x9D, core.jmpTo(finish),
  })
  core.writeCode(site, {core.jmpTo(wrapper), 0x90})
end

return M
