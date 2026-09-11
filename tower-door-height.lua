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

  -- Use the framework's existing FASM support. ESI is a building byte offset.
  -- Only the existing renderGM y argument changes; its RET 16 and ECX survive.
  local wrapper = core.allocateAssembly([[
    pushfd
    pushad
    sub esp, 8
    cmp dword [esp+48], 54
    jne finish
    movzx eax, word [esi+0xF98606]
    sub eax, 75
    cmp eax, 3
    ja finish
    mov eax, [esp+52]
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
    ; Original 0x40B7B0/frame81 reads the next side after 0x40B720/frame90.
    cmp eax, 81
    jne side_ready
    inc ebx
  side_ready:
    and ebx, 3
    lea ebp, [esi+0xF98534]
    mov ecx, [ebp+0xF8]
    cmp ecx, 4
    jb finish
    cmp ecx, 6
    ja finish
    mov eax, [ebp+0xF4]
    cmp eax, 80400
    jae finish
    movzx eax, byte [eax+0x1D46648]
    add eax, 90
    mov [esp], eax
    mov dword [esp+4], -1
    movzx edi, word [ebp+0xEE]
    movzx edx, word [ebp+0xF0]
    cmp ebx, 0
    je north
    cmp ebx, 1
    je east
    cmp ebx, 2
    je south
    dec edi
    add edx, ecx
    dec edx
    xor esi, esi
    mov ebx, -1
    jmp scan
  north:
    dec edx
    mov esi, 1
    xor ebx, ebx
    jmp scan
  east:
    add edi, ecx
    xor esi, esi
    mov ebx, 1
    jmp scan
  south:
    add edi, ecx
    dec edi
    add edx, ecx
    mov esi, -1
    xor ebx, ebx
  scan:
    cmp edi, 400
    jae next_tile
    cmp edx, 400
    jae next_tile
    lea eax, [edx+edx*2]
    mov eax, [eax*4+0x2337300]
    add eax, edi
    cmp eax, 80400
    jae next_tile
    mov ebp, [eax*4+0x1BF8368]
    and ebp, 0x302
    cmp ebp, 0x100
    jne next_tile
    movzx eax, byte [eax+0x1D32C38]
    cmp eax, [esp+4]
    jle next_tile
    mov [esp+4], eax
  next_tile:
    add edi, esi
    add edx, ebx
    dec ecx
    jnz scan
    cmp dword [esp+4], 0
    jl finish
    mov eax, [esp]
    sub eax, [esp+4]
    add [esp+60], eax
  finish:
    add esp, 8
    popad
    popfd
    jmp 0x455300
  ]])
  for _, site in ipairs(sites) do
    core.writeCode(site[1], {core.callTo(wrapper)})
  end
end

return M
