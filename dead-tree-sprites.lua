local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  -- renderMap consumes a frame locally; never change serialized tree state.
  local site = core.AOBScan(layout.patterns.TreeFrameLoad) + 15
  if site ~= A.TreeFrameLoad then
    error("Interface and Visual Fixes: unsupported tree renderer layout")
  end
  local wrapper = core.allocateCode(58)
  core.writeCode(wrapper, {
    -- TEST EAX flags are consumed after the frame load. ESI is a byte offset.
    0x9C, 0x50,
    0x8B, 0x96, {A.TreeFrame},
    -- Only the fallen-log frame needs correction; flat and animated views keep
    -- their original frame. Native image numbers are one-based.
    0x81, 0xFA, 0x92, 0x00, 0x00, 0x00,
    0x75, 0x23,
    -- Stage 5 is standing dead. Stage 6 retains its log and removal lifecycle.
    0x83, 0xBE, {A.TreeStage}, 0x05,
    0x75, 0x1A,
    -- Felling/harvesting leaves stage 5 intact. Keep its original log frame.
    0x66, 0x83, 0xBE, {A.TreeFelling}, 0x00,
    0x75, 0x10,
    0x0F, 0xB7, 0x86, {A.TreeKind},
    0x83, 0xE8, 0x01,
    0x83, 0xF8, 0x03,
    0x77, 0x01,
    0x42,
    0x58, 0x9D, core.jmpTo(site + 6),
  })
  core.writeCode(site, {core.jmpTo(wrapper), 0x90})
end

return M
