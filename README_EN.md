# Village in the Shade Save Editor

[中文说明 / Chinese README](README.md)

GUI + CLI save editor for the Steam release of *Village in the Shade /
ほのぐらしの庭 / 静谧田园* (AppID 3934250): money, inventory items
(ID / count / star rank), villager affection, livestock affection, wild
animal / cat likeability, in-game day. Ships with an item database
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
2. Open the editor; it auto-loads `save.001` (or pick one manually)
3. Edit money / items (count 1–9999, rank 0–4) / villager affection / game day
4. Click "Save Changes". The first write creates a `save.001.bak` backup
5. To recover: delete `save.001`, rename `save.001.bak` back

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
