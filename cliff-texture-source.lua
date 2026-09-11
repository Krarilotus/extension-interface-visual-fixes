local layout = require("native-layout")
local A = layout.addresses
local M = {}

function M.enable()
  local sites = {
    {A.CliffSource, layout.patterns.CliffSource, 30},
    {A.CliffOffsetSource, layout.patterns.CliffOffsetSource, 32},
  }
  for _, site in ipairs(sites) do
    if core.AOBScan(site[2]) ~= site[1] then
      error("Interface and Visual Fixes: unsupported cliff source layout")
    end
  end
  local epoch = require("render-frame").getEpoch()
  -- Each native half spans a complete strip, in screen order. The centre
  -- columns join the end of image N to the start of N+1 (32 wraps to 1).
  local columns = {}
  for x = 0, 29 do
    local sx = math.floor((x % 15) * 29 / 14 + 0.5)
    columns[#columns+1] = sx*2
    columns[#columns+1] = math.min(math.floor(sx/2), 14-math.floor(sx/2))
  end
  local uv = core.allocate(#columns, false)
  core.writeCode(uv, columns)
  -- Entry: source-check epoch, bytes, capacity, private buffer, flags.
  -- Flags: 1 = source copy valid, 2 = paired projection valid. A source change
  -- invalidates its own projection and the preceding pair. Each original is
  -- compared once per frame, even when two pairs use it. Storage remains one
  -- source copy and one projection per image; no duplicated neighbour copies.
  local bank = core.allocate(32*20, true)
  local ensureSource = layout.allocateAssembly(string.format([[
    pushfd
    pushad
    mov edx, eax
    sub edx, [CliffImages]
    cmp edx, 31
    ja unavailable
    imul ebx, edx, 20
    add ebx, %d
    mov esi, [eax*4+ImageOffsets]
    add esi, [ImageData]
    mov ecx, [eax*4+ImageSizes]
    shl eax, 4
    cmp word [eax+ImageHeaders], 30
    jne invalid
    movsx ebp, word [eax+ImageHeaders+2]
    sub ebp, 7
    jle invalid
    imul eax, ebp, 60
    cmp eax, ecx
    jne invalid
    cmp ecx, [ebx+8]
    ja grow
    cmp ecx, [ebx+4]
    jne resized
    test dword [ebx+16], 1
    jz changed
    mov edx, [%d]
    cmp [ebx], edx
    je available
    push esi
    mov edi, [ebx+12]
    shr ecx, 2
    cld
    repe cmpsd
    pop esi
    je verified
    jmp changed
  grow:
    push ecx
    call dword [ProcessHeap]
    mov ecx, [esp]
    add ecx, ecx
    push ecx
    cmp dword [ebx+12], 0
    je allocate
    push dword [ebx+12]
    push 0
    push eax
    call dword [ReallocateHeap]
    jmp allocated
  allocate:
    push 0
    push eax
    call dword [AllocateHeap]
  allocated:
    pop ecx
    test eax, eax
    jz invalid
    mov [ebx+12], eax
    mov [ebx+8], ecx
  resized:
    mov [ebx+4], ecx
  changed:
    mov edi, [ebx+12]
    mov ecx, [ebx+4]
    shr ecx, 2
    cld
    rep movsd
    mov dword [ebx+16], 1
    call invalidate_previous
  verified:
    mov edx, [%d]
    mov [ebx], edx
  available:
    mov [esp+28], ebx
    jmp source_done
  invalid:
    test dword [ebx+16], 1
    jz unavailable
    mov dword [ebx+16], 0
    call invalidate_previous
  unavailable:
    mov dword [esp+28], 0
  source_done:
    popad
    popfd
    ret
  invalidate_previous:
    lea edi, [ebx-20]
    cmp ebx, %d
    jne previous_ready
    mov edi, %d
  previous_ready:
    and dword [edi+16], -3
    ret
  ]], bank, epoch, epoch, bank, bank+31*20))
  local resolve = layout.allocateAssembly(string.format([[
    pushfd
    pushad
    mov esi, [eax*4+ImageOffsets]
    add esi, [ImageData]
    mov [esp+28], esi
    mov ebp, eax
    call %d
    test eax, eax
    jz done
    mov ebx, eax
    mov eax, ebp
    sub eax, [CliffImages]
    inc eax
    and eax, 31
    add eax, [CliffImages]
    call %d
    ; Mixed-height or unavailable neighbours cannot share native row stride.
    ; Use the validated current strip on both halves until compatible again.
    test eax, eax
    jz own_neighbour
    mov edx, [eax+4]
    cmp edx, [ebx+4]
    jne own_neighbour
    mov ebp, [eax+12]
    jmp neighbour_ready
  own_neighbour:
    mov ebp, [ebx+12]
  neighbour_ready:
    test dword [ebx+16], 2
    jnz cached
    mov esi, [ebx+12]
    mov edi, esi
    add edi, [ebx+4]
    mov eax, [ebx+4]
    xor edx, edx
    mov ecx, 60
    div ecx
    ; Locals: end, bytes, rows, destination, left source, entry, right source.
    push ebp
    push ebx
    push esi
    push edi
    push eax
    push dword [ebx+4]
    mov eax, esi
    add eax, [ebx+4]
    push eax
    xor ebx, ebx
  column:
    cmp ebx, 15
    jne column_source
    mov eax, [esp+24]
    mov [esp+16], eax
    add eax, [esp+4]
    mov [esp], eax
  column_source:
    movzx eax, byte [ebx*2+%d+1]
    xor edx, edx
    div dword [esp+8]
    mov eax, [esp+8]
    sub eax, edx
    cmp eax, [esp+8]
    jne source_row
    xor eax, eax
  source_row:
    imul eax, 60
    add eax, [esp+16]
    movzx edx, byte [ebx*2+%d]
    add eax, edx
    mov edi, [esp+12]
    lea edi, [edi+ebx*2]
    mov ecx, [esp+8]
  pixel:
    mov dx, [eax]
    mov [edi], dx
    add edi, 60
    add eax, 60
    cmp eax, [esp]
    jb next_row
    sub eax, [esp+4]
  next_row:
    dec ecx
    jnz pixel
    inc ebx
    cmp ebx, 30
    jb column
    add esp, 20
    pop ebx
    add esp, 4
    or dword [ebx+16], 2
  cached:
    mov eax, [ebx+12]
    add eax, [ebx+4]
    mov [esp+28], eax
  done:
    popad
    popfd
    ret
  ]], ensureSource, ensureSource, uv, uv))
  for _, site in ipairs(sites) do
    local first = site[1] == A.CliffSource
    local wrapper = layout.allocateAssembly(string.format([[
      pushfd
      pushad
      mov eax, [PrimaryImage]
      call %d
      mov [ebp-%d], eax
      mov eax, [SecondaryImage]
      call %d
      mov [ebp-%d], eax
      popad
      popfd
    ]], resolve, first and 16 or 20, resolve, first and 8 or 4) ..
      (first and [[
        mov eax, [SecondaryImage]
        mov edx, [eax*4+ImageOffsets]
      ]] or [[
        mov edx, [SecondaryImage]
        mov eax, [edx*4+ImageOffsets]
      ]]) .. string.format("jmp 0x%X", site[1]+site[3]))
    local patch = {core.jmpTo(wrapper)}
    for _ = 6, site[3] do patch[#patch+1] = 0x90 end
    core.writeCode(site[1], patch)
  end
end

return M
