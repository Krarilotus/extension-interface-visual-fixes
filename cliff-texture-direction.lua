local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  -- Both faces meet at the same texture phase. Rotate the map coordinates,
  -- then advance along either adjoining side of the footprint.
  local pattern = "8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00"
  local site = core.AOBScan(pattern)
  if site ~= A.CliffSelector then
    error("Interface and Visual Fixes: unsupported cliff texture selector layout")
  end
  -- Keep the existing graphics refresh and face classification. Use all 32
  -- rock strips; the old clamp duplicated frame1 instead of allowing frame32.
  local code = layout.assemble([[
    push ebx
    mov edx, [ecx+0x55489C]
    cmp edx, 6
    ja fallback
    test edx, 1
    jnz fallback
    mov ebx, [esp+0x1C]
    test edx, 2
    jz x_ready
    neg ebx
  x_ready:
    add esi, ebx
    test edx, 4
    jz phase_ready
    neg esi
  phase_ready:
    and esi, 31
    inc esi
    mov [ecx+0x554908], esi
    pop ebx
    cmp esi, 32
    jmp CliffSelectorReturn
  fallback:
    and esi, 31
    mov edx, 32
    sub edx, esi
    mov [ecx+0x554908], edx
    pop ebx
    jmp CliffSelectorFallback
  ]], site)
  if #code > 93 then error("Interface and Visual Fixes: cliff selector exceeds original space") end
  while #code < 93 do code[#code+1] = 0x90 end
  require("cliff-texture-source").enable()
  core.writeCode(site, code)
end

return M
