# Lower door draw order: candidate validation

Related to [issue 19](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/19).
The user's screenshots disproved the earlier complete visual acceptance in
`VALIDATION-TOWER-FOUNDATIONS.md`. In particular, the last foundation column
could cover a lower doorway. The previous screenshots are historical evidence,
not proof that this defect or the separately reported cliff seams are resolved.

## Cause and correction

The native tower overlay can run before all foundation columns have been drawn.
In the `iv-cliff-corner` reproducer, the left door's original draw at (522,290)
is followed by its tower's column at (534,392). The latter overwrites 289 of the
door's 791 opaque pixels. The height lookup is identity at the relevant heights;
changing the vertical height conversion would not fix this ordering problem.

The candidate retains a below-base doorway until its own foundation has been
painted through the sprite's horizontal extent. It emits the original sprite
call exactly once. Connection selection and its existing cache are unchanged.
Presentation state expires at each native map-render entry so clipped pending
doors cannot leak across frames, camera movements or loads.

New guarded patch sites are map-render entry `0x4E8CF0` and the existing foundation
column call `0x4EBA52`. All signatures are validated before any write. No new
connection scan, simulation hook, asset or separate render pass is added.
The seven-option allocation is 149,422 bytes, an increase of 82,406 bytes,
including an 81,924-byte presentation cache. It is never serialized.

## Completed checks

943 combined tests pass. The emitted x86 regressions cover both door faces,
waiting for the correct tower column, exactly one draw, already-painted backing,
frame expiration, unchanged registers/flags and restoration of native drawing
state. Existing connection ranking, placement, camera and composition tests pass.

The isolated native test used SHC 1.41 / UCP 3.0.7, all seven options,
winProcHandler 0.2.0 and graphicsApiReplacer 1.3.0. Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
The loose development module was the candidate, not published version 0.1.1.

The fixture places tower54/type75 at (204,86), width4, base104, flush with two
plateau edges. The east wall is at terrain8/top98; the south wall is at
terrain8/top68. Native captures and a bounded call trace from PID18720 cover
orientations 0,6,4,2. The trace records four visible doorway draws across those
views. A pixel-write audit finds zero doorway pixels overwritten by subsequent
recorded columns in each view. This audit does not model other scene occluders.
The native game is closed; no diagnostic probe belongs in the release package.

## Cost and remaining gates

An MSVC2005 SP1 native component benchmark executes the emitted x86 using 1,000
synthetic tower records and seven alternating baseline/candidate timing pairs.
Each arm makes one million column calls. Median added bookkeeping is 6.381 ns
per non-tower column, 8.139 ns per warm tower column, 8.053 ns for a tower's first
column in a frame, and 11.296 ns for flushing one pending door. Both arms use
empty draw terminals to isolate bookkeeping; the flush case includes the sprite
call but does not render pixels. These are component costs, not full-game FPS or
a tested 1000-speed simulation setting.

This candidate still needs native zoom/clipping, AI stair6 and wider tower-kind
acceptance. The new edge-position feedback is also open: the current formula
clamps to one-based positions 1.5 through N-0.5 relative to a presumed centred
native sprite anchor. Actual wall contact and doorway alignment must be verified
independently before calling that inset visually correct. Highest connection
first, centre breaking ties remains the agreed selection rule.

Cliff seams remain separately open in issue 16. Do not publish the final Store
patch or reuse old screenshots as acceptance until these remaining gates pass.
