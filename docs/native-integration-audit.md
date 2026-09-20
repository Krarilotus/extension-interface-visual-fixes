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
