# Extreme executable compatibility

Draft acceptance: source and emitted-code checks pass; native Extreme testing is pending.

Regular Crusader1.41 and Extreme1.41 retain the same relevant instruction/stack layouts, but their code addresses and global data locations differ. native-layout.lua selects83 named address pairs once through the existing data.version.isExtreme API. Its fifteen distinct signature variants retain the original fail-closed checks. Existing input, rendering and update hooks keep one owner.

Reference SHA256 values:
- SHC:3bb0a8c1e72331b3a30a5aa93ed94beca0081b476b04c1960e26d5b45387ac5a
- SHCE:55648e6b05d67d37a5773fe699bbb17a2d6ad4de1bb9dbded9a21caef82bd7fb

A private audit ran all seven actual Lua emitters against each complete executable. All24 signature scans and21 patch sites pass without overlap on both. The regular-game emitted bytes, allocation sizes and order are identical to0.1.2 (774,030bytes). Named assembly operands use the existing core assembler mapping API. No per-frame edition checks or extra hooks were added.

Regression tests additionally execute the Extreme placement acknowledgement, camera preview input matrix and dead-tree rendering cases. These preserve native registers/flags and validate successful placement, failed/cancelled/remote/editor cases, camera drag/release behavior and tree lifecycle state. Existing regular-game regressions remain in place. The original native game binaries and extracted instruction traces stay private.

Private reproduction and exact instruction witnesses: Roadmap/Investigations/Interface-Visual/extreme/{match_layouts.py,match_data.py,audit_emission.py,layout-candidates.json,data-candidates.json,pattern-proofs.json,regular-emission.json,extreme-emission.json}.

Remaining: native Extreme all-seven startup and targeted feature acceptance, tower/blitter original-call checks, final CI/review. Taller custom strips and defaults-on0.1.3 are separate follow-ups; neither is claimed by this compatibility change.

Native startup caught FASM OUT_OF_MEMORY (-2): passing all 83 constants into every assembly exhausted UCP 3.0.7's 64,000-byte assembler workspace. The layout helper now expands referenced named operands before calling the existing assembler. This preserves the exact emitted bytes and removes the constant declarations. Tests constrain CLI FASM to 64 KiB; all 116 assemblies across both editions and the taller-strip candidate pass. Native retry remains required because CLI and embedded FASM are distinct paths.
