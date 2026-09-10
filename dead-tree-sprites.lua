local M = {}

function M.enable()
  -- renderMap consumes a frame locally; never change serialized tree state.
  local site = core.AOBScan("69 F6 9C 00 00 00 0F BF 86 58 CC F2 00 85 C0 8B 96 54 CC F2 00 8B 0C 85 90 CE D7 00") + 15
  if site ~= 0x4EB831 then
    error("Interface and Visual Fixes: unsupported tree renderer layout")
  end
  local wrapper = core.allocateCode(48)
  core.writeCode(wrapper, {
    -- TEST EAX flags are consumed after the frame load. ESI is a byte offset.
    0x9C, 0x50,
    0x8B, 0x96, 0x54, 0xCC, 0xF2, 0x00,
    -- Only the fallen-log frame needs correction; flat and animated views keep
    -- their original frame. Native image numbers are one-based.
    0x81, 0xFA, 0x92, 0x00, 0x00, 0x00,
    0x75, 0x19,
    -- Stage 5 is standing dead. Stage 6 retains its log and removal lifecycle.
    0x83, 0xBE, 0xD4, 0xCC, 0xF2, 0x00, 0x05,
    0x75, 0x10,
    0x0F, 0xB7, 0x86, 0x9A, 0xCC, 0xF2, 0x00,
    0x83, 0xE8, 0x01,
    0x83, 0xF8, 0x03,
    0x77, 0x01,
    0x42,
    0x58, 0x9D, core.jmpTo(site + 6),
  })
  core.writeCode(site, {core.jmpTo(wrapper), 0x90})
end

return M
