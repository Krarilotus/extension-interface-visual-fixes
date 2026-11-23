-- Ghost Objects: rebuild the per-tile entity lists from each entity's own tile.
--
-- Based on Ghost Objects Fix by Monsterfish, relicensed by the author under GPL-3.0.
--
-- The game keeps the small objects ("entities": flags, projectiles, dust and spray
-- clouds, smoke, birds ...) of each tile in a linked list: a head word per tile and
-- a "next" word in each 232-byte entity record (ids below 25 use a separate head
-- byte per tile). The lists get tangled when an entity is freed while a list still
-- reaches it; the next entity created in that slot (a tower flag, a stone, an
-- arrow) is then drawn on the old tile too. Saved games and maps keep the tangle.
--
-- At the start of the entity update, whenever the game's own 0-199 tick cycle is a
-- multiple of the interval, rebuild all lists from the tile each living entity
-- stands on. Nothing walks a list at that moment. The tick cycle is saved with the
-- game and identical for every player, so the schedule needs no extension save data
-- and is the same after loading a save, in multiplayer and in replays (given the
-- same setting).
local layout = require("native-layout")
local A = layout.addresses
local M = {}

local BYTE_IDS = 0x19 -- ids below this use the byte heads
local DEFAULT_INTERVAL = 10 -- the entity update's own 10-tick cadence
local MAX_INTERVAL = 200 -- one full tick cycle

local function interval(config)
  local value = type(config) == "table" and tonumber(config["ghost-objects-interval"]) or nil
  if value == nil or value ~= value then value = DEFAULT_INTERVAL end
  return math.max(1, math.min(MAX_INTERVAL, math.floor(value)))
end

function M.enable(config)
  -- Bindings and checks ran in the shared preflight; recheck the prologue right
  -- before writing it.
  local site = A.EntityUpdate
  layout.requireOriginalEntityUpdate()
  local every = interval(config)
  local tiles = layout.ENTITY_TILES
  local stub = layout.allocateAssembly(string.format([[
    pushad
    pushfd
    mov ebx, ecx
    mov eax, [EntityTick]
    xor edx, edx
    mov ecx, %d
    div ecx
    test edx, edx
    jnz ghost_done
    cld
    xor eax, eax
    mov edi, EntityWordHeads
    mov ecx, %d
    rep stosd
    mov edi, EntityByteHeads
    mov ecx, %d
    rep stosd
    mov esi, EntitySlots - 1
  ghost_slot:
    mov eax, esi
    imul eax, eax, 0xE8
    add eax, ebx
    cmp word [eax+0x3C], 0
    je ghost_unlinked
    mov edx, [eax+0x60]
    test edx, edx
    jle ghost_unlinked
    cmp edx, %d
    jae ghost_off_map
    cmp esi, %d
    jge ghost_word_head
    movzx ecx, byte [edx+EntityByteHeads]
    mov [eax+0x32], cx
    mov ecx, esi
    mov [edx+EntityByteHeads], cl
    jmp ghost_next
  ghost_word_head:
    mov cx, [edx*2+EntityWordHeads]
    mov [eax+0x32], cx
    mov [edx*2+EntityWordHeads], si
    jmp ghost_next
  ghost_off_map:
    mov dword [eax+0x60], 0
  ghost_unlinked:
    mov word [eax+0x32], 0
  ghost_next:
    dec esi
    jnz ghost_slot
  ghost_done:
    popfd
    popad
    push ecx
    push ebx
    push ebp
    push esi
    mov esi, ecx
    jmp EntityUpdateResume
  ]], every, tiles // 2, tiles // 4, tiles, BYTE_IDS))
  core.writeCode(site, {core.jmpTo(stub), 0x90})
  log(INFO, string.format("ghost objects: tile object lists rebuilt every %d ticks of the game's tick cycle (%d slots)",
    every, A.EntitySlots))
end

return M
