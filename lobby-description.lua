local A = require("native-layout").addresses
local M = {}

function M.enable()
  -- The shared name lookup sets a global flag for shipped maps, but leaves it
  -- unchanged for custom names. Rendering another lobby row can therefore hide
  -- the selected map's embedded description. Rebind at the existing lookup.
  local site, choice = A.LobbyDescriptionCall, A.LobbyDescriptionChoice
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
