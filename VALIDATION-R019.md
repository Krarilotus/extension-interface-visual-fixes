# R019: distinct dead-tree stages

Related issue: [#7](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/7).
This draft is stacked on R132 PR #6. Native chop and remaining cost acceptance
remain pending; the four-species visual comparison, reload and decay now pass.

Original SHC 1.41 UpdateTree1 at 0x4F2380 selects native frame 146 for both stages
5 and 6 of species 1–4. Inspection of all four original sheets confirms frame
146 is the fallen log, 147 the standing dead tree and 148 the flat-view stump.
These are one-based native frame numbers. No new or modified art is included.

The existing renderMap frame load at 0x4EB831 now uses a 58-byte wrapper. Only
species 1–4 at stage 5 with stored frame 146 produce local EDX frame 147. Every
other register and the flags from the preceding TEST remain intact. Stored tree
fields are never written. Stage 6 still selects 146 and follows its original
removal lifecycle; the fix does not extend dead-tree lifetime.

Validation so far:

- 290 new tests execute the actual Lua-emitted x86 across eight species values,
  five stages and seven frames, checking local frame, ABI and unchanged complete
  tree records, plus eight felled-tree regressions, signature rejection and disabled/repeated enable.
- All 428 repository tests pass, including the earlier R007/R130/R132 cases.
- The reused original-code native component harness covers 56 frame cases and
  eight decay boundaries and eight harvest flows. Harvest eligibility and resource
  depletion leave stage 5 intact while setting harvest state 2; these original
  functions exposed a draft regression, reproduced by eight failing emitted-code
  cases before adding the guard. It executes original functions, with no running game
  attached; it is not full-game visual acceptance.
- The existing native skirmish save contains 59 species-2 trees at stage 5. Its
  compressed tree section was decoded with the original game decoder and verified
  against its original checksum, providing a fixture lead without modifying it.

Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
Only this SHC 1.41 layout is supported. The separate Extreme signature is not
accepted. No new dependency, asset or draw/input hook is introduced. One 58-byte
startup allocation and six changed code bytes. The runtime package has 16 files
and is 8,851 bytes, 1,384 bytes above R132. A native benchmark of the actual
emitted wrapper adds median 4.028 ns for living trees and 4.571 ns for dead trees
over five paired runs of two million calls. This excludes the original renderer;
full-game render cost remains pending.
All options default off.

The native comparisons below exercised the earlier 48-byte wrapper; the new
harvest guard still needs its native recheck. Full-game comparison uses an isolated synthetic w.sav: eight native-constructor
trees at existing grid positions, with surrounding trees in native pending-removal
state to avoid occlusion. Original native cleanup clears the neighbors. All four
species retain stage 5 and stored frame 146 while the patch renders standing-dead
art. Four living controls retain their existing art and animated frame range.
P pauses the test before the original short decay period removes a sample.

[Original view](docs/native-trees-original.png) and
[patched view](docs/native-trees-patched.png) use the same camera and fixture.
The flat-view fixture region (510,180)-(800,345), in 1282x746 captures, is pixel
identical between original and patched. The game is configured at 1920x1080,
rendered in a 1280x720 graphicsApiReplacer window. R007/R130/R132 are also enabled.
The actual installed R019 Lua SHA256 is
`8ed9562d818a5502d12c826a350578432ef210de9d45ab16993f4f70a0fef9e8`.

A new native d.sav is 876,248 bytes, SHA256
`160ec5609a00b15ee0f78bcf92be0aaf247613df8665976f07162dc0f572df03`.
Original-decoder/checksum verification confirms all four dead records are still
stage 5/frame 146 in that save. A fresh native process reloaded d on 11 September
with all eight fixture records present. The four dead trees then disappeared
through natural decay while the four living controls stayed stage 3 and animated
through frames 1-25. Bounded 50 ms read-only samples captured the short stage-6,
state-3, frame-146 transition for species 1 and 4, followed by cleared records;
species 2 and 3 were observed before and after removal, without capturing their
brief intermediate state. No product lifetime or saved tree state was altered.

The woodcutter reached the test area, but falling settlement popularity removed
its labor before a chop was established. This is inconclusive, not a chop pass.
All native sessions were closed normally and the shared desktop released after
each; the d reload pass used seven of its eight reserved minutes.

Before readiness: native chop and remaining
simulation/cost checks. Multiplayer, Extreme and replay remain untested. English and
German option labels are provided; other existing locales use English fallback.
Independent review and normal approved merge remain required.
