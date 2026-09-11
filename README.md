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

Enable **Distinguish dead tree stages** to show the existing standing-dead tree
art before the fallen-log stage (R019). This changes drawing only; tree lifetime
and save data stay unchanged. See [tree validation](VALIDATION-R019.md).

Enable **Align tower doors with connecting walls** to move each existing stone-tower
doorway to its highest connected wall (R023). Selection is independent for each
side. If several walls are equally high, the connection nearest that side's
centre wins; an exact tie uses the first connection in the game's fixed boundary
order. The door moves along the tower face as well as vertically. Thus a higher,
off-centre wall takes priority over a lower, centred wall. Removing the selected
wall makes the door follow the next qualifying connection on the game's existing
connection refresh. See [door validation](VALIDATION-R023.md).

Enable **Show Load in skirmish lobby** to expose the original single-player Load
control between the portrait and Start, including a lobby without AI opponents.
See [Load validation](VALIDATION-R001.md).
