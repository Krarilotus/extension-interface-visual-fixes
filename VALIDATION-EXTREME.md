# Extreme executable compatibility

Source, emitted-code, native component and targeted Extreme acceptance checks pass.

Regular Crusader1.41 and Extreme1.41 retain the same relevant instruction/stack layouts, but their code addresses and global data locations differ. native-layout.lua selects83 named address pairs once through the existing data.version.isExtreme API. Its fifteen distinct signature variants retain the original fail-closed checks. Existing input, rendering and update hooks keep one owner.

Reference SHA256 values:
- SHC:3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a
- SHCE:55648e6b05d67d37a5773fe699bbb17a2d6ad4de1bb9dbded9a21caef82bd7fb

A private audit ran all seven actual Lua emitters against each complete executable. All24 signature scans and21 patch sites pass without overlap on both. The regular-game emitted bytes, allocation sizes and order are identical to0.1.2 (774,030bytes). Named assembly operands are expanded before invoking the existing assembler. No per-frame edition checks or extra hooks were added.

Regression tests additionally execute the Extreme placement acknowledgement, camera preview input matrix and dead-tree rendering cases. These preserve native registers/flags and validate successful placement, failed/cancelled/remote/editor cases, camera drag/release behavior and tree lifecycle state. Existing regular-game regressions remain in place. The original native game binaries and extracted instruction traces stay private.

Private reproduction and exact instruction witnesses: Roadmap/Investigations/Interface-Visual/extreme/{match_layouts.py,match_data.py,audit_emission.py,layout-candidates.json,data-candidates.json,pattern-proofs.json,regular-emission.json,extreme-emission.json}.

Taller custom strips and defaults-on0.1.3 are separate follow-ups; their runtime was integrated for native release acceptance.

Native startup caught FASM OUT_OF_MEMORY (-2): passing all 83 constants into every assembly exhausted UCP 3.0.7's 64,000-byte assembler workspace. The layout helper now expands referenced named operands before calling the existing assembler. This preserves the exact emitted bytes and removes the constant declarations. Tests constrain CLI FASM to 64 KiB; all 116 assemblies across both editions and the taller-strip candidate pass. The integrated runtime subsequently passed the actual embedded assembler and started with all seven fixes enabled.

Native acceptance (2026-09-11): the cliff-corner save loads, displays masonry-backed lower wall doors, and renders connected cliff faces through all four rotations and zoom. In Extreme PID24924, selecting the tunnelers guild sets mapper89; successful native placement creates active building28 (kind25, owner1, coordinates201/53), deducts100 gold and clears mapper to0. Rejected placement in the previous run retained mapper89. The AI then builds both prepared towers and stairs: stair6 at300/196 has logic0x8100 and height/terrain8, displaying the left tower's ground door; stair1 at308/196 has logic0x900 and height88/terrain8 and adds no door to the right tower. Orientation is confirmed0. Evidence: extreme/native-placement-{ready,click1}.json, native-placement-success.png, native-ai-built.json and native-ai-stair6-success.png. The game exited normally and the desktop was released at19:08:08. Stock GM9 remains restored. Exact unpublished artwork and multiplayer sessions are not claimed tested.

The original Extreme tower parent and connection-refresh functions also pass 32 cold/warm coordinate checks spanning all four tower kinds and four rotations. Seven native alternating runs with 1,000 synthetic records show median added warm draw cost of 24.407 ns/tower and connection refresh cost of 174.621 ns/tower. Sprite output is intercepted for coordinate validation, so these component timings do not represent full-game FPS. Private reproduction: extreme/run_extreme_tower_benchmark.py.
