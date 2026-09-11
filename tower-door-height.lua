local M = {}

function M.enable()
  -- Existing renderGmOverlayBuilding2 calls, including the shared exit draw.
  -- Validate every site before allocating or writing anything.
  local sites = {
    {0x4E3681, "DC 52 50 6A 36 B9 90 A0 FE 01 E8 7A 1C F7 FF"},
    {0x4E36D1, "DC 52 50 6A 36 B9 90 A0 FE 01 E8 2A 1C F7 FF"},
    {0x4E3724, "CC 52 50 6A 36 B9 90 A0 FE 01 E8 D7 1B F7 FF"},
    {0x4E3777, "CD 52 50 6A 36 B9 90 A0 FE 01 E8 84 1B F7 FF"},
    {0x4E3807, "03 D5 52 51 50 B9 90 A0 FE 01 E8 F4 1A F7 FF"},
  }
  for _, site in ipairs(sites) do
    if core.AOBScan(site[2]) + 10 ~= site[1] then
      error("Interface and Visual Fixes: unsupported tower door renderer layout")
    end
  end

  local updateSites = {
    {0x4E8CF0, "83 EC 64 A1 94 83 F9 00 53 55 56 8B D9 57 33 FF 33 F6"},
    {0x4EBA52, "E8 A9 80 F6 FF 83 7C 24 54 00 74 34"},
    {0x41B7FF, "89 9C 0F 94 02 00 00"},
    {0x41B855, "03 81 28 E0 18 00 8B 04 85 68 83 BF 01 A9 00 01 00 00 74 1C A8 02 75 18 A9", 6},
    {0x512450, "51 A1 54 EC 1A 02 53 55 8B 2D 50 EC 1A 02 56 89 44 24 0C"},
    {0x50EDAF, "66 89 84 51 E0 80 0C 00 EB 6A 8B 95 1C FF FF FF 8B 82 08 49 55 00 8B 0D B4 CE D7 00 8D 54 01 FF", 10},
  }
  for _, site in ipairs(updateSites) do
    if core.AOBScan(site[2]) + (site[3] or 0) ~= site[1] then
      error("Interface and Visual Fixes: unsupported tower connection update layout")
    end
  end

  -- Lower doors cross the row where vanilla draws the building overlay.
  -- Foundation columns in later rows would erase them. Keep each affected draw
  -- until its own face has been painted through the sprite's horizontal extent.
  -- This is per-frame drawing state, independent of connection discovery.
  local depth = core.allocate(2048 * 40, true)
  local frameEpoch = require("render-frame").getEpoch()
  local depthAddress = string.format([[
    mov edi, esi
    shr edi, 2
    and edi, 2047
    lea edi, [edi+edi*4]
    lea edi, [edi*8+%d]
  ]], depth)
  local initializeDepth = core.allocateAssembly(string.format([[
    mov eax, [%d]
    cmp [edi], eax
    je ready
    mov [edi], eax
    mov dword [edi+4], 0x80000000
    mov dword [edi+8], 0x7FFFFFFF
    mov dword [edi+12], 0
  ready:
    ret
  ]], frameEpoch))
  local deferredDraw = core.allocateAssembly([[
    pushfd
    pushad
  ]] .. depthAddress .. string.format([[
    call %d
    mov ecx, [esp+48]
    mov edx, [esp+52]
    cmp dword [esp+44], 81
    jne right_face
    mov eax, [0xD7CF68]
    add eax, 80
    shl eax, 4
    movzx eax, word [eax+0xB98790]
    add eax, ecx
    cmp [edi+4], eax
    jge immediate
    mov [edi+16], ecx
    mov [edi+20], edx
    mov [edi+24], eax
    or dword [edi+12], 1
    jmp queued
  right_face:
    cmp [edi+8], ecx
    jle immediate
    mov [edi+28], ecx
    mov [edi+32], edx
    or dword [edi+12], 2
  queued:
    mov eax, [0x21AEC4C]
    movzx eax, word [eax]
    mov [edi+36], eax
    popad
    popfd
    ret 16
  immediate:
    popad
    popfd
    jmp 0x455300
  ]], initializeDepth))
  local foundationDraw = core.allocateAssembly([[
    call 0x453B00
    pushfd
    pushad
    movzx esi, word [ebp*2+0x1C95BB8]
    test esi, esi
    jz done
    cmp esi, 2000
    jae done
    imul esi, esi, 812
    movzx eax, word [esi+0xF98606]
    sub eax, 75
    cmp eax, 3
    ja done
  ]] .. depthAddress .. string.format([[
    call %d
    mov eax, [0xED3178]
    mov edx, [0xED317C]
    cmp edx, 1
    je right_extent
    lea ecx, [eax+16]
    cmp [edi+4], ecx
    jge right_extent
    mov [edi+4], ecx
  right_extent:
    cmp edx, 2
    je paint_ready
    add eax, 14
    cmp [edi+8], eax
    jle paint_ready
    mov [edi+8], eax
  paint_ready:
    cmp dword [edi+12], 0
    je done
    push dword [0xED3158]
    push dword [0xED3180]
    mov ebp, [0x21AEC4C]
    movzx eax, word [ebp]
    push eax
    mov ax, [edi+36]
    mov [ebp], ax
    mov dword [0xED3158], 0
    mov dword [0xED3180], 54
    test dword [edi+12], 1
    jz paint_right
    mov eax, [edi+24]
    cmp [edi+4], eax
    jl paint_right
    and dword [edi+12], -2
    push dword [edi+20]
    push dword [edi+16]
    push 81
    push 54
    mov ecx, 0x1FEA090
    call 0x455300
  paint_right:
    test dword [edi+12], 2
    jz restore_draw_state
    mov eax, [edi+28]
    cmp [edi+8], eax
    jg restore_draw_state
    and dword [edi+12], -3
    push dword [edi+32]
    push dword [edi+28]
    push 90
    push 54
    mov ecx, 0x1FEA090
    call 0x455300
  restore_draw_state:
    pop eax
    mov [ebp], ax
    pop dword [0xED3180]
    pop dword [0xED3158]
  done:
    popad
    popfd
    ret
  ]], initializeDepth))

  -- Private presentation state; never serialized or stored in building records.
  -- (building byte offset / 4) modulo 2048 is a collision-free permutation
  -- for IDs 0..1999: the native stride / 4 is the odd number 203.
  -- Each entry holds UID, origin, four ranked connections, valid sides, epoch.
  local cache = core.allocate(2048 * 32 + 4, true)
  local epoch = cache + 2048 * 32
  local address = string.format([[
    mov edi, esi
    shr edi, 2
    and edi, 2047
    shl edi, 5
    add edi, %d
  ]], cache)
  local initialize = core.allocateAssembly(address .. string.format([[
    mov eax, [esi+0xF9860C]
    mov [edi], eax
    mov eax, [esi+0xF98628]
    mov [edi+4], eax
    xor eax, eax
    mov [edi+8], eax
    mov [edi+12], eax
    mov [edi+16], eax
    mov [edi+20], eax
    mov [edi+24], eax
    mov eax, [%d]
    mov [edi+28], eax
    ret
  ]], epoch))

  -- Rank one tile the native connection loop already visits. Highest height
  -- wins, then closest to the side centre, then first in native boundary order.
  -- Raised stairs cannot enter a tower. Native stair6 has no raised-stair flag
  -- and retains terrain height. Below-base joins require the adjacent inner tile
  -- to belong to this tower, so the refreshed masonry supplies the backing.
  -- EAX=tile, EBX=boundary index, ECX=width, ESI=building offset
  -- -> EAX=rank, EDX=side.
  local rank = core.allocateAssembly([[
    push ebx
    push ecx
    push esi
    push edi
    push ebp
    cmp eax, 80400
    jae absent
    mov edx, [eax*4+0x1BF8368]
    and edx, 0xB02
    cmp edx, 0x100
    jne absent
    movzx edi, byte [eax+0x1D32C38]
    mov ebp, [esi+0xF98628]
    cmp ebp, 80400
    jae absent
    movzx ebp, byte [ebp+0x1D46648]
    cmp edi, ebp
    jae eligible
    mov eax, ebx
    xor edx, edx
    div ecx
    movzx ebx, word [esi+0xF98622]
    movzx ebp, word [esi+0xF98624]
    test eax, eax
    jz north_backing
    cmp eax, 1
    je east_backing
    cmp eax, 2
    je south_backing
    add ebp, ecx
    sub ebp, edx
    dec ebp
    jmp backing_tile
  north_backing:
    add ebx, edx
    jmp backing_tile
  east_backing:
    lea ebx, [ebx+ecx-1]
    add ebp, edx
    jmp backing_tile
  south_backing:
    lea ebx, [ebx+ecx-1]
    sub ebx, edx
    lea ebp, [ebp+ecx-1]
  backing_tile:
    cmp ebx, 400
    jae absent
    cmp ebp, 400
    jae absent
    lea eax, [ebp+ebp*2]
    mov eax, [eax*4+0x2337300]
    add eax, ebx
    cmp eax, 80400
    jae absent
    movzx eax, word [eax*2+0x1C95BB8]
    imul eax, eax, 812
    cmp eax, esi
    jne absent
    mov ebx, [esp+16]
  eligible:
    inc edi
    shl edi, 16
    mov eax, ebx
    xor edx, edx
    div ecx
    mov esi, eax
    mov ebp, edx
    lea eax, [edx+edx]
    sub eax, ecx
    inc eax
    cdq
    xor eax, edx
    sub eax, edx
    mov edx, 8
    sub edx, eax
    shl edx, 8
    or edi, edx
    mov eax, 8
    sub eax, ebp
    or eax, edi
    mov edx, esi
    jmp ranked
  absent:
    xor eax, eax
    xor edx, edx
  ranked:
    pop ebp
    pop edi
    pop esi
    pop ecx
    pop ebx
    ret
  ]])

  -- Reset the four sides when the original 40-update connection refresh starts.
  local beginUpdate = core.allocateAssembly(string.format([[
    pushfd
    pushad
    mov esi, edi
    call %d
    mov dword [edi+24], 15
    popad
    popfd
    mov [edi+ecx+0x294], ebx
    jmp 0x41B806
  ]], initialize))
  local visitTile = core.allocateAssembly(string.format([[
    pushfd
    pushad
    mov ecx, [edi+0xF9862C]
    mov esi, edi
    call %d
    mov esi, edi
  ]], rank) .. address .. [[
    cmp eax, [edi+edx*4+8]
    jbe visited
    mov [edi+edx*4+8], eax
  visited:
    popad
    popfd
    mov eax, [eax*4+0x1BF8368]
    jmp 0x41B85C
  ]])
  -- Final map preparation runs after every new map and SP/MP save load.
  -- ordinary camera movement and painting do not reset the cache.
  local resetMap = core.allocateAssembly(string.format([[
    pushfd
    inc dword [%d]
    popfd
    push ecx
    mov eax, [0x21AEC54]
    jmp 0x512456
  ]], epoch))

  -- A cold side is initialized once after load / building-slot reuse. After
  -- that, drawing reads the cache; only the native connection loop refreshes it.
  local wrapper = core.allocateAssembly(string.format([[
    pushfd
    pushad
    sub esp, 32
    cmp dword [esp+72], 54
    jne finish
    cmp esi, 812*2000
    jae finish
    movzx eax, word [esi+0xF98606]
    sub eax, 75
    cmp eax, 3
    ja finish
    mov eax, [esp+76]
    cmp eax, 81
    je frame_ok
    cmp eax, 90
    jne finish
  frame_ok:
    mov ebx, [0x1FE7AA4]
    test ebx, 1
    jnz finish
    cmp ebx, 6
    ja finish
    shr ebx, 1
    inc ebx
    cmp eax, 81
    jne side_ready
    inc ebx
  side_ready:
    and ebx, 3
    mov [esp+12], ebx
    lea ebp, [esi+0xF98534]
    mov ecx, [ebp+0xF8]
    cmp ecx, 4
    jb finish
    cmp ecx, 6
    ja finish
    mov [esp+16], ecx
    mov eax, [ebp+0xF4]
    cmp eax, 80400
    jae finish
    movzx eax, byte [eax+0x1D46648]
    add eax, 90
    mov [esp], eax
  ]] .. address .. [[
    mov eax, [%d]
    cmp eax, [edi+28]
    jne cold_building
    mov eax, [ebp+0xD8]
    cmp eax, [edi]
    jne cold_building
    mov eax, [ebp+0xF4]
    cmp eax, [edi+4]
    je entry_ready
  cold_building:
    call %d
  entry_ready:
    mov [esp+8], edi
    mov ecx, [esp+12]
    bt [edi+24], ecx
    jc cached
    mov dword [esp+4], 0
    mov dword [esp+20], 0
    mov dword [esp+24], 0
    mov dword [esp+28], 0
    movzx edi, word [ebp+0xEE]
    movzx edx, word [ebp+0xF0]
    mov ecx, [esp+16]
    cmp ebx, 0
    je north
    cmp ebx, 1
    je east
    cmp ebx, 2
    je south
    dec edi
    add edx, ecx
    dec edx
    mov dword [esp+28], -1
    jmp scan
  north:
    dec edx
    mov dword [esp+24], 1
    jmp scan
  east:
    add edi, ecx
    mov dword [esp+28], 1
    jmp scan
  south:
    add edi, ecx
    dec edi
    add edx, ecx
    mov dword [esp+24], -1
  scan:
    cmp edi, 400
    jae next_tile
    cmp edx, 400
    jae next_tile
    lea eax, [edx+edx*2]
    mov eax, [eax*4+0x2337300]
    add eax, edi
    mov ebx, [esp+20]
    push edx
    call %d
    pop edx
    cmp eax, [esp+4]
    jbe next_tile
    mov [esp+4], eax
  next_tile:
    add edi, [esp+24]
    add edx, [esp+28]
    inc dword [esp+20]
    mov eax, [esp+20]
    cmp eax, ecx
    jb scan
    mov edi, [esp+8]
    mov ecx, [esp+12]
    mov eax, [esp+4]
    mov [edi+ecx*4+8], eax
    bts [edi+24], ecx
  cached:
    mov eax, [edi+ecx*4+8]
    test eax, eax
    jz no_door
    ; Use the native building draw position, not its per-kind door offsets.
    ; The draw tile is one tile behind the front footprint corner. A face tile
    ; projects to 16x8 pixels; the existing 20x47 door threshold is at (10,42).
    ; Parent renderGmOverlayBuilding2 arguments remain at +116 (X), +120 (Y).
    mov ebx, [esp+16]
    lea edx, [ebx*8]
    mov ecx, [esp+116]
    cmp dword [esp+76], 81
    jne right_anchor
    sub ecx, edx
    add ecx, 6
    mov [esp+80], ecx
    shr edx, 1
    mov ecx, [esp+120]
    sub ecx, edx
    sub ecx, 99
    jmp anchor_ready
  right_anchor:
    add ecx, edx
    add ecx, 4
    mov [esp+80], ecx
    shr edx, 1
    mov ecx, [esp+120]
    sub ecx, edx
    sub ecx, 100
  anchor_ready:
    mov [esp+84], ecx
    ; Position along the face from its true midpoint.
    movzx ebx, al
    mov ecx, 8
    sub ecx, ebx
    lea ecx, [ecx*2+1]
    sub ecx, [esp+16]
    ; Inset only the extreme connections by half a tile, symmetrically.
    mov edx, [esp+16]
    sub edx, 2
    cmp ecx, edx
    jle upper_inset
    mov ecx, edx
  upper_inset:
    neg edx
    cmp ecx, edx
    jge lower_inset
    mov ecx, edx
  lower_inset:
    mov edx, ecx
    shl edx, 3
    sub [esp+80], edx
    shl ecx, 2
    cmp dword [esp+76], 81
    jne position_y
    neg ecx
  position_y:
    add [esp+84], ecx
    shr eax, 16
    dec eax
    mov edx, [esp]
    sub edx, eax
    add [esp+84], edx
    sub edx, 90
    jle finish
    add esp, 32
    popad
    popfd
    jmp %d
  finish:
    add esp, 32
    popad
    popfd
    jmp 0x455300
  no_door:
    add esp, 32
    popad
    popfd
    ret 16
  ]], epoch, initialize, rank, deferredDraw))

  -- The existing building graphics refresh already classified the cliff face.
  -- Use native tile_walls columns beneath tower footprint tiles. Keep the
  -- renderer, clipping, terrain and logical map untouched; no new tile scan.
  local foundation = core.allocateAssembly([[
    pushfd
    pushad
    mov eax, [ebp-0x30]
    cmp eax, 2000
    jae original
    imul eax, eax, 812
    movzx eax, word [eax+0xF98606]
    sub eax, 75
    cmp eax, 3
    ja original
    mov ecx, [ebp-0xE4]
    mov edx, [ecx+0x55489C]
    cmp edx, 6
    ja original
    test edx, 1
    jnz original
    mov ebx, [ebp-0x1C]
    mov esi, [ecx+0x554A38]
    test edx, 2
    jz even_axes
    cmp ebx, 1
    je coordinate
    jmp x_axis
  even_axes:
    cmp ebx, 1
    jne coordinate
  x_axis:
    mov esi, [ebp-0x3C]
  coordinate:
    and esi, 15
    cmp ebx, 1
    jne other_face
    test edx, 4
    jnz first_increasing
    mov eax, 17
    sub eax, esi
    jmp write_masonry
  first_increasing:
    lea eax, [esi+2]
    jmp write_masonry
  other_face:
    add edx, 2
    test edx, 4
    jnz second_increasing
    mov eax, 32
    sub eax, esi
    jmp second_wrap
  second_increasing:
    lea eax, [esi+17]
  second_wrap:
    cmp eax, 17
    jne write_masonry
    mov eax, 1
  write_masonry:
    add eax, [0xD7CEB8]
    dec eax
    mov edx, [ecx+0x554A3C]
    mov [ecx+edx*2+0xC80E0], ax
    and word [ecx+edx*2+0x301C80], 0xF7FF
    popad
    popfd
    jmp 0x50EE19
  original:
    popad
    popfd
    mov edx, [ebp-0xE4]
    jmp 0x50EDB5
  ]])
  core.writeCode(0x4EBA52, {core.callTo(foundationDraw)})
  for _, site in ipairs(sites) do
    core.writeCode(site[1], {core.callTo(wrapper)})
  end
  core.writeCode(0x41B7FF, {core.jmpTo(beginUpdate), 0x90, 0x90})
  core.writeCode(0x41B855, {core.jmpTo(visitTile), 0x90, 0x90})
  core.writeCode(0x512450, {core.jmpTo(resetMap), 0x90})
  core.writeCode(0x50EDAF, {core.jmpTo(foundation), 0x90})
end

return M
