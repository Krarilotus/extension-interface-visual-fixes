# Interface and Visual Fixes

Optional fixes for SHC/SHCE 1.41 and UCP 3.0.7, all off by default. The "UCP3 Fixes" plugin turns on the preview, tree, tower door and cliff fixes; "UCP3 Recommended" also turns on the two lobby features. Apply your settings and restart the game.

- Keep custom map descriptions visible in the lobby.
- Clear the building preview after successfully placing a unique building.
- Update building previews while scrolling the camera.
- Show distinct standing-dead trees before fallen logs.
- Align tower doors with connections and extend wall masonry beneath cliff-edge towers.
- Show the existing Load button in the single-player lobby.
- Improve cliff continuity after rotation and on diagonal steps.

Front-facing steps use consecutive strips; receding steps use stable variation where overlap prevents continuity.

Tower doors choose the highest eligible connection; nearest centre breaks ties. Outer doors move half a tile inward. AI stair6 alone allows a ground door; raised stairs do not count.

Tower masonry with doors at the connecting wall heights.

![Tower masonry with doors at the connecting wall heights.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/tower-foundation.png)

Connected cliff textures after rotation.

![Connected cliff textures after rotation.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/cliff-textures.png)
