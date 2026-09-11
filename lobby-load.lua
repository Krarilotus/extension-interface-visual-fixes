local M = {}
local enabled = false

function M.enable()
  if enabled then return end
  local draw = core.AOBScan("83 3D ? ? ? ? 63 0F 84 89 02 00 00 39 2D ? ? ? ? 0F 84 6A 03 00 00")
  local action = core.AOBScan("E8 ? ? ? ? 83 F8 02 7C AE BE 01 00 00 00 6A 09 B9 ? ? ? ? 89 35 ? ? ? ? E8") + 5
  local prepare = core.AOBScan("C7 05 78 7D FE 01 03 00 00 00 89 35 AC 9C FE 01 89 35 B4 7D FE 01")
  -- These predicates belong to the Load cases, not the shared Start/team helper.
  if draw ~= 0x42AFB2 or action ~= 0x4426E0 or prepare ~= 0x42733A
      or core.readInteger(draw + 2) ~= 0x191DD80
      or core.readInteger(0x5E9988) ~= 0x02000003
      or core.readInteger(0x5E998C) ~= 444
      or core.readInteger(0x5E9990) ~= 540
      or core.readInteger(0x5E99A0) ~= 1
      or core.readInteger(0x5E99A8) ~= 0x400001AB
      or core.readInteger(0x5E99AC) ~= 3
      or core.readInteger(0x5E99B4) ~= 0x149 then
    error("Interface and Visual Fixes: unsupported SHC 1.41 lobby Load layout")
  end
  local guard = core.allocateCode(73)
  core.writeCode(guard, {
    0x83, 0x3D, {0x191DD80}, 0x63,
    0x0F, 0x84, {action + 5 - (guard + 13)},
    0x83, 0xF8, 0x02,
    0x0F, 0x8C, {0x442693 - (guard + 22)},
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
    0xC7, 0x05, {0x5E998C}, {444},
    0x83, 0x3D, {0x191DD80}, 0x63,
    0x75, 0x0A,
    0xC7, 0x05, {0x5E998C}, {560},
    0x9D,
    0xC7, 0x05, {0x1FE7D78}, {3},
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
