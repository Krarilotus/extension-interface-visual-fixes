# R130 validation

The original placement UI leaves the selected marketplace tool active after its
command commits. Native Castle Builder / A Mighty Oasis reproduces it: building17,
type26, owner1 exists while mapper77 remains selected. Moving the pointer draws a
second preview. An invalid occupied-keep attempt correctly preserves retry.

The patch redirects the existing post-commit minimap notification at SHC0x516a0f
through an87-byte wrapper. It clears only the matching local mapper for marketplace77
or mercenary post/barracks/guilds86..89, only when called by placement execution
0x481f3c. It excludes editor/siege-editor and preserves other callers and tools.
The native category function0x456fd0 establishes these five replacement categories;
storage expands, and keeps already clear in their existing setup path.

The original notification still runs with the same registers, flags, stack and
argument. No command protocol, simulation field, input callback or renderer is
added. Only the existing local selection changes after successful placement.

## Completed checks

- 56 automated tests across R007/R130 pass;36 exercise R130's actual Lua-emitted
  code, all five unique mappers, ordinary/expandable tools, local/remote actors,
  cancellation/different selection, non-command callers, editor exclusions and ABI.
- 14 local original-executable caller-flow cases pass. Terminal simulation calls
  are stubbed: this verifies original eligibility branches and acknowledgement
  stack offsets, not full simulation. Failed eligibility bypasses the wrapper.
- 36 original command-flow cases pass with terminal serialization/simulation
  stubs: schedule-only and resource rejection never enter placement; eligibility
  rejection bypasses acknowledgement; successful local matching unique tools
  clear. Remote actors, changed tools and ordinary building commits retain the
  selection. This is original-code flow evidence, not a live multiplayer test.
- Native emitted-code instrumentation in the isolated SHC1.41 process: invalid
  marketplace placement retains mapper77; valid placement commits building19,
  type26/owner1 and clears mapper0. Moving the pointer draws no stale preview.
  Existing marketplace replacement behavior is retained. Reference executable SHA:
  3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a.
  Developer loader, official UCP3.0.7 code, winProcHandler0.2.0,
  graphicsApiReplacer1.3.0, R007 enabled. Original executable unchanged.
- Baseline repeatable woodcutter and expandable granary remain selected after
  placement. Patched woodcutter repeat placement also passes; patched expandable
  storage remains pending.
- Clean restart loads/enables the actual module successfully with both R007/R130
  options enabled. Installed unique-placement.lua matches the tested source SHA256
  8a04f3950829bb339ef7bbb845d255d09da598b2819adfe2587967e951d8420e.
- The saved Castle Builder fixture reloads successfully. With the actual module,
  mercenary-post mapper86 commits type8/owner1 and clears0. A normal skirmish on
  the original BigD Arena report map starts with native resources; barracks
  mapper87 commits local building39/type9 and clears0, costing15stone.
  AI construction continues independently. The current video setting is1920x1080.
- Follow-up actual-module skirmish: tunnelers mapper89 commits local building45,
  type25 at214,66 and clears0. Engineers mapper88 survives occupied-keep rejection
  with no resource charge, then commits local building47/type24 at205,69 and
  clears0. Both show no second preview when the pointer moves. Native resource
  initialization only; no inventory seed or diagnostic code injection.
- Patched woodcutter mapper51 commits local building28/type3 at198,74, costs3wood
  and remains selected with a visible next preview. Right-click cancellation
  removes that preview (visual observation; sampler ended before cancellation).
- A separate native g.sav preserves both guilds and the woodcutter:880856bytes,
  SHA256bf32e750ea38cfaeae0bd7387fc0b133b9b8e0be06cc53aa2c6aec0dadba378e.
  The prior Castle Builder save is preserved; this new save's reload is pending.
- Native wrapper microbenchmark, five alternating paired runs of two million
  calls per case: marketplace median4.641ns added/call (4.398–5.495), ordinary
  tool median4.556ns (4.056–5.288). The actual emitted wrapper uses a terminal
  notification stub and reproduced stack; this is not whole-game timing.

[Original stale preview](docs/native-market-stale-preview.png) and
[patched native result](docs/native-market-cleared-after.png).

Actual module: [engineers cleared](docs/native-engineers-cleared.png),
[tunnelers cleared](docs/native-tunnelers-cleared.png), and
[ordinary preview retained](docs/native-ordinary-retained.png).

## Remaining acceptance

Patched expandable placement; insufficient resources after selection,
unique-tool cancel/reselect; native delayed
and remote commands. Multiplayer/replay/Extreme compatibility
is not established. Same-type reselect while a command is delayed is treated as
matching the still-selected tool; no selection generation or extra input hook exists.

Package currently14runtime files/6,065compressed bytes, +2,314bytes over R007;
no runtime dependency. One startup allocation87bytes and5changed call-site bytes;
no per-frame work. CI is now activated in .github/workflows/test.yml; its results,
independent review and normal approved merge remain required.
