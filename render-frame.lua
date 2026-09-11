-- One map-render entry hook shared by presentation-only caches.
local epoch
local M = {}

function M.getEpoch()
  if epoch then return epoch end
  local pattern = "83 EC 64 A1 94 83 F9 00 53 55 56 8B D9 57 33 FF 33 F6"
  if core.AOBScan(pattern) ~= 0x4E8CF0 then
    error("Interface and Visual Fixes: unsupported map renderer layout")
  end
  epoch = core.allocate(4, true)
  local entry = core.allocateAssembly(string.format([[
    pushfd
    inc dword [%d]
    popfd
    sub esp, 0x64
    mov eax, [0xF98394]
    jmp 0x4E8CF8
  ]], epoch))
  core.writeCode(0x4E8CF0, {core.jmpTo(entry), 0x90, 0x90, 0x90})
  return epoch
end

return M
