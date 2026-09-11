# Interface and Visual Fixes

Fixes descriptions disappearing from the existing lobby map text area (R007).
Also clears the selected marketplace, barracks, mercenary post or guild tool
after its successful local placement (R130), preserving retries and ordinary
repeat placement. Enable **Clear unique-building preview after placement** to
use this separate option.

Enable **Show lobby map descriptions** and restart the game. The option defaults
to off. Install the runtime files and `locale` folder in
`ucp/modules/interface-visual-fixes-0.1.0`.

See [validation](VALIDATION-R007.md) for tested behavior and remaining gates.
SHC 1.41 is the declared target. No release is published.

Enable **Show building previews while scrolling** to keep the existing building
ghost visible during camera movement (R132). Placement uses the same native
coordinates and command path. See [camera preview validation](VALIDATION-R132.md).

R019 and R023 share this module owner and will arrive in separate PRs.
