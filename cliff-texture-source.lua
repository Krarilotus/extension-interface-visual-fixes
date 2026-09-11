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
  -- Raw GM9 strips contain both halves of a 30-pixel strip. Each visible face
  -- needs the complete strip, projected onto its 16 screen columns. Undo the
  -- source skew; the existing native blitter supplies the destination skew.
  local columns = {}
  for x = 0, 29 do
    local sx = math.floor(math.min(x, 29-x) * 29 / 14 + 0.5)
    columns[#columns+1] = sx*2
    columns[#columns+1] = math.min(math.floor(sx/2), 14-math.floor(sx/2))
  end
  local uv = core.allocate(#columns, false)
  core.writeCode(uv, columns)
  -- Each visible image owns an original copy and a converted copy. Grow only
  -- when its metadata requires more space; preserve native resource ownership.
  -- Compare once per render frame to detect replacement and address reuse.
  -- Entry: epoch, source bytes, capacity bytes, buffer, valid conversion.
  local bank = core.allocate(32*20, true)
  local resolve = layout.allocateAssembly(string.format([[
    pushfd
    pushad
    mov esi, [eax*4+ImageOffsets]
    add esi, [ImageData]
    mov [esp+28], esi
    mov edx, eax
    sub edx, [CliffImages]
    cmp edx, 31
    ja done
    mov ecx, [eax*4+ImageSizes]
    shl eax, 4
    cmp word [eax+ImageHeaders], 30
    jne done
    movsx ebp, word [eax+ImageHeaders+2]
    sub ebp, 7
    jle done
    imul eax, ebp, 60
    cmp eax, ecx
    jne done
    imul ebx, edx, 20
    add ebx, %d
    cmp ecx, [ebx+8]
    ja grow
    cmp ecx, [ebx+4]
    jne resized
    cmp dword [ebx+16], 0
    je convert
    mov edx, [%d]
    cmp [ebx], edx
    je cached
    push esi
    mov edi, [ebx+12]
    shr ecx, 2
    cld
    repe cmpsd
    pop esi
    je verified
    jmp convert
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
    jz done
    mov [ebx+12], eax
    mov [ebx+8], ecx
  resized:
    mov [ebx+4], ecx
  convert:
    push esi
    mov edi, [ebx+12]
    mov ecx, [ebx+4]
    shr ecx, 2
    cld
    rep movsd
    pop esi
    ; Convert each column down its full metadata-defined height. The source
    ; skew wraps within this image, including strips shorter than the skew.
    push ebx
    push esi
    push edi
    push ebp
    mov eax, [ebx+4]
    push eax
    add eax, esi
    push eax
    xor ebx, ebx
  column:
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
    mov dword [ebx+16], 1
  verified:
    mov edx, [%d]
    mov [ebx], edx
  cached:
    mov eax, [ebx+12]
    add eax, [ebx+4]
    mov [esp+28], eax
  done:
    popad
    popfd
    ret
  ]], bank, epoch, uv, uv, epoch))
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
