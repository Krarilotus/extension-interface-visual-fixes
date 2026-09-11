local layout = require("native-layout")
local A = layout.addresses
-- One map-render entry hook shared by presentation-only caches.
local epoch
local M = {}

function M.getEpoch()
  if epoch then return epoch end
  local pattern = layout.patterns.RenderMapEntry
  if core.AOBScan(pattern) ~= A.RenderMapEntry then
    error("Interface and Visual Fixes: unsupported map renderer layout")
  end
  epoch = core.allocate(4, true)
  local entry = layout.allocateAssembly(string.format([[
    pushfd
    inc dword [%d]
    popfd
    sub esp, 0x64
    mov eax, [RenderMapState]
    jmp RenderMapResume
  ]], epoch))
  core.writeCode(A.RenderMapEntry, {core.jmpTo(entry), 0x90, 0x90, 0x90})
  return epoch
end

return M
