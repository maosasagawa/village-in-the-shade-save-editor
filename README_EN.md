# Village in the Shade Save Editor

[中文说明 / Chinese README](README.md)

GUI + CLI save editor for the Steam release of *Village in the Shade /
ほのぐらしの庭 / 静谧田园* (AppID 3934250): money, inventory items
(ID / count / star rank), villager affection, in-game day. Ships with an item
database (2,856 entries, Traditional Chinese + English) and villager data
extracted from the game files. GUI defaults to Chinese — switch to English
via the dropdown in the top-right corner.

## Download

Grab from [Releases](../../releases):

- `VitsSaveEditor.exe` — GUI (Windows)
- `vits-cli.exe` — command line (Windows)

On Linux / Steam Deck run from source: `python3 gui.py` or `python3 cli.py dump`

## Save location

- Windows: `%APPDATA%\Nippon Ichi Software, Inc\Honogurashinoniwa\<SteamID>\save.001`
- Steam Deck (Proton): `~/.local/share/Steam/steamapps/compatdata/3934250/pfx/drive_c/users/steamuser/AppData/Roaming/Nippon Ichi Software, Inc/Honogurashinoniwa/<SteamID>/save.001`

Both are auto-detected.

## Usage

1. **Close the game** (consider temporarily disabling Steam Cloud for it)
2. Open the editor; it auto-loads `save.001` (or pick one manually)
3. Edit money / items (count 1–9999, rank 0–4) / villager affection / game day
4. Click "Save Changes". The first write creates a `save.001.bak` backup
5. To recover: delete `save.001`, rename `save.001.bak` back

Empty slots are supported: pick an item and apply — the editor splices a new
record and fixes up the save structure (fresh uniqueID included).

## Affection mechanics (reverse engineered from gamedefine)

- Tier caps: Lv1=100, Lv2=300, Lv3=600, Lv4=1000, Lv5=1500, Lv6 (max)=2100
- Gains: talk +10 / quest complete +30 / dialogue choice success +30
- Each tier fires a story flag `GAME_FLAG_<ROLE>_LOVE_LEVELn`

## CLI examples

```
vits-cli dump                 # money + inventory
vits-cli find Fertilizer      # item ID search (20010/20020/20030)
vits-cli set-money 999999
vits-cli set-slot 0 --id 20030 --count 99 --rank 4
vits-cli npc                  # villager affection + game time
vits-cli set-npc 1090 2100
vits-cli set-day 76
```

## File format notes

- Outer container `YKCMP_V1`, type 8 = raw LZ4 block, decompresses to a fixed
  20 MiB buffer
- Inner `SER` serialization tree: `[type u8][name-offset u32][size u32][data]`
  with a string table at the tail; types: 0 leaf, 1 array, 2 object, 3 map,
  4 pointer, 5 string
- Inventory: `inventoryItemList_` → `pData_/dataID` (u64), `stackCount_` (u32),
  `rank_` (u32); money: `money_/this->value_` (u64); affection:
  `npcStatusList_/*/loveRate_/this->value_`; clock: `gameTime_/second_`
  (in-game seconds, 1 day = 86400)
- Item/NPC names extracted from `data.dat` (FAFULLFS archive, param tables +
  multilingual string pools)

## Disclaimer

For educational purposes. Editing saves is at your own risk — always keep
backups. Not affiliated with Nippon Ichi Software.
