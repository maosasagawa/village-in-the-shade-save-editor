# Village in the Shade Save Editor

[中文说明 / Chinese README](README.md)

GUI + CLI save editor for the Steam release of *Village in the Shade /
ほのぐらしの庭 / 静谧田园* (AppID 3934250): money, inventory items
(ID / count / star rank), villager affection, livestock affection, wild
animal / cat likeability, in-game day, and per-save game language by cloning
the selected save into another official slot, including normal/horror-off
mode selection. Ships with an item database
(2,856 entries, Traditional Chinese + English), 16 villagers, 28 livestock
species and 247 creatures extracted from the game files. GUI defaults to
Chinese — switch to English via the dropdown in the top-right corner.

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
2. Open the editor; it reads `save.lst`, lists official saves, selects the first,
   and lets you switch saves from the top dropdown
3. Edit money / items (count 1–9999, rank 0–4) / villager affection / game day
4. Click "Save Changes". The first write creates a `save.001.bak` backup
5. To recover: delete `save.001`, rename `save.001.bak` back

### Save language, mode / copy

The game fixes its language per save. The editor copies the currently selected
save into a target slot, then updates both the target save's language flags and
the `save.lst` preview `languageID`. Japanese, English, French, Spanish,
Traditional Chinese and Korean are available, together with Normal Horror Mode
and Horror-Off Mode.

- Official slot numbers: slot 1=`save.001`, slot 2=`save.006`, slot 3=`save.011`
  (five file numbers are reserved per slot)
- Empty targets are created directly; the GUI asks before replacing occupied slots
- The target save and `save.lst` are backed up before replacement; if `.bak`
  exists, a new timestamped backup is created
- **Fully close the game first**, or the game may overwrite the files on exit
- Mode updates both `GAME_FLAG_HORROR_OFF_MODE` and the list preview
  `isHororOffMode`. Switching a progressed save may repeat/skip story events or
  desync flags; test mode changes only in a copied slot

Empty slots are supported. When splicing a new record the editor fixes up
ancestor container sizes, header offsets, and every t4 pointer's addr field
(addr encodes the object's stream offset; the loader resolves shared pointers
through it, so all addrs past the splice point must be shifted).

## Affection mechanics (reverse engineered from gamedefine / characterpresent.dat / village.exe)

- Tier caps: Lv1=100, Lv2=300, Lv3=600, Lv4=1000, Lv5=1500, Lv6 (max)=2100
- Gains: talk +10 / quest complete +30 / dialogue choice success +30
- Each tier fires a story flag `GAME_FLAG_<ROLE>_LOVE_LEVELn`

### Gifts

| Reaction | Normal day | Birthday |
|----------|-----------|----------|
| Liked gift (4 items per villager) | +25 | +50 |
| Neutral gift | +15 | +30 |
| Disliked gift (4 items per villager) | +5 | +10 |

- Star-rank bonus (liked gifts only): ★1 ×1.1, ★2 ×1.2, ★3 ×1.35, ★4 ×1.5
  (a ★4 liked gift on a birthday = 75 points)
- Limits: 1 gift per villager per day, 2 per week (resets Monday); special
  story items bypass the weekly limit but give no affection (they trigger
  unique events instead)
- Each villager's liked/disliked items and birthday are listed in the
  Chinese README's table (data from `character.dat` / `characterpresent.dat`)

### Livestock & cats

- Livestock (`livestockList_`): affection 0–2000 (small animals such as
  chickens cap at 1500), plus a mood value 0–100
- Wild animals (`creatureLikeabilityList_`): in-game likeability 0–120,
  stored ×100 in the save (0–12000); petting +3, feeding +4 (needs ≥30 to
  feed, ≥60 to pet; 30 per gauge bar)
- 7 cats total: Ginger, White, Black, Mask-and-Mantle, Calico, Fluffy,
  and Coco the pet cat

## CLI examples

```
vits-cli dump                 # money + inventory
vits-cli find Fertilizer      # item ID search (20010/20020/20030)
vits-cli set-money 999999
vits-cli set-slot 0 --id 20030 --count 99 --rank 4
vits-cli npc                  # villager affection + game time
vits-cli set-npc 1090 2100
vits-cli set-day 76
vits-cli animals              # livestock + cat likeability
vits-cli set-animal 0 2000    # livestock by index from `animals`
vits-cli set-cat all 12000    # max all cats (or pass a creature ID)
vits-cli saves                # list official saves indexed by save.lst
vits-cli copy-save 2 jp --horror-off
vits-cli copy-save 3 en --horror-on --replace
```

## File format notes

- Outer container `YKCMP_V1`, type 8 = raw LZ4 block, decompresses to a fixed
  20 MiB buffer
- `save.lst` uses YKCMP type 4 and stores official file numbers, timestamps and
  an ExtraData SER preview containing `languageID`
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

## License

Copyright (C) 2026 maosasagawa

Project-authored source code is licensed under the
[GNU General Public License v3.0 only](LICENSE) (GPL-3.0-only). Game names,
trademarks, and data extracted from game files remain the property of their
respective owners.
