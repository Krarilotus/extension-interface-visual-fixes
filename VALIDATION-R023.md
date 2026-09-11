# R023: tower door height beside connecting walls

Related issue: [#9](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/9).
Stacked on R019 PR #8. Draft pending corrected native views and the acceptance
checks below. Existing native reproduction is confirmed.

SHC 1.41 renderGmOverlayBuilding2 at 0x4E2AD0 draws existing GM54 doorway frames
81/90 with fixed offsets for stone towers 75–78. The entrance writer 0x41B7C0
records connection presence without consulting height. Its original boundary
helper 0x40BA10 scans all 4/5/6 tiles of a side. Wooden tower74 uses another path.

In the isolated game, native placement beside tower 54/type 75 at(204,86) produced
a Stone Wall at(208,86), height 98, and a Low Wall at(206,90), height 68. Both have
terrain 8; their rises are 90 and 60. The existing doorway stays above the low wall
at the high-wall position. All four camera rotations were captured. This also
confirms mapper 46 means Low Wall in this UI, despite the old WOODWALL enum name.
Native h.sav and the original decoder/CRC confirm both entrance flags persist.
Fixture SHA256: `8c91afe7e8ba418af0ae387da6ae75a6ce5dfdf150904de26cced4d400cbe07e`.

The wrapper changes only the existing renderGM y argument. It scans the oriented
boundary with the original eligibility rule: logic 0x100 set, 0x2/0x200 clear.
The adjustment is tower terrain plus 90 minus the highest eligible wall height.
This lowers a same-terrain low-wall doorway by 30 native pixels, preserves high
walls, and retains the higher connection when a side has mixed heights. That
mixed/elevated policy still needs its full-game visual acceptance. A side with
no eligible connection retains the original draw position.

The five existing call sites are 0x4E3681,0x4E36D1,0x4E3724,0x4E3777 and0x4E3807.
All are verified before any write. The last call is shared with other buildings;
the wrapper guards tower type, GM and frame. Registers, flags, original draw
count/order, ECX and RET 16 cleanup are preserved. There are no simulation writes,
new assets, input hooks or additional draw calls.

Validation:

- A first native patched check caught swapped doorway sides in the draft.
  Thirty-two original selector calls now independently establish the frame/side
  mapping: at orientation0, frame81 reads side282 and frame90 reads side281.
  The other rotations advance these sides modulo4. The regression failed before
  the correction; the native component harness now includes asymmetric sides.

- 246 focused tests run actual Lua-emitted code assembled with FASM, covering all
  four types, both door sides, four rotations, several terrain heights, low/high
  walls, last boundary tiles, mixed heights, ineligible/absent connections,
  unsupported contexts, signature checks, state/register preservation and ABI.
- The reused native original-renderer harness captures 320 matching draw
  coordinates through the actual 343-byte wrapper, including original per-tower
  offsets. Only terminal drawing is instrumented; this is component evidence,
  not full-game corrected pixels or pathfinding acceptance.
- The installed UCP 3.0.7 code.zip already contains core.allocateAssembly and
  vendor/fasm/fasm.dll. This reuses existing framework support. CI installs the
  FASM CLI solely to execute the same assembly during tests.

One 343-byte startup allocation, 25 replaced code bytes, no per-frame allocation;
each doorway scans at most six tiles. Runtime package: 17 files, 10,654 bytes, 1,803 bytes
above R019. Added rendering/startup cost measurement remains pending.

Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
Only this SHC 1.41 layout is accepted. Default off; English and German labels,
English fallback for other current locales. No Extreme/MP/replay claim.

Before readiness: corrected native low/high/no-wall views, both sides and four
types/rotations; mixed heights, elevation, removal/rebuild and save/reload;
clipping/layout, preserved collision/pathfinding/simulation and relevant costs.
Independent review and normal approved merge remain required.
