# Interface and Visual Fixes

Optional fixes for SHC/SHCE 1.41 and UCP 3.0.7, all off by default. The "UCP3 Fixes" plugin turns on the preview, tree, tower door and cliff fixes; "UCP3 Recommended" also turns on the two lobby features. Apply your settings and restart the game.

- Сохраняет описания пользовательских карт видимыми в лобби.
- Убирает предпросмотр после успешной постройки уникального здания.
- Обновляет предпросмотр здания при перемещении камеры.
- Отличает стоящие мёртвые деревья от поваленных стволов.
- Выравнивает двери башен по примыканиям и продолжает каменную кладку под башнями у края обрыва.
- Показывает существующую кнопку загрузки в одиночном лобби.
- Улучшает стыки текстур скал после поворота камеры и на диагональных уступах.
- Rebuild tile object lists so stray flags, stones and arrows stop appearing on the wrong tile.

Передние уступы используют последовательные текстуры; уходящие вглубь — стабильное разнообразие там, где перекрытие мешает непрерывности.

Дверь выбирает самое высокое подходящее примыкание; при равной высоте — ближайшее к центру. Крайние двери сдвигаются внутрь на полклетки. Stair6, построенная ИИ, даёт дверь у земли без стены; приподнятые лестницы не учитываются.

Кладка под башней и двери на высоте примыкающих стен.

![Кладка под башней и двери на высоте примыкающих стен.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/tower-foundation.png)

Стыкующиеся текстуры обрывов после поворота камеры.

![Стыкующиеся текстуры обрывов после поворота камеры.](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/cliff-textures.png)
