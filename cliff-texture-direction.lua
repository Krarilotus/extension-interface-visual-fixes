local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  -- One image contains consecutive left/right face strips. Its base phase
  -- follows the horizontal projection, including two steps per front diagonal.
  local pattern = "8B 91 9C 48 55 00 85 D2 75 1B 83 F8 01 75 3E 8B 54 24 18 83 E2 1F BE 20 00 00 00 2B F2 89 B1 08 49 55 00 EB 38 83 FA 04 75 10 83 F8 01 75 10 8B 54 24 18 83 E2 1F 03 D0 EB 1D 83 FA 02 75 0E 83 E6 1F 83 C6 01 89 B1 08 49 55 00 EB 10 83 E6 1F BA 20 00 00 00 2B D6 89 91 08 49 55 00"
  local site = core.AOBScan(pattern)
  if site ~= A.CliffSelector then
    error("Interface and Visual Fixes: unsupported cliff texture selector layout")
  end
  -- Keep the existing graphics refresh and face classification. Use all 32
  -- rock strips; the old clamp duplicated frame1 instead of allowing frame32.
  local selector = layout.allocateAssembly([[
    pushfd
    pushad
    mov edx, [ecx+0x55489C]
    cmp edx, 6
    ja fallback
    test edx, 1
    jnz fallback
    ; A depth-facing staircase has overlapping faces at the same screen X.
    ; Detect its local continuation during the existing terrain refresh only.
    cmp eax, 1
    je left_face
    cmp eax, 2
    jne projected
    mov eax, [ecx+0x5548A8]
    jmp check_depth
  left_face:
    mov eax, [ecx+0x5548AC]
  check_depth:
    mov ebx, [esp+0x3C]
    mov ebp, [esp+4]
    mov esi, [esp+0x38]
    mov edi, [ecx+0x5548A4]
    push eax
    call depth_stair
    test eax, eax
    jnz depth_found
    mov eax, [esp]
    xor edi, 4
    call depth_stair
  depth_found:
    pop edx
    test eax, eax
    jz projected
    ; Stable coordinate variation, never the simulation RNG or a frame counter.
    imul esi, [esp+0x3C], 0x1F123BB5
    imul edx, [esp+4], 0x5F356495
    xor esi, edx
    mov edx, esi
    shr edx, 16
    xor esi, edx
    jmp phase_ready
  projected:
    mov edx, [ecx+0x55489C]
    mov ebx, [esp+0x3C]
    mov esi, [esp+4]
    test edx, 2
    jz x_ready
    neg ebx
  x_ready:
    neg esi
    add esi, ebx
    test edx, 4
    jz phase_ready
    neg esi
  phase_ready:
    and esi, 31
    inc esi
    mov [ecx+0x554908], esi
    mov [esp+4], esi
    popad
    popfd
    cmp esi, 32
    jmp CliffSelectorReturn
  fallback:
    popad
    popfd
    and esi, 31
    mov edx, 32
    sub edx, esi
    mov [ecx+0x554908], edx
    jmp CliffSelectorFallback

  depth_stair:
    ; EAX outward direction, EDI depth direction, EBX/EBP tile X/Y,
    ; ESI effective height, ECX map. Return true only for an equally high
    ; diagonal neighbour with the same exposed outward side. Check both ends
    ; of a run without walking its boundary or keeping per-tile state.
    pushad
    cmp eax, 7
    ja not_depth
    cmp ebx, 399
    ja not_depth
    cmp ebp, 399
    ja not_depth
    lea edx, [ebp+ebp*2]
    mov edx, [edx*4+TileRows]
    add edx, ebx
    mov ebx, ebp
    shl ebx, 5
    lea ebx, [ebx+edi*4]
    add edx, [ecx+ebx]
    cmp edi, 1
    je previous_row
    cmp edi, 7
    je previous_row
    cmp edi, 3
    je next_row
    cmp edi, 5
    jne not_depth
  next_row:
    inc ebp
    jmp row_ready
  previous_row:
    dec ebp
  row_ready:
    cmp ebp, 399
    ja not_depth
    cmp edx, 80399
    ja not_depth
    test dword [edx*4+TileLogic], 0x30
    jnz not_depth
    movzx ebx, byte [edx+TileHeight]
    test dword [edx*4+TileLogic], 0x100
    jz neighbour_height
    movzx ebx, byte [edx+TileTerrain]
  neighbour_height:
    cmp ebx, esi
    jne not_depth
    shl ebp, 5
    lea ebp, [ebp+eax*4]
    add edx, [ecx+ebp]
    cmp edx, 80399
    ja not_depth
    test dword [edx*4+TileLogic], 0x30
    jnz not_depth
    movzx ebx, byte [edx+TileHeight]
    test dword [edx*4+TileLogic], 0x100
    jz outward_height
    movzx ebx, byte [edx+TileTerrain]
  outward_height:
    cmp ebx, 136
    jae not_depth
    add ebx, 20
    cmp esi, ebx
    jle not_depth
    mov eax, 1
    jmp depth_done
  not_depth:
    xor eax, eax
  depth_done:
    mov [esp+28], eax
    popad
    ret
  ]])
  require("cliff-texture-source").enable()
  local code = {core.jmpTo(selector)}
  for _ = 6, 93 do code[#code+1] = 0x90 end
  core.writeCode(site, code)
end

return M
