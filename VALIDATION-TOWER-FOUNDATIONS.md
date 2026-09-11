# Tower masonry and lower connecting doors

**Acceptance reopened:** the user's later screenshots show foundation columns
covering a lower door. The edge inset also needs independent alignment checks.
See [the draw-order follow-up](VALIDATION-DOOR-DRAW-ORDER.md) for the confirmed
cause, candidate checks and remaining gates. The earlier results below are
historical and do not establish complete visual acceptance.

Issue [19](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/19).
The existing tower-door option now extends wall masonry beneath exposed tower
footprints. A lower connection can supply a door where the adjacent inner tile
belongs to that tower. Highest connection wins; nearest centre breaks ties.
Outermost joins remain inset half a tile. Stair6 alone qualifies; raised stairs
1–5 do not. This changes presentation, not terrain, access or pathfinding.

## Cause and implementation

The original graphics refresh at `0x509180` assigns cliff GM9 columns beneath
building footprints. Walls instead use GM10 masonry and the existing ordinary
vertical clipping path. The tower-specific correction at `0x50EDAF` writes a
GM10 column and clears only the `0x800` clipping-offset flag. It reuses the face
classification already computed by the caller and the native straight wall
column formulas. Other building kinds keep the original branch. No assets,
render pass, polling loop or simulation hook are added.

The existing connection ranker previously rejected everything below the tower's
terrain base. It now accepts those joins only when the adjacent inner footprint
tile belongs to the same tower. Empty or foreign backing remains excluded.
The native connection update and cold cache initialization perform this check;
warm drawing does not scan tiles. Map reload and building reuse retain the
existing cache invalidation.

The nine patch signatures are checked before any allocation or write. Native
startup caught a repeated foundation signature; the final signature includes
the preceding store/jump and was verified unique in the reference executable.
The new graphics branch is 220 bytes; the backing guard adds 133 bytes. Combined
seven-option allocation is 67,016 bytes, 353 bytes more than before. The package
still has 19 files and seven initially disabled options, with no new dependency.

## Verification

925 combined tests execute the emitted Lua/FASM code. Foundation tests cover
all four tower kinds, rotations, straight/corner classifications, preserved
registers/flags, exact graphics writes and unchanged other-building fallbacks.
Door cases cover lower high/low walls, stair6 alone, raised-stair exclusion,
foreign/empty backing, height-before-centre selection and existing invalidation.
A private original-code probe matched 12,800 native straight wall-column results.
Original game bytes and private fixture saves are not distributed.

Native SHC1.41/UCP3.0.7 tests used runtime `2ae1ba0`, all seven options enabled,
winProcHandler0.2.0 and graphicsApiReplacer1.3.0. The package SHA256 was
`2812704878ac27f15007255a5e147d8416dd8dd11fa686ec83933af3c3961ecd`.
Later documentation/localization edits do not change the tested runtime.
Reference executable SHA256:
`3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a`.

In `iv-cliff-corner`, small tower54 at204,86 touches both plateau edges. Its base
is104; the east wall remains at terrain8/top98 and the south wall at terrain8/top68.
PID1092 displayed masonry and both lower doors in rotations0/6/4/2. Read-only
samples confirmed the selected heights98/68, GM10 columns at the seven exposed
footprint tiles, unchanged terrain heights and unchanged other cliff textures.
The native game closed and the desktop was released at12:52:59 CEST, 11 September.

![Masonry beneath the tower, with high and low connections](docs/r023/foundations/rotation-0.png)

![The same tower and masonry after rotation](docs/r023/foundations/rotation-6.png)

In `iv-ai-foundation`, only elevated terrain and an AI construction plan were
prepared. Native AI player2 built tower51 at299,192 and stair6 at300,196, plus
tower28 at307,192 and raised stair1 at308,196. Both tower bases were104. In PID5116,
stair6 had logic0x8100/height8 and supplied the left foundation's ground door;
raised stair1 had logic0x900/height88 and supplied none. Read-only cache samples
confirmed these choices. The game closed and desktop was released at12:56:58.

![AI-built stair6 supplies the left ground door; raised stair supplies none](docs/r023/foundations/ai-stair6.png)

These new native scenes use the small tower and stock textures. Other kinds are
covered by emitted-code tests and the earlier native R023 checks; no claim is
made that every texture pack was launched. The current pack's existing GM10
range supplies the masonry. Multiplayer, Extreme and replay are not certified.

## Cost

Five alternating native benchmark pairs used 1,000 synthetic tower records and
200 rounds. With eligible lower connections, median added cost was 25.594 ns per
tower draw (0.0256 ms per1,000) and191.949 ns per connection refresh (0.1919 ms
per1,000). The same fixture-backing writes ran in both timing arms. This exercises
the new lower-height guard; above-base results were25.109/182.647 ns respectively.
Refresh cadence remains the game's existing40-update schedule, not every frame.

The graphics branch's separate million-call test measured median added5.896 ns
per tower tile refresh and5.830 ns for other-building fallbacks. It runs only
when the existing graphics layer refreshes, with no additional draw work.
These bounded component costs are negligible at the tested scale; they are not
full-game FPS measurements or a guarantee about arbitrary hardware/mod mixes.
