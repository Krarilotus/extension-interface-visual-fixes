# Tower doors: native examples

The foreground square tower is the subject of the first two images. Each side
chooses its highest connected wall, then the nearest connection to that side's
centre among walls of that height. Doorways move along the face and vertically.

Two high walls and one low wall connect to the same side. The nearer high wall
at300,252 wins over the high wall at298,252 and the low wall at299,252.

![Door at the nearer of the two high connections](nearer-high.png)

After removing the selected high wall, the doorway follows the remaining high
wall at298,252. The nearer low wall does not take priority. The camera moved
between captures; compare the doorway with the connecting wall on the tower.

![Door follows the remaining off-centre high connection](farther-high.png)

The smaller tower demonstrates independent sides: its high and low connections
retain different doorway heights after loading another save.

The high connection at the outermost east tile places its doorway half a tile
inward. The low connection on the south side keeps its own height.

![Outermost high connection inset from the tower corner](review-edge.png)

A single stair6 connection supplies a doorway at ground level. Raised stair1–5
are excluded, even when no other wall is present.

![Ground-level doorway supplied by stair6 alone](review-stair6.png)

![Raised stair connection without a false doorway](review-stairs.png)

A low wall below the tower's terrain base does not create a doorway in the cliff.
The cliff appearance itself is unchanged by the door option.

![No doorway in the cliff beneath the tower](review-cliff.png)

Captured in the native SHC1.41 game with the extension enabled. These are existing
game sprites; no explanatory overlays or new game panels are added. The last
four images use isolated, controlled saves: the edge case retains naturally
placed geometry, while the stair/cliff cases set the documented native tile
values offline. They verify rendering, not placement or navigation changes.
