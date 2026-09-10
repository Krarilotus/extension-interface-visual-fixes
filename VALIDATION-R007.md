# R007 validation

## Cause and correction

The name lookup at SHC `0x46d390` selects the string table for recognized
shipped map names. It leaves the global source flag unchanged for custom names.
The lobby map list uses that lookup for other rows. The selected custom map's
description renderer consequently sees a flag written for another map and skips
its embedded text. Its bytes and measured height remain intact.

The patch resets the source flag immediately before the existing selected-name
lookup at `0x4287bd`. The original lookup then selects the appropriate source.
It uses the existing title, description font, clipping, scrolling and layout.
The shared name lookup itself and other callers are unchanged.

One 15-byte wrapper: a 10-byte store followed by a tail jump to the original
lookup. The original call site changes by five bytes. There is no extra lookup,
input hook, render pass, frame polling, persistent state or runtime dependency.
MOV/JMP preserve incoming flags/registers; the original cdecl return address and
arguments stay in place. Allocation occurs once during module enable.

## Evidence and tests performed

Reference SHC 1.41 executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
Original report/fixtures:
[UCP2 #878](https://github.com/UnofficialCrusaderPatch/UnofficialCrusaderPatch2/issues/878).

- 20 automated tests execute the actual Lua-emitted x86 wrapper. They cover
  stale source values, selected custom/shipped lookup behavior, register/flag/
  stack preservation, unsupported layout, disabled option and repeated enable.
  Run `python -m pytest -q` after installing `requirements-test.txt`.
- Local original-code emulation runs 16 lookup sequences against the reference
  executable, with only terminal character/string and localized-resource access
  stubbed. It reproduces stale source selection and verifies the wrapper.
- Both supplied maps decode with the original decoder and matching CRC32.
  Live native sampling confirms embedded bytes, scroll=-19 and an incorrect
  string-table source flag/index0 while descriptions are missing.
- Native before/after: official UCP 3.0.7 release, winProcHandler0.2.0,
  graphicsApiReplacer1.3.0, fresh isolated profile, 1280x720. The emitted wrapper
  was installed using bounded debugger-style instrumentation in the isolated
  process. Both supplied custom descriptions appear. Repeated switching to
  shipped maps preserves their descriptions; leaving/re-entering the lobby
  preserves the fix. This comparison used emitted-code instrumentation.
- Actual module-loader acceptance: developer UCP loader, official 3.0.7 code,
  the same two compatibility modules, and only this fix enabled. The startup log
  confirms successful module load/enable. Both report fixtures, shipped maps,
  screen re-entry, German umlauts/eszett and wrapping pass. An original-code
  encoder/decoder round-trip verified three additional map fixtures. Long text
  scrolls to its final marker using the existing controls; selecting an empty
  description removes all previous text. The alternate saved resolution was
  1280x1024, displayed through the compatibility module's scaled window.
- The native TCP/IP multiplayer host lobby also passes shipped/custom switching,
  German text, scrolling to the end and empty-after-long clearing. Description
  clipping stays within its existing pane alongside the player/chat/map controls.
  This was a host-only session: a remote client and synchronization are untested.
- A native x86 microbenchmark of the actual 15-byte wrapper used five paired
  runs of 20 million calls with alternating baseline/patched order. Added cost
  was 0.330–0.512 ns per call (median 0.451 ns) on this desktop. This measures
  wrapper overhead against a terminal lookup stub, not whole-game frame time.
- Original scrollbar emulation (44 cases) rejected an earlier range-clamp
  hypothesis; no scrollbar patch is included.
- SHC and Extreme signatures each match once. Extreme static addresses are
  call `0x4287ed`, lookup `0x46d5b0`, source flag `0x2a7c764`.
  This does not establish Extreme native compatibility; it is not declared.

## Remaining gates

Native comparison: [before](docs/native-test-missing-before.png),
[after](docs/native-test-visible-after.png).
Module acceptance: [German text](docs/native-module-german.png),
[multiplayer host long-text end](docs/native-module-mp-long-end.png),
[empty after long](docs/native-module-mp-empty.png).

CI activation, independent review and normal approved merge remain pending.
Remote-client lobby acceptance needs a second test session. Extreme, multiplayer synchronization,
save/replay and full compatibility are not claimed from the automated tests.
No simulation, command, save-format or asset changes are made.

The original legacy graphics path failed during startup on this desktop.
Tests therefore use the existing graphics/window compatibility modules above.
Audio and active replay installations/branches remain separate.

Candidate package: 13 runtime files, 3,751 bytes compressed; no dependencies
added. The build manifest excludes tests, diagnostics, screenshots and tooling.
CI has not run: the current OAuth credential cannot publish GitHub workflows.
The intended workflow is preserved in `.ci/test.yml`; activation at
`.github/workflows/test.yml` requires credentials with `workflow` scope.
