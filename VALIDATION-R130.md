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
- Native emitted-code instrumentation in the isolated SHC1.41 process: invalid
  marketplace placement retains mapper77; valid placement commits building19,
  type26/owner1 and clears mapper0. Moving the pointer draws no stale preview.
  Existing marketplace replacement behavior is retained. Reference executable SHA:
  3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a.
  Developer loader, official UCP3.0.7 code, winProcHandler0.2.0,
  graphicsApiReplacer1.3.0, R007 enabled. Original executable unchanged.
- Baseline repeatable woodcutter and expandable granary remain selected after
  placement. Patched ordinary and other unique native cases are still pending.

[Original stale preview](docs/native-market-stale-preview.png) and
[patched native result](docs/native-market-cleared-after.png).

## Remaining acceptance

Actual module-loader restart; all five unique types; patched ordinary/expandable
placement; insufficient resources, cancel/reselect, save/reload; native delayed
and remote commands; relevant native cost. Multiplayer/replay/Extreme compatibility
is not established. Same-type reselect while a command is delayed is treated as
matching the still-selected tool; no selection generation or extra input hook exists.

Package currently14runtime files/6,065compressed bytes, +2,314bytes over R007;
no runtime dependency. One startup allocation87bytes and5changed call-site bytes;
no per-frame work. CI activation still needs workflow-authorized credentials
(see .ci/test.yml); independent review and normal approved merge remain required.
