# Native integration audit (in progress)

Related: [runtime bindings #33](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/33),
[reported crashes #34](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/34).
The binding correction resolves issue33; the crash investigation remains open.

## Startup diagnostics validation

All 1,488 tests pass. Six complete regular/Extreme local/EFIGS/PL executables
produce identical game patches, allocations (151,284 bytes) and scan calls with
or without the new startup diagnostics, compared with merged PR38. Seven extra
native bytes relative to the original release belong to PR38's cold-door fix,
not logging. No logging instruction or extra state read runs during drawing or
simulation. Enabling all seven options writes 121 startup messages, 4,739 message
bytes before the framework prefix/timestamp. Partial/disabled configurations
do not initialize unused capabilities, and a second enable writes nothing.
The feature loop retains its existing order and all-before-write preflight.

The optional Windows dump procedure is documented, not enabled or exercised on
this desktop. No native game session or unpublished Reconquista asset was used.

## Existing owners inspected

| Capability | Implementation and revision inspected | Reuse decision |
| --- | --- | --- |
| AOB discovery/cache | UCP 3.0.7 `content/ucp/code/core.lua`, `data/cache.lua`, tag `v3.0.7` (`77c6accf14a55fb95434fe6ffd96516e005568b5`) | Use `core.AOBScan`; it already owns cached discovery and revalidates cached matches. Verify signature uniqueness offline. Do not add a second scanner/cache. |
| Assembly and patch allocation | Same tag, `core.assemble`, `core.allocateAssembly`, `core.allocateCode`, `core.writeCode`, `core.callTo`/`jmpTo` | Use the existing symbol-mapping argument, filtered to symbols referenced by a wrapper to fit the embedded 64 KB FASM workspace. Remove private textual operand substitution. |
| Global structures | Same tag, `data/structures.lua` | Does not supply these bindings: its implemented game variable is game speed; `PlayerData` is empty and addresses are fixed. Not a suitable runtime resolver for this module. |
| Existing lobby control | `ui` 1.0.1: `manager/init.lua:lookupMenu`, `ui/menu.lua:fromID/fromPointer`, current local owner checkout | Public access resolves constructed menu objects; it does not expose the internal Load-case eligibility/draw predicates or the pre-initialization static item definition. Keep the existing native item/action/render path; no duplicate control or menu registry. Owner checkout has unrelated work and was not modified. |
| GM resources | `TheRedDaemon--ucp_gmResourceModifier` `019039afcb29f3806aa30c7157ae5a1253c06673`, `init.lua`, `gmResourceModifier.cpp:SetGm/FreeGm1Resource/copyToShc` | Resource owner retains installed replacements through reference counts and refuses to free in-use resources. Exports loading/replacement/freeing; no inspected public raw-image generation/bounds notification. Do not replace resource ownership. |
| Texture configuration | `extension-textureSwapper/init.lua`, public `ApplyConfiguration` and its `afterInit` caller | Uses the GM owner. Explicit configuration changes require the game thread outside drawing. The cliff cache must not infer that asset replacement cannot occur. |
| Graphics/window integration | `graphicsApiReplacer` `473774d8b8028f4e9a4f4367291d54066bad57e3`, Lua initialization and DLL exports | Owns presentation/window changes; no inspected public map-render epoch callback. Preserve the module's existing single shared render-entry hook; do not add another. Exact installed DLL/preset for the reported crash is unavailable. |
| Existing AOB usage | UCP2-Legacy 2.15.1 `caa50aba9fc85c5fc766c413b23085ddfbba4a79`, `init.lua` and `port/ai_attackwave.lua` | Reuse the same workflow: contextual wildcarded `core.AOBScan` in initialization, decode native operands/relative targets with `core.readInteger`, use framework allocation/patching. Keep discovery before feature writes. Consolidate repeated enable branches into one ordered list; no copied Legacy feature implementation. |
| Diagnostic logging | UCP 3.0.7 `dll/core/initialization/logging.cpp`, `content/ucp/code/logging.lua`, `extensions/environment.lua`, `main.lua` | Use module-prefixed `log(INFO, ...)`. Existing logger owns files/filtering; main already logs config and versions. Add startup binding/code/cache addresses only. No private logger, extra native reads, render callback or exception handler. Windows LocalDumps supplies optional fault-time register/heap capture outside the extension. |

The Store-pinned UCP2-Legacy 2.15.2 revision
`3fd852df9ac3f2b00595512555e9043e3b624437` was also compared in these two files.
It retains the same AOB/operand-decoding workflow; its additional persistent
simulation-state ownership is unrelated to these presentation caches and is not
copied into this module.

Gynt's applicable framework guidance is [“No, improve AOB's, don't make the scanner slower.”](https://github.com/UnofficialCrusaderPatch/UnofficialCrusaderPatch3/issues/148#issuecomment-5665748438)
No Gynt review was found in the inspected module issue comments, inline PR comments,
commit comments, or reviews for its twenty previous PRs. This is not a claim about
uninspected private conversations or other repositories.

## Assembler cleanup verification

All 1,395 existing tests pass with the framework symbol-mapping argument.
The original and revised modules emit byte-for-byte identical patches and allocated
data/code for both complete local SHC and Extreme 1.41 reference executables.
Each allocates 151,277 bytes before the on-demand cliff-image heap buffers.
Both old and new assembly were checked with FASM's 64 KB workspace.
No new runtime instruction, allocation, hook, dependency or feature behavior is added.
This is offline verification, not new native gameplay acceptance or crash resolution.

## Runtime binding correction

The 86-entry SHC/Extreme address-pair table has been removed. Common contextual
signatures use `core.AOBScan`, and matched instructions supply data operands and
relative targets. Named bindings are retained at initialization; assembly receives
the resolved values. There is no executable hash/base whitelist or address fallback.

| Bindings | Resolution and layout contract | Existing patch interaction |
| --- | --- | --- |
| Placement acknowledgement and command return | Identify the post-commit notification, placement entry, its command caller and minimap callee; verify both relative call targets. Decode mode/player operands. | Preserve the single acknowledgement call and original tail call. Reject changed callees before any patch. |
| Camera preview and dead trees | Identify the original scrolling gate and its exit; decode the branch and compare its target with the native exit context. Decode tree-frame array access and retain verified Tree field offsets/156-byte stride. | Existing preview gate and frame load only. No new input hook. |
| Lobby Load | Identify native draw/action/preparation cases and the static existing item by type/parameter, coordinates, activity, art and tooltip. Item fields are offsets within that definition. | Same item, native action and render callbacks; all enabled binding discovery precedes R007 and other writes. |
| Tower connections and drawing | Identify all five overlay calls, update/reset/selection sites and foundation call; verify native callees. Decode the Buildings array; fields use its 812-byte record layout. Decode TileMapState's LogicLayer, with verified member offsets for other layers/orientation. | Retain existing refresh hooks, one shared render entry and one foundation call. No additional cache, census or render pass. |
| Cliff sources and GM metadata | Identify both source sites and validate agreement of primary/secondary image and offset operands. Decode header/size arrays, texture-renderer root and GM base-index array. GM IDs 9, 10 and 54 select cliff, wall and tower entries. | Existing source substitutions and selector only. Dimensions/pixel processing are unchanged, including oversized texture handling. |
| Heap imports | Decode import slots from native allocation/reallocation contexts. | Same Win32 heap API/ABI; no private allocator introduced. |

Struct offsets are cross-checked with native instructions and OpenSHC declarations
at `b6e4a6ce1624c24953dfcbb71f99596f8e09ec9d` (`TileMapState.hpp`, `Tree.hpp`,
`ViewportState.hpp`). Those declarations are evidence, not a shipped runtime API.
The misleading names `MapWidth` and `CurrentBuildingLayerPointer` are now
`ViewportY` and `CursorSamplePointer`: the latter is the screen pixel used by
native mouse picking, not a pointer into the building tile layer. Behavior is unchanged.

All 1,409 tests pass. Component/ABI tests explicitly isolate bindings; separate
production-discovery tests cover both families, changed data operands, a moved
render entry, missing contexts, redirected calls, disabled features and failure
before patch allocation. The seven-option composition test uses production discovery.
Offline uniqueness checking belongs to the test oracle; runtime uses the framework's
existing first-match scanner/cache, following Gynt's guidance rather than adding
another scanner. This does not claim support for arbitrary future executables.

Complete-PE verification uses the local regular/Extreme pair plus official EFIGS
and Polish regular/Extreme 1.41 fixtures. All six produce byte-for-byte identical
patches and allocations to the pre-refactor module. Thus there are no added
instructions, allocations or scans in rendering/simulation. Extra identifying
contexts are resolved only at initialization. No native session or unreleased
Reconquista pack was run; the random-crash investigation remains open.

## Crash investigation limits

The supplied report dates the first map-blitter crash before installation of the
attached resolution-zoom module. On the local Extreme reference, offsets `0x54517`
and `0x5454B` are source reads in the Y-offset blitter. There is no supplied dump,
fault pointer, complete stack, exact tester executable, or unpublished pack asset.

4,480 original-blitter emulation cases using 160/320-row synthetic source strips
found no read outside the module's private allocations. Additional 161/240-row
cases also passed, followed by 4,480 cases using 512/1,024-row strips. Oversized
Reconquista textures remain explicitly in scope; no vanilla-height cap is proposed.
Synthetic strips below 160 rows expose out-of-allocation reads:
the original Y-offset blitter uses a fixed 160-row anchor. Existing positive-height
resolver tests alone do not establish safe downstream blitting for those sizes.
This does not match the tester's reported taller artwork and is not attribution
of that crash. Reachability through native terrain classification and safe handling
of such metadata remain to be established before claiming arbitrary-height support.

The supplied zoom module calls the original video-options apply handler and patches
keyboard/screen-change dispatch, not the map blitters. Its optional in-game guards
fail open if discovery fails; that is a separate behavior to investigate with its
owner, not proof of the source-image crash. No change to that supplied module has
been made, and neither game nor desktop was used during this audit.

## Ghost Objects (0.2.0)

Merged from `Krarilotus/GhostObjectsFix@489d388` (Monsterfisch/GhostObjectsFix#1),
relicensed by the author under GPL-3.0 for inclusion; see [CREDITS](../CREDITS.md).
Off by default; no UCP3 plugin turns it on.

### Reuse decision: rebuild schedule

| Capability | Inspected | Decision |
| --- | --- | --- |
| Load lifecycle | UCP 3.0.7 `content/ucp/code/hooks.lua` (`77c6accf`) and framework main `d891e0e`: only `afterInit` (process start) exists | No game-load event in the framework. |
| Save sections | map-extensions `registerSection` (used by the reviewed version to reset its countdown on initialize/deserialize) | Not used: Map Extensions is not part of the default setup, and a save section would make saves differ between UCP3 family members. |
| Code section bounds (for the uniqueness scan) | UCP 3.0.7 `core.lua` exposes no image/section bounds; `core.scanForAOB` without a limit searches up to `0x7FFFFFFF`; `data/version.lua` uses fixed `0x400000`-`0x600000` bounds | Find the game image's DOS header with `core.AOBScan` (first image at or after UCP's scan origin), validate its PE headers (`ImageBase` equals the match) and use the end of the section containing the entity update as the scan limit. No fixed address. |
| Saved game clock | `GameStateStructures.gameTicksLoadBalancer` (OpenSHC `Game/GameStateStructures.hpp` +0x918A4). The entity update reads it with its first instruction (`mov ecx, [tick]`, then `tick % 10`). `processSingleTimeTick` increments it and wraps at 200 (SHC `0x45CC19`, SHCE `0x45CE29`). It is serialized as save section 1024 (section table entry at SHC `0xB92CA8` / SHCE `0xB92E38`, 4 bytes) | **Used.** Read from the matched entity-update instruction (`EntityTick` = operand at body +2), no extra signature. Rebuild when `tick % interval == 0`; interval 1 to 200 (one cycle). Same schedule for every player, after loading a save and in replays; no process-local countdown and no extension save data. |

### Bindings

| Binding | Responsibility | Resolution | Checks before any write |
| --- | --- | --- | --- |
| `EntityUpdate` / `EntityUpdateBody` / `EntityUpdateResume` | Patch site: `updateEntities` prologue (6 bytes `51 53 55 56 8B F1`), stub resumes after it | `EntityUpdate` AOB matches the body after the prologue, so an occupied prologue is still found | Second `core.scanForAOB` from body+1 to the end of the code section containing the body must find nothing (ambiguous otherwise); copies of code bytes in data or heap memory are ignored. Prologue bytes must be original, else refuse naming `improved-siegeengines.oil.aim` / `oil.spread` (`requireOriginalEntityUpdate`, also called in `ghost-objects.lua` right before writing). |
| `ImageBase` | The game image's PE headers, for the end of its code section | `ImageHeader` AOB (DOS header) through `core.AOBScan`: first image at or after UCP's scan origin | The headers' `PE` signature and `ImageBase` must equal the match, and one of their sections must contain the entity update body (`.text`, ends `0x59D806` SHC / `0x59DC36` SHCE); otherwise unsupported. |
| `EntityTick` | Saved 0-199 tick cycle | Operand of the body's first instruction | Same match as the patch site. |
| `EntityTileWalker`, `EntityByteHeads`, `EntityWordHeads` | Per-tile head byte array (ids < 25) and head word array | Walker AOB, operands at +0x2A and +0x78 | Opcode `0F BF 14 45` before +0x78; heads exactly 80,400 x 2 bytes apart. |
| `SeagullRemoval`, `EntitySlots` | Entity slot count (3,000 SHC, 6,000 SHCE) | Seagull removal loop, `cmp ecx, imm32` at +0x40 | Opcode `81 F9`; count 100 to 20,000. |

Entity record layout (stride 232; next +0x32, liveness word +0x3C, tile +0x60 relative
to the `EntityState` receiver in ECX) is the reviewed version's, cross-checked against
OpenSHC `Map/Entities/Entity.hpp` (record fields +0x1E/+0x2A/+0x4C plus the receiver's
array offset 0x14). The stub, its slot walk and its quarantine of off-map tile values
(set to 0) are the reviewed version's.

### Compatibility

| Overlap | Decision |
| --- | --- |
| Improved Siegeengines 1.0.28 `oil.aim`/`oil.spread` (same prologue; not in the Store) | If Improved Siegeengines loads first and Ghost Objects is on, the preflight raises an error naming those options. Framework 3.0.7 `main.lua` calls `enable` without `pcall`, so **UCP stops at startup**: no fix of this module and no later extension is enabled. In the other order Improved Siegeengines' own `try` turns its oil feature off with a warning (its short `51 53 55 56 8B F1 8B 0D` signature no longer matches); its other features keep working. The result depends on load order; acceptable while Improved Siegeengines is not in the Store and Ghost Objects is off by default and turned on by no plugin. A declared conflict would be cleaner once Improved Siegeengines is published. |
| Standalone Ghost Objects Fix (Monsterfish; not in the Store) | Same prologue; whichever loads second refuses. Use one of them. |
| Smarter Buildings decorations, MapEditorImprovements, BuildingOverlays | No shared patch site with Ghost Objects (their I&V overlaps are other features' sites, unchanged here). |

### Static checks against both executables

Full-PE check of `Stronghold Crusader.exe` (SHA-256 `3bb0a8c1…`) and
`Stronghold_Crusader_Extreme.exe` (`55648e6b…`), 1.41: each of the three signatures
matches exactly once, every opcode/layout check holds, and the derived bindings equal
`tests/fixtures/component-bindings.json`. SHC: patch site `0x4087C0`, tick `0x011BC95C`,
heads `0x01CF7E08`/`0x01D1F228`, 3,000 slots. SHCE: `0x4087D0`, `0x0129144C`,
`0x0278B308`/`0x027B2728`, 6,000 slots. `tests/test_ghost_objects.py` repeats discovery,
refusal and layout checks on the extracted contexts and emulates the emitted stub on
both families. EFIGS/Polish executables were not available for this change.
