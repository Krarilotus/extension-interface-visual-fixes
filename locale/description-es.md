# Interface and Visual Fixes

Optional fixes for SHC/SHCE 1.41 and UCP 3.0.7, all off by default. The "UCP3 Fixes" plugin turns on the preview, tree, tower door and cliff fixes; "UCP3 Recommended" also turns on the two lobby features. Apply your settings and restart the game.

- Mantiene visibles las descripciones de mapas personalizados en la sala.
- Retira la vista previa tras construir correctamente un edificio único.
- Actualiza la vista previa de construcción al mover la cámara.
- Distingue los árboles muertos en pie de los troncos caídos.
- Alinea las puertas con las conexiones y prolonga la mampostería bajo las torres al borde de acantilados.
- Muestra el botón Cargar existente en la sala de un jugador.
- Mejora la continuidad de los acantilados al girar la cámara y en escalones diagonales.
- Rebuild tile object lists so stray flags, stones and arrows stop appearing on the wrong tile.

Los escalones de frente usan texturas consecutivas; los que se alejan mantienen una variación estable donde el solapamiento impide la continuidad.

La puerta elige la conexión válida más alta; en caso de empate, la más central. En los extremos se desplaza media casilla hacia dentro. Stair6 de la IA permite una puerta a nivel del suelo; las escaleras elevadas no cuentan.

Mampostería bajo la torre y puertas a la altura de los muros conectados.

![Mampostería bajo la torre y puertas a la altura de los muros conectados.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/tower-foundation.png)

Texturas de acantilado conectadas tras girar la cámara.

![Texturas de acantilado conectadas tras girar la cámara.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/cliff-textures.png)
