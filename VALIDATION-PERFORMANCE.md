# High-speed combat comparison, 20 September 2026

The supplied configuration uses timeprovider0.1.0, limiterType=fixedFpsFloor,
minFramesPerSecond=5 and speed1100. Its fixed-floor implementation budgets
simulation time against 1,000,000 / minFramesPerSecond microseconds. Under load,
that configuration permits roughly200ms between game frames.

Thirty-second samples in the isolated Extreme installation:

| Build | Existing FPS floor | Seven fixes | Game frames/s | Median interval ms | 95th percentile ms |
| --- | ---: | --- | ---: | ---: | ---: |
| 0.1.4 plus cliff correction | 5 | On | 4.967 | 199.626 | 205.132 |
| 0.1.4 plus cliff correction | 5 | Off | 4.967 | 199.925 | 209.218 |
| 0.1.4 plus cliff correction | 60 | On | 48.765 | 19.741 | 24.284 |
| 0.1.4 plus cliff correction | 60 | Off | 49.466 | 19.391 | 23.904 |
| Full AoB0.1.5 candidate379109b | 30 | On | 29.799 | 32.995 | 37.773 |
| Full AoB0.1.5 candidate379109b | 30 | Off | 29.632 | 33.192 | 38.253 |

Each pair reloads the same preserved combat save, uses orientation4,
camera[150,20], zoom1, speed1100, and preserves the other modules, AI and textures.
Off disables all seven options; the module remains loaded but installs none of
its patches. The disabled render entry was verified unpatched. The initial off5
sample with a different zoom was excluded and replaced with the matching sample.

Measurements poll the existing native game-loop stopwatch read-only and convert
the installed timeprovider's microsecond timestamps. Enabled render-epoch counts
agree with observed loop counts to within one frame. These are game-loop frame
intervals, not display/Present timings. No injected counters or production
profiling hooks were added. The sampled per-loop simulation counters are not a
reliable throughput total: a later loop can reset/update them before polling.

Disabling these fixes did not remove the severe five-frame-per-second stutter.
Raising the existing FPS floor improved drawing cadence. It also reserves more
time for drawing, reducing achievable simulation throughput at extreme requested
speeds; this is a scheduling tradeoff, not free extra CPU capacity.

The small enabled/disabled differences do not establish a meaningful regression
or a universal zero-overhead guarantee. These are bounded, single-run samples;
combat evolves during measurement, load-to-sample delays are not cycle-exact,
and background system noise is uncontrolled. The candidate on30 run had one
101ms outlier, so it must not be described as eliminating every hitch.

No feature was removed based on these results. A floor30 test profile preserves
all seven fixes and gives a practical smoother cadence in this tested battle.
This belongs to the existing timeprovider setting, not a duplicate setting or
timing hook inside Interface and Visual Fixes. Original supplied configuration
and signed packages remain preserved. The new cliff correction's separate
native component benchmark is recorded in VALIDATION-CLIFF-BOUNDS.md.
