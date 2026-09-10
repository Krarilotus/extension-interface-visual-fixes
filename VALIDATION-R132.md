# R132: building preview during camera movement

Related issue: [#5](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/5).
Stacked on R130 PR #4, which is stacked on R007 PR #2. Independent review and
native patched acceptance remain required; this is not a merged/released fix.

## Cause and change

Original SHC1.41 handler0x4451c0 computes mouse world coordinates, then skips its
preview/placement path while scrolling unless a new left click starts. The
native read-only trace confirmed camera movement and scrolling=1 while the
selected woodcutter51 preview stayed at333,194. The ghost disappeared and returned
after scrolling stopped. This was reproduced with graphicsApiReplacer1.3.0's
existing control.padding=20, UCP3.0.7 and winProcHandler0.2.0, at1920x1080 rendered
in a1280x720 window. The reference executable SHA256 is
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.

The six-byte conditional branch at0x445263 now enters a39-byte wrapper. When
scrolling, it permits the existing path only if the already-computed building
size is positive and neither a held left button nor release event is pending.
New clicks still bypass this guard through the original jump. Every register,
stack slot and the incoming comparison flags are preserved. No second renderer,
input registration, polling callback or command format is added.

Original size lookup0x4fa550 was evaluated for mapper0..399. Positive sizes cover
buildings, siege tents and brush previews; assembly points, editor units and
special sprite tools are excluded by their nonpositive size. Other handler paths
remain unchanged. The patch is separate from R0070x4287bd and R1300x516a0f.

## Automated evidence

-138 repository tests pass:82 R132 cases plus the existing56 regressions. Actual
  Lua-emitted x86 executes through the original new-click/scroll gate for all
  combinations of scrolling/start/held/release and sizes-1,0,1,3,13.
-The actual emitted patch also passes48 comparisons against the original full
  UI handler for woodcutter, marketplace and engineers guild. Terminal transform,
  eligibility, render and command helpers are stubbed. Idle scrolling adds the
  preview call without resource/command calls; other call traces match baseline.
-Original signature matches once; missing, duplicated, shifted or already-changed
  layouts are rejected. Original executable bytes are not distributed in tests.
-Windows local invocation uses `pytest -p no:faulthandler` because Unicorn's
  handled virtual-memory exceptions otherwise print misleading fatal-exception
  traces despite successful assertions. Linux CI runs the ordinary pytest command.

Runtime package:15 files,7467 bytes,1402 bytes above R130; no new dependency.
One39-byte startup allocation and six changed code bytes. Additional camera-frame
work is the existing idle eligibility/preview path. Whole-game frame cost and
patched native layout/placement checks are pending. English and German labels are
provided; other existing locales use explicit English fallback for this option.

## Native gates still pending

Patched edge scrolling, preview-to-commit tile equality, valid/invalid targets,
zoom/orientation and supported layout checks; drag/release regression and relevant
frame cost. Multiplayer, Extreme and replay compatibility are not claimed.
R007/R130 remain independently selectable; all options default off and require
a game restart to change.
