# R023: tower doors follow their connecting walls

Closes [issue9](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/9).
R019 PR8 is merged. This PR targets main. Native acceptance of horizontal
positioning, connection refresh and load invalidation is complete. Earlier
height-only screenshots are not used as proof of this revised behavior.

## Behavior

For each stone-tower side independently, choose the highest eligible connecting
wall. Among equally high walls, choose the connection nearest the side centre.
An exact centre-distance tie uses the first tile in the fixed native boundary
order. A higher off-centre wall therefore wins over a lower centred wall. Move
the existing doorway along the tower face and vertically to the chosen wall.
The original game supplies the doorway draw calls. The wrapper suppresses a
doorway when that side has no qualifying connection. An outermost connection
places its doorway half a tile inward; interior positions remain unchanged.

The native boundaries, relative to tower origin(x,y) and width w, are north
(x+n,y-1), east(x+w,y+n), south(x+w-1-n,y+w), west(x-1,y+w-1-n), with n0..w-1.
The original selector probes establish frame81/frame90 sides: south/east at
orientation0, west/south at2, north/west at4 and east/north at6. Position changes
follow the same isometric face: each boundary step is -16X and -8Y for frame81,
or -16X and +8Y for frame90. Even-width side centres include half-tile offsets.
The vertical height correction is tower terrain+90 minus absolute wall height.
Eligibility requires the original logic0x100 set and0x2/0x200 clear, plus no
raised-stair flag0x800 and connection height at least the tower terrain base.
Original placeDefensiveStructureTile0x5034A0 assigns stair1–5 that raised-stair
flag and rises80/64/48/32/16. Stair6 retains terrain height and receives0x100,
so it supplies a ground-level doorway without another wall. Below-base walls
are excluded rather than placing a door into the terrain. Existing qualifying
gatehouse tiles continue to work; this does not add keep connections or change
which crenellations the native entrance flags accept.

## Ownership and cost

Original renderGmOverlayBuilding2 uses fixed GM54 frame81/90 offsets for tower
kinds75-78. The five existing drawing calls are0x4E3681,0x4E36D1,0x4E3724,
0x4E3777 and0x4E3807. The wrapper preserves registers, flags, ECX and RET16
cleanup, adjusting only X/Y or suppressing an inaccessible doorway. It adds
no draw calls and does not change entrance flags or pathfinding.

The original computeBuildingEntranceFlagsForOrientations0x41B7C0 already visits
all16/20/24 boundary tiles every40 tower updates. Two hooks at0x41B7FF/0x41B855
collect the selected connection during that loop; they add no second scan or
update callback. Warm drawing reads a cached entry, with no wall/row-array reads.
A cold visible side is scanned once after load or building-slot reuse, at most
six tiles. Final map preparation0x512450 invalidates entries by epoch. UID and origin
checks prevent a reused slot retaining the previous tower's connection. The
cache is private presentation memory and is not serialized or written into game
records. Placement/removal refresh on the game's existing40-update cadence.

Eight signatures are validated before allocation/writes. Six startup code blocks
total851bytes; private zeroed data uses65,540bytes. The patch replaces45 original
instruction bytes. There are no per-frame allocations, new input registrations,
additional drawings, assets or runtime dependencies; it uses the existing FASM
support supplied by UCP3.0.7. All options default off and require a restart.

## Automated and native component evidence

300 focused tests execute the actual Lua/FASM instructions. They cover all four
tower types, both door frames, all four rotations, terrain heights, low/high and
mixed walls, endpoint connections, absent/ineligible walls, ABI and complete
building-record preservation. New cases prove height-before-centre selection,
deterministic centre ties, removal refresh, epoch/UID invalidation, collision-free
cache indexing for all2000 native slots and zero wall/row reads over100 warm draws.
The original connection loop's overwritten load and flag-reset instructions
retain their exact register/flag and game-memory effects.

