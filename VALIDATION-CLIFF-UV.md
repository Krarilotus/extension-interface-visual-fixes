# Cliff texture source correction

Stock and alternative-cliff native acceptance pass. The release candidate is
ready for CI/review and publication; see the Store PR for release status.

## Cause

The earlier rotation-only selector still leaves visible seams. GM9's rock images
are 30x160 raw pixels. The native cliff blitters use columns 0..15 on one face and
14..29 on the other; selecting successive complete images therefore skips part
of the texture pattern on each face. Source strips already contain a vertical
skew, while the native blitters also position column pairs on an isometric slope.
Changing only the image index cannot repair those omitted source coordinates.

The candidate maps a complete source strip onto each 16-column visible face,
mirrors the opposite face, and removes the source skew. Both existing native
blitters retain destination skew, clipping, zoom and vertical repetition. A
rotated x+y phase advances along both adjacent map axes and agrees at their
corner. All 32 rock strips are used; the old clamp duplicated frame 1 instead of
allowing 32. The existing terrain graphics refresh still stores the frame choice.

## Ownership and compatibility

The in-place selector remains 0x4FC95C/93bytes. Source resolution is replaced at
0x453BDB/30bytes and0x45417B/32bytes, inside the two existing blitters. It adds no
draw calls or render pass. Original source pointers and pixels are never changed.
GM9 rock images1..32 must have the native 30x167 header and 9600-byte payload;
other images and incompatible sizes pass through. Waterfalls and GM10 masonry
pixels are not converted. RGB555/565 words are copied without interpreting colour.

render-frame.lua owns the single existing 0x4E8CF0 frame hook, shared with the
tower-door presentation cache. Tower connection refresh is unchanged. The new
strip cache retains a private source copy and projected copy. A visible strip is
compared once per frame, with conversion only when bytes change. Repeated tile
draws read the cached copy; invisible strips do no work. At most 307,200 source bytes
are compared per frame. Byte comparison intentionally supports individual image
replacement, reset, in-place changes and allocator address reuse without taking
ownership of another module's resources or requiring its undocumented internals.

Combined seven-option allocations: 774,030 bytes (149,494 before this correction).
The shared frame entry is allocated once with either feature enabled alone or
both enabled. No state is serialized and no simulation/RNG paths are modified.

## Verification

945 automated tests pass. New emitted-x86 tests cover complete source-strip
coverage, shared corner pixels, both colour-word formats, no repeated source
reads in a frame, image replacement/reset/address reuse, unsupported dimensions,
waterfall pass-through, exact AOB guards and the combined non-overlapping patches.

An MSVC 2005 SP1 native component test runs the original 453B00 and 454080 blitters
with the emitted patch. Its 32 pixel-buffer comparisons cover both blitters, all
four face masks, both zoom levels and top clipping. Patched output matches the
original blitter drawing the corresponding projected synthetic source exactly.

Seven alternating timing pairs each execute 1,000 frames with 1,000 source resolutions
per frame, including verification of all 32 strips. Median added cost is 0.070443 ms
per frame (range 0.069226..0.078328 ms). This isolates source-resolution work, not
full-game FPS or a 1000-speed simulation. Conversion occurs only on changed data.
Private reproduction: R023/run_cliff_uv_benchmark.py and cliff-uv-benchmark/.
Original executable SHA256:3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a.

The isolated native PID 23340 loaded the exact b3c276f candidate with all seven
options, SHC 1.41/UCP 3.0.7, winProcHandler 0.2.0 and graphicsApiReplacer 1.3.0. The
stock cliff-corner fixture passes in all four rotations and Z zoom. Both faces
continue the rock pattern through the corner; tower masonry and lower doors
remain intact. Original stock GM9 stayed byte-identical on disk. Native captures
are native-cliff-uv-stock-{0,6,4,2,zoom}.png; geometry/viewport sampling records
zoom 1/orientation 2. The game closed normally and its process exited before the
desktop was released at 17:00:49.

![Connected stock cliff faces](docs/store/cliff-textures.png)

![Another camera orientation](docs/cliffs/connected-6.png)

A second native session, PID 31712, used the ConqueringEurope cliff resource
with the same seven-option configuration and fixture. Both faces and their
corner pass in all four rotations and both zoom levels. Tower masonry and lower
doors remain intact. This checks the alternative cliff resource, not installation
of the entire texture pack. Its SHA256 is
48b3c6cc38fef1ddbd085f336efeff18c8c9479b9c9c2d266a5800b3ae5622bc.
Native captures are native-cliff-uv-europe-{0,6,4,2,zoom}.png; the viewport record
confirms zoom 1 after the final rotation. The game closed normally, process absence was
verified, and the desktop was released at 17:19:25 on 11 September 2026. The
private installation's stock GM9 was then restored and its original hash verified.

Resource-swap/reset cases above are emitted-x86 tests; they are not a claim of a
native textureSwapper UI session. These measurements do not establish multiplayer,
Extreme or full-game FPS compatibility.
