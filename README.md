# 静谧田园 存档修改器 / Village in the Shade Save Editor

[English README](README_EN.md)

图形界面 + 命令行，修改 Steam 版《静谧田园 / ほのぐらしの庭 / Village in the Shade》(AppID 3934250) 的存档：
金钱、背包物品（ID / 数量 / 星级）、村民好感度、游戏天数。内置从游戏数据提取的
2856 条物品数据库（繁中 + 英文名）和 16 位村民资料。

## 好感度机制（逆向自 gamedefine）

- 等级段上限：Lv1=100, Lv2=300, Lv3=600, Lv4=1000, Lv5=1500, Lv6(满)=2100
- 增长：对话 +10 / 完成委托 +30 / 对话选项成功 +30
- 每级触发对应剧情旗标 `GAME_FLAG_<角色>_LOVE_LEVELn`

## 下载

从 [Releases](../../releases) 下载：

- `VitsSaveEditor.exe` — 图形界面版（Windows）
- `vits-cli.exe` — 命令行版（Windows）

Linux / Steam Deck 直接用 Python 运行：`python3 gui.py` 或 `python3 cli.py dump`

## 存档位置

- Windows: `%APPDATA%\Nippon Ichi Software, Inc\Honogurashinoniwa\<SteamID>\save.001`
- Steam Deck (Proton): `~/.local/share/Steam/steamapps/compatdata/3934250/pfx/drive_c/users/steamuser/AppData/Roaming/Nippon Ichi Software, Inc/Honogurashinoniwa/<SteamID>/save.001`

程序会自动查找以上路径。

## 使用

1. **关闭游戏**（建议同时在 Steam 中暂时关闭该游戏的云存档同步）
2. 打开修改器，自动加载（或手动选择）`save.001`
3. 修改金钱 / 选中格子改物品、数量（1–9999）、星级（0–4）
4. 点「保存修改」。首次写入自动备份 `save.001.bak`
5. 出问题恢复：删除 `save.001`，把 `save.001.bak` 改名为 `save.001`

支持空格子直接添加物品（v1.1+，自动分配 uniqueID 并修正存档结构）。

计划中：物品缩略图（游戏图标为 NIS 自研 NLTX 图集格式，尚需逆向像素格式与物品→图集映射）。

## 命令行示例

```
vits-cli dump                          # 查看金钱与背包
vits-cli find 肥料                     # 搜索物品ID (肥料=20010 优质=20020 高级=20030)
vits-cli set-money 999999
vits-cli set-slot 0 --id 20030 --count 99 --rank 4
vits-cli npc                           # 查看村民好感度和游戏时间
vits-cli set-npc 1090 2100             # 修改好感度
vits-cli set-day 76                    # 修改游戏天数(时刻保留)
```

## 存档格式（逆向笔记）

- 外层 `YKCMP_V1` 容器，类型 8 = 原始 LZ4 block，解压后为固定 20 MiB 缓冲
- 内层 `SER` 序列化树：`[类型u8][字段名偏移u32][大小u32][数据]`
  - 类型 0=基本值, 1=数组(+u32计数), 2=对象, 3=map(+u32计数), 4=指针(+u32地址), 5=字符串
  - 字段名偏移指向文件尾部的字符串表
- 背包：`inventoryItemList_`，每格含 `pData_/dataID`（物品ID, u64）、
  `stackCount_/this->value_`（数量, u32）、`rank_`（星级, u32）等
- 金钱：`money_/this->value_`（u64）
- 物品名提取自 `data.dat`（FAFULLFS 归档中的参数表 + 多语言字符串池）

## 免责声明

仅供学习交流。修改存档有风险，请务必备份。与 Nippon Ichi Software 无关。
