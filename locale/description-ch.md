# Interface and Visual Fixes

适用于 SHC/SHCE 1.41 和 UCP 3.0.7 的七项修复，默认全部启用。每项均可单独关闭。应用设置后请重启游戏。

- 保持大厅中的自定义地图描述可见。
- 成功放置唯一建筑后清除建造预览。
- 移动镜头时更新建筑预览。
- 区分尚未倒下的枯树和倒地的树干。
- 使塔门对齐连接处，并将石墙纹理延伸到悬崖边的塔楼下方。
- 在单人大厅中显示原有的载入按钮。
- 改善镜头旋转后及对角阶梯处的悬崖纹理衔接。

朝向镜头的阶梯使用连续纹理；向远处延伸的阶梯在重叠妨碍衔接时使用固定的纹理变化。

塔门优先选择最高的有效连接；高度相同时选择最靠近中间的位置。最外侧的门向内移动半格。AI 建造的 Stair6 无需其他墙体即可提供地面高度的门；抬高的楼梯不算有效连接。

塔楼下方的石墙纹理，以及与连接墙体等高的门。

![塔楼下方的石墙纹理，以及与连接墙体等高的门。](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/tower-foundation.png)

旋转镜头后连续的悬崖纹理。

![旋转镜头后连续的悬崖纹理。](https://raw.githubusercontent.com/Krarilotus/extension-interface-visual-fixes/b666f94ac104c46193af8bb12c8c7c8364fb0fa0/docs/store/cliff-textures.png)
