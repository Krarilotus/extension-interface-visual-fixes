# Cliff source extent correction

Related: [issue34](https://github.com/Krarilotus/extension-interface-visual-fixes/issues/34).

The unchanged tester setup reproduced the reported Extreme source-read fault at
RVA `0x547C1` on 20 September 2026 at 17:04. The dump identifies this module's
private converted cliff source, rather than a destination surface or colour map.
It contains 160 rows; the native offset consumer starts at row152 and requests
90 rows. The instruction eventually reaches uncommitted memory. Earlier probes
wrongly excluded draw heights greater than the terrain offset. The captured
image has a 30x167 header and 9,600-byte payload: oversized assets are not required.

The existing cache now stores a cyclic projection over
`[-104, max(sourceRows,416))`. The native offset anchor is160, terrain offset is
0..255, draw height is below255, and face3 subtracts eight source rows. The native
producer's byte-indexed height lookup is the identity mapping in the captured
build; its separate building path sets offset8 without reducing draw height.
Clipping reduces drawn rows but does not make height<=offset a valid invariant.
The allocation covers rows-103..413, preserves every original projected pixel
inside the image, and wraps extension pixels within the actual asset height.
Short and oversized assets use the same path; no vanilla-height cap is added.

Reuse: `cliff-texture-source.lua` retains its two existing UCP-discovered hook
sites, framework assembly/patch APIs, process heap bindings, shared render epoch
and image invalidation. It introduces no new binding, hook, scan, logging loop,
dependency or gameplay write. Warm resolution adds one pointer adjustment.
Only cold conversion fills the extended range. At32 visible images, additional
cached storage is675KiB for160-row strips and195KiB for1,024-row strips.

Validation on the local change:

- The captured-input test fails before the change and passes afterward in both
  original executable consumers. Bounds checks use requested allocation sizes,
  not readable heap-page slack or a neighbouring allocation.
- All1,515 repository tests pass, including1,536 consumer combinations covering
  independent offsets/heights, both consumers, four masks, both zooms, clipping,
  and1/160/320/1,024-row assets. Extended pixels match an independent cyclic oracle.
- The existing native Windows harness passes128 nonempty destination-surface
  comparisons across SHC/Extreme and160/1,024-row textures.
- Seven-run native component medians,1,000 frames and1,000 resolutions/frame:
  SHC160 rows0.07926->0.07966ms; Extreme160 rows0.07572->0.08916ms;
  SHC1,024 rows0.39213->0.41442ms; Extreme1,024 rows0.39312->0.41924ms.
  These include all existing conversion-cache work, are component measurements,
  and do not measure whole-game FPS or prove a universal performance bound.

The actual game crash was captured on0.1.4 with the supplied configuration.
On 20 September the isolated 0.1.4 installation with only this correction loaded
the preserved combat autosave, survived four orientations and both zooms, and
continued through August1211 at the supplied speed1100 and FPS floor5 without
another unhandled exception. The complete AoB-based0.1.5 candidate at source
379109bd5624fd47d5e7b0acc3166ac9fda98539 was then tested in Extreme with the same
save and module configuration, changing only the Interface version and FPS floor
to30. It survived four orientations and both zooms; ProcDump recorded a normal
exit and no unhandled crash dump. This is a bounded retest, not proof that every
reported crash is fixed. See VALIDATION-PERFORMANCE.md for the timing comparison.

Normal Crusader installed all seven features and rendered the existing
iv-cliff-rotation save, but that fixture immediately ended in defeat under this
configuration. Its full rotation acceptance remains incomplete. Additional
language/distribution builds have offline binding/consumer evidence, not new
full-game acceptance in this retest. The separate paused information-marker
fade defect in issue46 remains open and is not corrected by this change.

The production diff retains the existing AoB and decoded-operand bindings;
six complete executable fixtures retain the same69 scan calls and hook sites,
with45 added assembled bytes. Review found no new owner API, hook, private
resolver or duplicated subsystem in this correction. The runtime scanner is
the target framework's existing first-match API; fixture uniqueness must not
be described as arbitrary-build runtime ambiguity detection.

Private reproduction assets/dump/autosave and benchmark receipts stay under
the task investigation directory; this document does not redistribute them.
The already published0.1.5 package has not been replaced. Store publication and
remaining native acceptance are still pending.
