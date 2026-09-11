# Diagonal cliff sequencing

Draft native acceptance; this candidate is not released.

Version 0.1.3 assigned one index to both visible faces. Its rotated x+y phase
advanced along straight sides but stayed constant on one diagonal. The opposite
diagonal skipped an index between tiles while duplicating each tile's two faces.
The bank contains 32 rock strips, followed by non-rock/waterfall images.

The candidate uses the horizontal projection x-y, -x-y, y-x, or x+y for rotations
0, 2, 4, or 6. A native column contains complete consecutive strips in screen
order: its left half uses N and its right half N+1, with 32 wrapping to 1.

```text
Straight boundary:       1 -- 2 -- 3 -- 4
Front-facing staircase: [1|2] [3|4] [5|6]
```

Staircases extending directly into the view overlap in depth at constant screen
X. During the existing terrain refresh, the selector checks only the immediate
forward/back diagonal neighbours for equal effective height and the same exposed
side. Those steps use deterministic coordinate variation. This is not a boundary
walk, per-frame check, random-number call or new per-tile cache. Wall tiles use
the terrain height, matching the original face classifier.

The two existing blitter hooks still own source conversion. Their two native
image globals continue serving vertical layering; they are not repurposed as
left/right inputs. Each cached projection pairs adjacent validated source copies.
A source change invalidates its own pair and the preceding pair. Originals are
compared once per render frame, even when shared by two pairs; storage remains
one source copy plus one projection per image. No draw call or frame hook is added.
If a neighbour is unavailable or has different dimensions, the validated current
strip supplies both halves until compatible data returns. Non-rock images retain
the native source; original resource pointers and pixels remain untouched.

Automated: 1,395 tests pass, including straight sides, both staircase directions,
all rotations, stable variation, wraparound, neighbour changes and cache sharing,
source bounds at 11 heights, allocation failure and all seven existing fixes.
Original regular-game native blitters pass all 160 nonempty pixel comparisons
across five heights, both blitters, four face masks, both zooms and top clipping.
Extreme native comparison, measured costs and in-game octagonal fixture acceptance
are pending. Exact unpublished artwork is for its author's later check.
