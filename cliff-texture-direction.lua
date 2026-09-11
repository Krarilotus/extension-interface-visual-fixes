local M = {}

function M.enable()
  -- computeClimbRampRotation has already classified the visible cliff faces.
  -- Its old orientations 2/6 use Y for both faces, repeating along the X axis.
  local pattern = "8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00"
  local site = core.AOBScan(pattern)
  if site ~= 0x4FC95C then
    error("Interface and Visual Fixes: unsupported cliff texture selector layout")
  end
  -- Replace the calculation in place. No allocation, new callback or render
  -- hook: the caller stores this result in its existing terrain graphics layer.
  -- Preserve EAX (face classification) and the original range clamp/epilogue.
  local code = core.assemble([[
    mov edx, [ecx+0x55489C]
    cmp edx, 6
    ja fallback
    test edx, 1
    jnz fallback
    test edx, 2
    jz unrotated_axes
    cmp eax, 1
    jne use_x
    xor edx, 4
    jmp coordinate_ready
  unrotated_axes:
    cmp eax, 1
    jne coordinate_ready
  use_x:
    mov esi, [esp+0x18]
  coordinate_ready:
    and esi, 31
    test edx, 4
    jnz increasing
  decreasing:
    mov edx, 32
    sub edx, esi
    jmp store_offset
  increasing:
    lea edx, [esi+1]
  store_offset:
    mov [ecx+0x554908], edx
    jmp 0x4FC9B9
  fallback:
    and esi, 31
    jmp decreasing
  ]], {}, site)
  if #code > 93 then error("Interface and Visual Fixes: cliff selector exceeds original space") end
  while #code < 93 do code[#code+1] = 0x90 end
  core.writeCode(site, code)
end

return M
