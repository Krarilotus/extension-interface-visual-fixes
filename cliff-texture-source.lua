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
  local offsets = {}
  for y = 0, 159 do
    for x = 0, 29 do
      local sx = math.floor(math.min(x, 29-x) * 29 / 14 + 0.5)
      local skew = math.min(math.floor(sx/2), 14-math.floor(sx/2))
      local at = 2 * (((y-skew) % 160) * 30 + sx)
      offsets[#offsets+1], offsets[#offsets+2] = at % 256, math.floor(at/256)
    end
  end
  local uv = core.allocate(#offsets, false)
  core.writeCode(uv, offsets)
  -- Keep originals private, without replacing GM pointers or modifying pixels.
  -- A visible strip is compared once per map-render frame, not once per tile.
  -- This also handles reset, individual-image swaps and allocator address reuse.
  -- Conversion runs only when the actual source bytes change. At most 32 strips
  -- (307,200 bytes) are compared in a frame; invisible strips do no work.
  local stride = 8 + 9600*2
  local bank = core.allocate(32*stride, true)
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
    cmp dword [eax*4+ImageSizes], 9600
    jne done
    shl eax, 4
    cmp dword [eax+ImageHeaders], 0x00A7001E
    jne done
    imul ebx, edx, %d
    add ebx, %d
    cmp dword [ebx+4], 0
    je convert
    mov edx, [%d]
    cmp [ebx], edx
    je cached
    push esi
    lea edi, [ebx+8]
    mov ecx, 2400
    cld
    repe cmpsd
    pop esi
    je verified
  convert:
    push esi
    lea edi, [ebx+8]
    mov ecx, 2400
    cld
    rep movsd
    pop esi
    lea edi, [ebx+9608]
    xor ecx, ecx
  pixel:
    movzx edx, word [ecx*2+%d]
    mov ax, [esi+edx]
    mov [edi+ecx*2], ax
    inc ecx
    cmp ecx, 4800
    jb pixel
    mov dword [ebx+4], 1
  verified:
    mov edx, [%d]
    mov [ebx], edx
  cached:
    lea eax, [ebx+9608]
    mov [esp+28], eax
  done:
    popad
    popfd
    ret
  ]], stride, bank, epoch, uv, epoch))
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
