# R019: distinct dead-tree stages

Related issue: [#7](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/7).
This draft is stacked on R132 PR #6. Full-game native acceptance remains pending.

Original SHC 1.41 UpdateTree1 at 0x4F2380 selects native frame 146 for both stages
5 and 6 of species 1–4. Inspection of all four original sheets confirms frame
146 is the fallen log, 147 the standing dead tree and 148 the flat-view stump.
These are one-based native frame numbers. No new or modified art is included.

The existing renderMap frame load at 0x4EB831 now uses a 48-byte wrapper. Only
species 1–4 at stage 5 with stored frame 146 produce local EDX frame 147. Every
other register and the flags from the preceding TEST remain intact. Stored tree
fields are never written. Stage 6 still selects 146 and follows its original
removal lifecycle; the fix does not extend dead-tree lifetime.

Validation so far:

- 282 new tests execute the actual Lua-emitted x86 across eight species values,
  five stages and seven frames, checking local frame, ABI and unchanged complete
  tree records, plus signature rejection and disabled/repeated enable.
- All 420 repository tests pass, including the earlier R007/R130/R132 cases.
- The reused original-code native component harness covers 56 frame cases and
  eight decay boundaries. It executes original functions, with no running game
  attached; it is not full-game visual acceptance.
- The existing native skirmish save contains 59 species-2 trees at stage 5. Its
  compressed tree section was decoded with the original game decoder and verified
  against its original checksum, providing a fixture lead without modifying it.

Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
Only this SHC 1.41 layout is supported. The separate Extreme signature is not
accepted. No new dependency, asset or draw/input hook is introduced. One 48-byte
startup allocation and six changed code bytes. The runtime package has 16 files
and is 8,800 bytes, 1,333 bytes above R132; native render cost remains pending.
All options default off.

Before readiness: full-game original/patched comparison for all four species,
dead-stage transition, flat/living/wind/chop views, save/reload and unchanged
simulation traces. Multiplayer, Extreme and replay remain untested. English and
German option labels are provided; other existing locales use English fallback.
Independent review and normal approved merge remain required.
