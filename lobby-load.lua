local layout = require("native-layout")
local A = layout.addresses
local M = {}
local enabled = false

function M.enable()
  if enabled then return end
  local draw, action, prepare = A.LobbyLoadDraw, A.LobbyLoadAction, A.LobbyPrepare
  local guard = core.allocateCode(73)
  core.writeCode(guard, {
    0x83, 0x3D, {A.LobbyMode}, 0x63,
    0x0F, 0x84, {action + 5 - (guard + 13)},
    0x83, 0xF8, 0x02,
    0x0F, 0x8C, {A.LobbyLoadReject - (guard + 22)},
    core.jmpTo(action + 5),
  })
  -- Set the existing item's position during lobby preparation, before native
  -- rendering and input. The 45x58 scroll fits between the master portrait
  -- (right edge 529) and Start's hit rectangle (left edge 620). Restore the
  -- original position for every other mode, including SP -> MP navigation.
  -- Preserve flags/registers and replay the displaced secondary-mode write.
  local position = guard + 27
  core.writeCode(position, {
    0x9C,
    0xC7, 0x05, {A.LobbyLoadX}, {444},
    0x83, 0x3D, {A.LobbyMode}, 0x63,
    0x75, 0x0A,
    0xC7, 0x05, {A.LobbyLoadX}, {560},
    0x9D,
    0xC7, 0x05, {A.GameMode}, 0x03, 0x00, 0x00, 0x00,
    core.jmpTo(prepare + 10),
  })
  -- Single-player draws through the original active-button block. Multiplayer
  -- retains its original fallthrough, host/readiness checks and rendering.
  core.writeCode(draw + 7, {0x0F, 0x84, 0x3E, 0x00, 0x00, 0x00})
  core.writeCode(action, {core.jmpTo(guard)})
  core.writeCode(prepare, {core.jmpTo(position), 0x90, 0x90, 0x90, 0x90, 0x90})
  enabled = true
end

return M
