# Interface and Visual Fixes

Fixes descriptions disappearing from the existing lobby map text area (R007).
The separate **Show Load in skirmish lobby** option (R001) exposes the native
Load icon and permits loading with only the human player. Both options default
to off and require a game restart. The original Load dialog and game-language
tooltip are retained. In single-player, the icon sits to the right of the
skirmish-master portrait, before the Start hand. Multiplayer retains its
original position and eligibility.

See [R001 validation](VALIDATION-R001.md) for tested behavior and remaining gates.

Enable **Show lobby map descriptions** and restart the game. The option defaults
to off. Install the runtime files and `locale` folder in
`ucp/modules/interface-visual-fixes-0.1.0`.

See [validation](VALIDATION-R007.md) for tested behavior and remaining gates.
SHC 1.41 is the declared target. No release is published.

R130, R132, R019 and R023 share this module owner and will arrive in separate PRs.
