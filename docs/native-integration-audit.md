# Native integration audit (in progress)

Related: [runtime bindings #33](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/33),
[reported crashes #34](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/34).
Neither issue is resolved by the assembler cleanup.

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

## Remaining binding work

The production fixed-address table is still present. Replace it completely before
closing #33. Contextual common-signature candidates have been checked for 77 of its
86 entries against the two local reference PEs; that is research, not a shipped
resolver or completion evidence. Group roots and decode call/branch targets instead
of creating a scanner per field. Preflight all enabled capabilities before writes.
Verify the official EFIGS/PL fixtures as well as the local SHC/Extreme pair.

Two current names are misleading: `MapWidth` holds `ViewportState.viewportY`,
and `CurrentBuildingLayerPointer` is `ViewportState.ptrColor`, the screen pixel used
for native mouse picking. The render-map instructions initialize it from the map
surface and cursor coordinates. Deferred door drawing saves/restores that pixel;
it is not a pointer into the building tile layer. Correct these names as part of
the binding change, with no invented replacement ownership.

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