A private native benchmark executes original0x41B7C0 and0x4E2AD0 with the actual
patch and captured native map data. A1000-record synthetic workload uses all four
tower kinds and eligible walls along every boundary. Cold and warm original
renderer coordinates are asserted for both door frames. Five alternating pairs
of200,000 tower draws/refreshes measure median added30.609ns per tower draw
(two doors), and146.739ns per connection refresh. That is0.0306ms per1000-tower
draw pass and0.1467ms per1000-tower connection pass, or0.00367ms amortized across
1000 tower updates at the unchanged40-update interval. A first cold1000-tower
draw pass took0.1017ms total versus0.0427ms warm. This intentionally heavy native
component workload tests accelerated execution; it is not a1000-speed game-menu
setting, full-game FPS, rasterization measurement or universal worst-case claim.
Original game bytes and private image data are not distributed.

## Native acceptance of corner, stair and cliff correction

Runtime revision2b589f5 passed775 combined tests and a native SHC1.41 session
on11September2026, PID20624. At800x600 in the1280x720 wrapper, four prepared
saves were loaded consecutively. The same tower54 UID was retained, while the
cache epochs advanced1/2/3/4 and the selected connections changed correctly:

- Edge: east index0,height98; south index1,height68. The outer high connection
  has a half-tile inset. This save keeps the previously naturally placed geometry.
- Stair6 alone: south index1,height8, at tower base8; ground-level door visible.
- Raised stair alone: height88 with0x800; no connection selected and no door.
- Cliff: tower base104, wall top68; no connection selected and no door in terrain.

The stair/cliff cases are controlled offline fixtures using the documented native
tile values, not claims about building placement or troop traversal. Only the
test setup alters those saves; the product only alters presentation. Read-only
native samples verify tile logic/heights and cached selection. The screenshot
gallery shows all four outcomes. The game closed normally and the desktop was
released at11:41:47 CEST. A separate cliff-texture suggestion is outside this fix.

## Earlier native acceptance of selection and cache lifecycle

Earlier height-only implementation b5df175 passed native low/high joins for all
four tower types, mixed-height selection, removal, rotations and save reload.
New native captures of d3f43159 verify the same final drawing and connection-cache
instructions used by43e61945. In m.sav, square tower20 has a low wall at299,252
(height68). Native placement adds high walls at300,252 and298,252 (height98).
The cache selects300,252, the nearer of the two equally high connections. Native
deletion of that selected wall changes selection to298,252; the doorway moves
along the face to the remaining high connection, despite the nearer low wall.
Native rotation0 to2 retains that selection on the appropriate visible face.
See [the captioned screenshots](docs/r023/README.md). Read-only geometry samples
record both wall candidates and the cache choice; no live game memory was edited.

Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
UCP3.0.7, winProcHandler0.2.0 and graphicsApiReplacer1.3.0; isolated1920x1080
configuration rendered in a1280x720 window. Multiplayer, Extreme and replay are
not claimed. The change does not alter pathfinding, collision or simulation
commands. Localized English/German descriptions state the selection and movement;
other existing option catalogs retain explicit English fallback for this option.

The first cached native pass exposed an incomplete load invalidation hook:
setupAllMapSections0x512100 runs for initial setup/MP loading, but the SP load
branch skips it. The counter stayed1 across SP reload. Final prepareMap0x512450
is called after both SP/MP section loads and new-map creation; invalidation now
uses that shared boundary. The emitted-code regression restores an identical
UID/origin with changed geometry and verifies a fresh selection immediately.
The final43e61945 code was then installed in the combined six-option package
(ZIP SHA2565e3146b40a7eff7e8ab26792eba08417097cb998395f6abaf558698809b35678).
Native SP loads m -> h -> m advanced the cache epoch1 ->2 ->3. Tower20 returned
to low wall index3,height68; small tower54 independently selected east high
index0,height98 and south low index1,height68. The final native process was
closed normally and the desktop released at10:35:54 CEST on11September2026.
The load-hook change is outside the steady-state render/update paths.
