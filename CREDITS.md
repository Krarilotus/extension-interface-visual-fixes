# Credits

## Ghost Objects

The Ghost Objects fix (`ghost-objects.lua`, option `interface-visual-fixes.ghost-objects`)
is based on [Ghost Objects Fix](https://github.com/Monsterfisch/GhostObjectsFix) by
**Monsterfish**: the diagnosis of the tangled per-tile object lists, the rebuild routine,
the entity signatures and layout checks, and the original translations. The reviewed
version merged here is `Krarilotus/GhostObjectsFix@489d388`
(Monsterfisch/GhostObjectsFix#1).

Licence of this part: relicensed by the author under GPL-3.0 for inclusion; consent relayed by Krarilotus on 2026-11-22.

Changes for Interface and Visual Fixes: the signatures, layout checks and the check that
refuses an already changed entity update live with the module's other bindings in
`native-layout.lua`; the uniqueness check is limited to the game's code section; the
rebuild schedule follows the game's own saved tick cycle instead of a countdown reset
through a Map Extensions save section; the option is off by default.
