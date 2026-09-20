# Redundancy audit

Related: [issue43](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/43).
This cleanup is separate from the unresolved [crash investigation](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/34).

The test harness now loads UCP 3.0.7's actual `core.lua` and `utils.lua` at revision
`77c6accf14a55fb95434fe6ffd96516e005568b5`. Their `compile`, `callTo`, `jmpTo`,
`assemble`, `allocateAssembly` and memory wrappers replace Python copies of
flattening, relative branches, symbol-prefix formatting and two-pass assembly.
Only native memory/FASM boundaries and independent fixture scan oracles are
substituted. Hash verification and Lua 5.4 keep this aligned with the target;
the framework's `dll/Directory.Build.props` specifies Lua 5.4.6.

Five repeated enable/disable tests, one cliff-disabled test and the lobby's mock
composition test are replaced by one parameterized startup test covering every
option missing, false and true, including required module names and idempotence.
The full seven-feature native composition test remains. The layout arithmetic
test now checks coordinates read from actual emitted lobby code. The obsolete
version-not-equal-to-0.1.0 check is removed; it could not protect later releases.
ABI, bounds, rotation, oversized/replaced textures, placement and localization
cases remain. Immutable tower/cliff instruction fixtures are cached per input;
each emulated case still creates its own memory, registers and runtime caches.

There are no declared extension dependencies to remove. All four Python test
dependencies are used: pytest for cases, Lupa for Lua execution, Unicorn for x86
execution and memory/register checks, PyYAML for manifests/localization. FASM
assembles native wrappers; Node runs the pinned GUI's real localization resolver.
None becomes a new player dependency. Research tools, tests, screenshots and
historical acceptance records are excluded by the explicit package manifest;
deleting them would not reduce the installed module.

The [native integration inventory](native-integration-audit.md) records existing
framework, Legacy, UI, graphics and resource owners. Runtime already uses UCP's
cached AOB scanning, allocation, assembler mappings, patch writing and logger.
Operand/relative-target reads use `core.readInteger`, as Legacy does. Replacing
those short reads with `utils.AOBExtract` parsing would not remove a private
scanner or allocator: neither exists. The shared render epoch and the separate
connection/depth/image caches have different invalidation responsibilities;
removing them would lose update, occlusion or texture-replacement behavior.
No new owner API, hook or runtime dependency is introduced by this audit.

Validation: 1,501 offline tests pass and the 32-file package builds. This first
cleanup changes no packaged files and is not a new native gameplay or crash test.
