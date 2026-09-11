# Single-player lobby Load (R001)

The native Load item exists in the lobby but its renderer skips single-player
skirmish. Its action also uses Start's valid-team-count gate, blocking human-only
loading. This optional correction draws the original icon and accepts the Load
action in single-player without requiring an AI opponent. Host/readiness,
modal/transition guards and every original loader/navigation operation remain.

Implementation scope: SHC1.41 only. Load renderer JE at0x42afb9 goes to the
existing active-button block0x42affd for mode99; all other modes fall through
unchanged. Load-only compare/branch at0x4426e0 redirects through27bytes that
exempt mode99 and preserve the original comparison for all other modes. Start's
separate comparison and shared team helper are untouched. The existing menu
table, pixel hit test, GM art and localized tooltip are reused. No menu/cffi
dependency, additional input hook, polling, save/state/serializer change.

The user also requested a single-player-only position correction after noticing
the master portrait overdraws the icon. Lobby preparation at0x42733a..0x427343
now sets the existing Load item's x at0x5e998c to560 for mode99 and restores444
for every other mode. Its y remains540. A46-byte wrapper preserves flags and
registers and replays the original secondary-mode write. Both native drawing
and alpha hit testing read the same item; no render-time position update is used.
Original normal/hover Load frames are45x58, the master portrait spans
x409..529/y452..553 and Start's native hit rectangle begins atx620.
The new Load rectangle x560..605/y540..598 fits the800x600 menu canvas.

Integration: sibling of R130 based on R007a765ded, approved by the Interface
owner in PR2 comment5626163468 and directly assigned by the user. R0070x4287bd
does not overlap these sites. The additional preparation hook implements the
user's subsequent explicit SP-only positioning request. Other Interface branches
remain separately owned.

## Validation completed

- 66 automated tests: existing20R007 plus46R001, actual Lua-emitted x86 branches,
  mode/team boundaries, register/stack preservation, disabled/idempotent enable,
  signature/layout rejection and option composition. Includes SP/MP navigation
  in both directions, position reset, untouched item fields, preserved flags,
  displaced instruction replay and minimum-canvas bounds.
- Private original-executable fixture:54 original-code cases and160 comparisons
  using actual Lua output through the original action/renderer/team helper,
  with terminal draw/dialog stubbed. Other tested modes0/1/2/666 compare equal;
  MP host/client, readiness, one/two players and same/distinct teams included.
  Modal/transition blocking remains. This is not a live MP test.
- Native SHC1.41 baseline reproduced human-only refusal and human+Rat hidden
  target opening. Back/reopen and g.sav load worked before the patch.
- Earlier packaged module, before repositioning, with R001 and R007 enabled:
  original Load icon visible
  in human-only and human+Rat lobbies; both open native Load; human-only Back
  returns to lobby; subsequent reopen and g.sav loading work. R007 custom map
  description appears in the same lobby. English tooltip/dialog, original art,
  but the master portrait overlaps its top13pixels. This prompted the position
  correction above; these captures do not validate the new position.
  Native video options confirm1920x1080. Captures are
  scaled1282x746 window images and are not themselves resolution evidence.

Exact test executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
Developer loader, official UCP3.0.7 code.zip SHA256
`ee93555d0455cde4fc68dc5434203142aa0acbc43882d819525c4077be833e00`,
winProcHandler0.2.0 and graphicsApiReplacer1.3.0, padding20. Isolated profile.
g.sav SHA256`bf32e750ea38cfaeae0bd7387fc0b133b9b8e0be06cc53aa2c6aec0dadba378e`.
Native module enable recorded2026-09-11 08:22:31; game closed and slot released
08:26:29. Logs, original-code fixtures and save hashes are retained in the
assigned workspace `Roadmap/Investigations/R001-lobby-load/evidence`.

## Remaining acceptance

Native new-position rendering/hover/click and SP-to-MP position reset;
packaged option-off; empty/invalid save list handling; minimum/default
layout and long translated game tooltip; focused MP host smoke. No native
Extreme/remote multiplayer/replay certification is claimed. Nine maintained
launcher locales (en/de/fr/ru/hu/tr/ch/es/fa) contain matching keys; independent
translation review remains pending. In-game resources follow game language,
launcher option follows GUI language.

Runtime package14files6113bytes, +2362bytes over R007's3751byte archive, no new
dependency.73 allocated code bytes,21 overwritten instruction bytes. Three
startup AOB lookups, one extra original button draw in the SP lobby per frame;
no per-frame allocation/scanning. Action guard executes only when Load reaches
the existing team comparison. Whole-frame and startup timing not benchmarked.
Position work runs only during native lobby preparation. Package SHA256:
`cb0924ddd410dd41b1a365344e1a14cd100581696af98db8a634a7ec9daa1980`.

The first repositioned native build exited on entering the lobby. Its replayed
MOV used a nested small integer, which UCP compiles as one byte rather than a
dword. Corrected to four explicit bytes and fixed the test compiler's matching
mistake. All66 tests pass again; a private fixture now compares emitted bytes
against the actual hash-checked UCP3.0.7 core.compile/writeCode/jmpTo at four
allocation bases. Original-code gates also pass again. Revised native retry
is required; the initial failed run is not acceptance.

PR remains draft until material native gates pass. Independent review and normal
approved merge remain required; no release or completed issue resolution.
