# R023: tower doors follow their connecting walls

Closes [issue9](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/9).
R019 PR8 is merged. This PR targets main and remains draft until native acceptance
of the new horizontal positioning and cache implementation is complete. Earlier
height-only screenshots do not prove this revised behavior.

## Behavior

For each stone-tower side independently, choose the highest eligible connecting
wall. Among equally high walls, choose the connection nearest the side centre.
An exact centre-distance tie uses the first tile in the fixed native boundary
order. A higher off-centre wall therefore wins over a lower centred wall. Move
the existing doorway along the tower face and vertically to the chosen wall.
The original game still decides whether the doorway is drawn. No qualifying
connection leaves the original draw arguments unchanged.

The native boundaries, relative to tower origin(x,y) and width w, are north
(x+n,y-1), east(x+w,y+n), south(x+w-1-n,y+w), west(x-1,y+w-1-n), with n0..w-1.
The original selector probes establish frame81/frame90 sides: south/east at
orientation0, west/south at2, north/west at4 and east/north at6. Position changes
follow the same isometric face: each boundary step is -16X and -8Y for frame81,
or -16X and +8Y for frame90. Even-width side centres include half-tile offsets.
The vertical height correction is tower terrain+90 minus absolute wall height.
Eligibility retains the original logic0x100 set,0x2/0x200 clear rule.

## Ownership and cost

Original renderGmOverlayBuilding2 uses fixed GM54 frame81/90 offsets for tower
kinds75-78. The five existing drawing calls are0x4E3681,0x4E36D1,0x4E3724,
0x4E3777 and0x4E3807. The wrapper preserves their order/count, registers, flags,
ECX and RET16 cleanup and only adjusts X/Y arguments.

The original computeBuildingEntranceFlagsForOrientations0x41B7C0 already visits
all16/20/24 boundary tiles every40 tower updates. Two hooks at0x41B7FF/0x41B855
collect the selected connection during that loop; they add no second scan or
update callback. Warm drawing reads a cached entry, with no wall/row-array reads.
A cold visible side is scanned once after load or building-slot reuse, at most
six tiles. Existing map setup0x512100 invalidates entries by epoch. UID and origin
checks prevent a reused slot retaining the previous tower's connection. The
cache is private presentation memory and is not serialized or written into game
records. Placement/removal refresh on the game's existing40-update cadence.

Eight signatures are validated before allocation/writes. Six startup code blocks
total794bytes; private zeroed data uses65,540bytes. The patch replaces44 original
instruction bytes. There are no per-frame allocations, new input registrations,
additional drawings, assets or runtime dependencies; it uses the existing FASM
support supplied by UCP3.0.7. All options default off and require a restart.

## Automated and native component evidence

258 focused tests execute the actual Lua/FASM instructions. They cover all four
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
of200,000 tower draws/refreshes measure median added20.052ns per tower draw
(two doors), and156.046ns per connection refresh. That is0.0201ms per1000-tower
draw pass and0.156ms per1000-tower connection pass, or0.00390ms amortized across
1000 tower updates at the unchanged40-update interval. A first cold1000-tower
draw pass took0.0743ms total versus0.0296ms warm. This intentionally heavy native
component workload tests accelerated execution; it is not a1000-speed game-menu
setting, full-game FPS, rasterization measurement or universal worst-case claim.
Original game bytes and private image data are not distributed.

## Native acceptance pending for the revised code

Earlier height-only implementation b5df175 passed native low/high joins for all
four tower types, mixed-height selection, removal, rotations and save reload.
Those results established the cause and fixtures, but horizontal movement and
cache lifecycle require new captures of the current source. Use m.sav with low
wall299,252 on square tower20; add high wall300,252, then a farther high wall,
remove the selected wall and confirm both the selected connection and doorway
move. Rotate using the native controls and reload m to check invalidation.

Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.
UCP3.0.7, winProcHandler0.2.0 and graphicsApiReplacer1.3.0; isolated1920x1080
configuration rendered in a1280x720 window. Multiplayer, Extreme and replay are
not claimed. The change does not alter pathfinding, collision or simulation
commands. Localized English/German descriptions state the selection and movement;
other existing option catalogs retain explicit English fallback for this option.
