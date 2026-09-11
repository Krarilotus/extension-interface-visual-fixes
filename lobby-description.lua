local M = {}

function M.enable()
  -- The shared name lookup sets a global flag for shipped maps, but leaves it
  -- unchanged for custom names. Rendering another lobby row can therefore hide
  -- the selected map's embedded description. Rebind at the existing lookup.
  local site = core.AOBScan("8D 44 24 14 50 68 ? ? ? ? E8 ? ? ? ? 8B C8 A1 ? ? ? ? 83 C0 E0 C1 E0 05 99 83 E2 1F") + 10
  local choice = core.AOBScan("83 3D ? ? ? ? 00 75 ? A1 ? ? ? ? 8B 0D ? ? ? ? 2B 35 ? ? ? ? 83 C0 E0 C1 E0 05")
  if choice - site ~= 0xEB then
    error("Interface and Visual Fixes: unsupported lobby description layout")
  end
  local sourceFlag = core.readInteger(choice + 2)
  local lookup = site + 5 + core.readInteger(site + 1)
  local wrapper = core.allocateCode(15)
  core.writeCode(wrapper, {
    0xC7, 0x05, {sourceFlag}, 0x00, 0x00, 0x00, 0x00,
    core.jmpTo(lookup),
  })
  -- Tail-jump to the original lookup: same arguments, return value and ABI.
  -- MOV/JMP preserve its incoming flags and registers. No additional lookup.
  core.writeCode(site, {core.callTo(wrapper)})
end

return M
