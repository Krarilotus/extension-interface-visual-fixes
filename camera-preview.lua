local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  -- The existing handler has already computed building size and mouse world XY.
  -- Restrict the added idle path to positive-size building/brush previews; unit,
  -- assembly-point and other special tools retain their original scrolling gate.
  local site = core.AOBScan(layout.patterns.CameraPreview) + 6
  if site ~= A.CameraPreviewBranch then
    error("Interface and Visual Fixes: unsupported camera preview layout")
  end
  local resume = site + 6
  local finish = A.CameraPreviewExit
  local wrapper = core.allocateCode(39)
  core.writeCode(wrapper, {
    -- Preserve the original scrolling comparison flags and every register.
    0x9C,
    -- Not scrolling: resume the original path immediately.
    0x74, 0x18,
    -- EBX is zero here. Non-building tools keep the original early return.
    0x39, 0x1D, {A.PreviewWidth},
    0x7E, 0x16,
    -- Held and release events retain the original scrolling behavior. A new
    -- left-click already bypasses this gate in the unmodified caller.
    0x39, 0x1D, {A.LeftHeld},
    0x75, 0x0E,
    0x39, 0x1D, {A.LeftReleased},
    0x75, 0x06,
    0x9D, core.jmpTo(resume),
    0x9D, core.jmpTo(finish),
  })
  core.writeCode(site, {core.jmpTo(wrapper), 0x90})
end

return M
