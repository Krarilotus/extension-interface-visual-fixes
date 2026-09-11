# Tower doors: native examples

Each side chooses its highest eligible connection. The connection nearest the centre breaks ties at that height. Doors follow the actual connection height and move along the face. At the extreme tiles, a doorway sits halfway between the outermost two tile positions, for4x4,5x5 and6x6 towers.

![Five-wide tower: half-tile inset at the outer connection](anchor-five.png)

![Round tower: doorway at the wall contact](anchor-round.png)

Cliff-edge towers extend their existing wall masonry down the exposed face. Lower walls can supply doors in that masonry; bare terrain cannot.

![Lower walls meet doors in the tower masonry](../store/tower-foundation.png)

AI-built stair6 alone supplies a ground doorway. Raised stair1-5 are excluded, even when no other wall is present. In this native AI fixture, the left tower has stair6 and a ground doorway; the right tower has raised stair1 and no doorway.

![AI stair6 and raised-stair comparison](foundations/ai-stair6-current.png)

[Current anchor, ordering, native tests and cost](../../VALIDATION-DOOR-DRAW-ORDER.md). Earlier screenshots in this directory are historical evidence, not the current alignment acceptance.
