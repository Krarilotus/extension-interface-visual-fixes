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
    {0x41B7FF, "89 9C 0F 94 02 00 00"},
    {0x41B855, "03 81 28 E0 18 00 8B 04 85 68 83 BF 01 A9 00 01 00 00 74 1C A8 02 75 18 A9", 6},
    {0x512450, "51 A1 54 EC 1A 02 53 55 8B 2D 50 EC 1A 02 56 89 44 24 0C"},
  }
  for _, site in ipairs(updateSites) do
    if core.AOBScan(site[2]) + (site[3] or 0) ~= site[1] then
      error("Interface and Visual Fixes: unsupported tower connection update layout")
    end
  end

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
  -- and retains terrain height. A connection below the tower base is unusable.
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
    mov esi, [esi+0xF98628]
    cmp esi, 80400
    jae absent
    movzx esi, byte [esi+0x1D46648]
    cmp edi, esi
    jb absent
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
    ; Position along the existing face, relative to its side-centre anchor.
    ; One boundary tile projects to -16 X and -8/+8 Y for frame 81/90.
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
  ]], epoch, initialize, rank))
  for _, site in ipairs(sites) do
    core.writeCode(site[1], {core.callTo(wrapper)})
  end
  core.writeCode(0x41B7FF, {core.jmpTo(beginUpdate), 0x90, 0x90})
  core.writeCode(0x41B855, {core.jmpTo(visitTile), 0x90, 0x90})
  core.writeCode(0x512450, {core.jmpTo(resetMap), 0x90})
end

return M
