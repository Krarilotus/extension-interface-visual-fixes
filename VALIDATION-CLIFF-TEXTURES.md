# Cliff texture direction

Issue16: at map orientations2 and6, the original texture selector uses the Y
coordinate for both cliff faces. A face running along X repeats a single strip
instead of advancing through the texture. Orientations0 and4 already distinguish
the axes. Texture packs can make the repeated strip more obvious, but the wrong
coordinate comes from the game, not a pack.

## Change and compatibility

`computeClimbRampRotation`0x4FC810 classifies the visible faces before selecting
an offset. The fix replaces only its93-byte offset calculation at0x4FC95C,
after validating the full original signature and its address. The result feeds
the existing `updateGfxLayer`0x509180 terrain graphics refresh. The map renderer
continues to read the same prepared graphics layer and call its existing blits.

| Orientation | Face1 | Other face |
| --- | --- | --- |
| 0 | decreasing X | decreasing Y |
| 2 | increasing Y | decreasing X |
| 4 | increasing X | increasing Y |
| 6 | decreasing Y | increasing X |

Increasing uses `(coordinate &31)+1`; decreasing uses `32-(coordinate &31)`.
The original final range clamp and epilogue remain intact. Existing correct
orientations and the already-correct face at2/6 retain their original results.
Unsupported orientations keep the original fallback. EAX classification and
callee-saved registers are preserved; only the existing texture-result field is
written. The code fits in the original space, with NOP padding and no trampoline.

There are no new assets, allocations, callbacks, render hooks, terrain scans or
simulation changes. The combined seven-option allocation total remains66,663
bytes, entirely from the other options. The option defaults off, requires a
restart and uses UCP3.0.7's existing assembler. It targets SHC1.41; Extreme, MP
and replay are not certified by this test. Replacing cliff surfaces below towers
with masonry is a separate idea and is not included.

## Automated checks and native component cost

46 focused tests execute the actual Lua/FASM selector. They cover all four
orientations and six face classifications, coordinate boundaries, the unchanged
cases/fallback, exact write/register effects, signature rejection before writes
and the disabled option. The combined suite passes821 tests, including patch-site
composition and the existing six features.

A private native probe executes the complete original0x4FC810 function with and
without the actual patch. Its12,800 differential cases cover four orientations,
eight neighbouring-height patterns and400 X coordinates. Classification remains
identical; offsets match the rotated face axes and previously correct results
remain unchanged. Original game bytes are not distributed.

Five alternating pairs of one million calls per orientation measure median added
0.830ns,0.441ns,0.907ns and0.557ns for orientations0,2,4,6 respectively. Individual
samples range from-0.980ns to1.779ns, indicating measurement noise at this scale.
Even one million selector calls add less than1ms at each measured median. There
is no additional work in the frame renderer: this replaces an existing graphics
refresh calculation. This component measurement is not full-game FPS or a claim
of literally zero instructions/cost on every machine.

## Native comparison

Pending final corrected-build acceptance. Baseline native session PID10388 uses
SHC1.41/UCP3.0.7, winProcHandler0.2.0 and graphicsApiReplacer1.3.0 at800x600. A
12x12 plateau ends exactly at tower54's east/south footprint edges; adjacent high
and low walls remain below its base. All four orientations were captured with
the cliff option absent and read-only graphics-layer samples retained.
