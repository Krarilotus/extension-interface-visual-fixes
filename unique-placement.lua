local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  -- This stack-sensitive acknowledgement is verified for both 1.41 executables.
  -- Failed eligibility/tutorial paths never reach the post-commit notification.
  local site = core.AOBScan("53 B9 ? ? ? ? E8 ? ? ? ? 8B 44 24 2C 83 F8 05 7F 07") + 6
  local entry = core.AOBScan("83 EC 08 53 55 8B 6C 24 18 56 8B F1 8B 4C 24 24")
  if site ~= A.PlacementNotifyCall or entry ~= A.PlacementEntry then
    error("Interface and Visual Fixes: unsupported placement acknowledgement layout")
  end
  local original = site + 5 + core.readInteger(site + 1)
  if original ~= A.MinimapNotify then
    error("Interface and Visual Fixes: placement notification was changed")
  end
  -- At wrapper entry: return-to-command +0x20, actor +0x24, mapper +0x18.
  -- PUSHFD/PUSH EAX add eight bytes to those offsets. The minimap argument and
  -- its this pointer stay untouched; the original function still consumes them.
  local wrapper = core.allocateCode(87)
  core.writeCode(wrapper, {
    -- Preserve the caller's flags and EAX.
    0x9C, 0x50,
    -- Only synchronized placement execution, never AI/setup callers.
    0x81, 0x7C, 0x24, 0x28, {A.PlacementCommandReturn},
    0x75, 0x44,
    -- Leave editor and siege-editor tools alone.
    0x83, 0x3D, {A.GameMode}, 0x01,
    0x74, 0x3B,
    -- Siege-editor mode.
    0x83, 0x3D, {A.GameMode}, 0x06,
    0x74, 0x32,
    -- Placement actor must be the local player.
    0x8B, 0x44, 0x24, 0x2C, 0x3B, 0x05, {A.LocalPlayer},
    0x75, 0x26,
    -- Read the original mapper saved by placeBuilding, not shared command scratch.
    0x8B, 0x44, 0x24, 0x20, 0x83, 0xF8, 0x4D,
    0x74, 0x0B,
    -- Marketplace77 or mercenary post/barracks/guilds86..89.
    0x83, 0xE8, 0x56, 0x83, 0xF8, 0x03,
    0x77, 0x15,
    -- Restore the mapper value after the range check.
    0x83, 0xC0, 0x56,
    -- Do not clear a cancelled or different selected tool.
    0x39, 0x86, 0xE4, 0x48, 0x55, 0x00,
    0x75, 0x0A,
    -- Clear the existing build tool; its normal renderer removes the preview.
    0xC7, 0x86, 0xE4, 0x48, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00,
    -- Restore ABI and tail-call the original minimap notification.
    0x58, 0x9D,
    core.jmpTo(original),
  })
  core.writeCode(site, {core.callTo(wrapper)})
end

return M
