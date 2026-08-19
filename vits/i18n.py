# -*- coding: utf-8 -*-
"""Minimal i18n. Default Chinese; switchable to English at runtime."""

LANG = 'zh'  # default

STRINGS = {
    'title': {'zh': '静谧田园 存档修改器 v1.3  (Village in the Shade)',
              'en': 'Village in the Shade Save Editor v1.3'},
    'open': {'zh': '打开存档...', 'en': 'Open Save...'},
    'save': {'zh': '保存修改', 'en': 'Save Changes'},
    'money': {'zh': '金钱', 'en': 'Money'},
    'apply': {'zh': '应用', 'en': 'Apply'},
    'tab_inv': {'zh': '背包', 'en': 'Inventory'},
    'tab_npc': {'zh': '村民好感 / 时间', 'en': 'Villagers / Time'},
    'col_slot': {'zh': '格', 'en': 'Slot'},
    'col_id': {'zh': '物品ID', 'en': 'Item ID'},
    'col_name': {'zh': '名称', 'en': 'Name'},
    'col_count': {'zh': '数量', 'en': 'Count'},
    'col_rank': {'zh': '星级', 'en': 'Rank'},
    'edit_slot': {'zh': '编辑选中格子', 'en': 'Edit Selected Slot'},
    'search_item': {'zh': '搜索物品:', 'en': 'Search item:'},
    'count': {'zh': '数量:', 'en': 'Count:'},
    'rank04': {'zh': '星级(0-4):', 'en': 'Rank (0-4):'},
    'apply_slot': {'zh': '应用到格子', 'en': 'Apply to Slot'},
    'empty': {'zh': '(空)', 'en': '(empty)'},
    'not_loaded': {'zh': '(未加载)', 'en': '(not loaded)'},
    'game_time': {'zh': '游戏时间', 'en': 'Game Time'},
    'day_pre': {'zh': '第', 'en': 'Day'},
    'day_post': {'zh': '天', 'en': ''},
    'apply_day': {'zh': '应用天数', 'en': 'Apply Day'},
    'col_npc_id': {'zh': 'ID', 'en': 'ID'},
    'col_npc_name': {'zh': '名字', 'en': 'Name'},
    'col_npc_role': {'zh': '身份', 'en': 'Role'},
    'col_love': {'zh': '好感度/2100', 'en': 'Affection/2100'},
    'col_level': {'zh': '等级', 'en': 'Level'},
    'love_label': {'zh': '好感度 (0-2100, 等级段 100/300/600/1000/1500/2100):',
                   'en': 'Affection (0-2100, tiers 100/300/600/1000/1500/2100):'},
    'apply_npc': {'zh': '应用到选中村民', 'en': 'Apply to Villager'},
    'max_all': {'zh': '全部拉满', 'en': 'Max All'},
    'hint': {'zh': '提示: 修改前请关闭游戏; 首次保存会自动备份 save.001.bak',
             'en': 'Tip: close the game before editing; first save creates save.001.bak backup'},
    'loaded': {'zh': '已加载: {} 个背包格', 'en': 'Loaded: {} inventory slots'},
    'err': {'zh': '错误', 'en': 'Error'},
    'open_fail': {'zh': '打开失败', 'en': 'Failed to open'},
    'save_fail': {'zh': '保存失败', 'en': 'Failed to save'},
    'done': {'zh': '完成', 'en': 'Done'},
    'saved_msg': {'zh': '已写入存档。\n首次修改已自动备份为 save.001.bak\n如出现问题，删除 save.001 并将备份改名恢复即可。',
                  'en': 'Save written.\nFirst edit auto-backed up as save.001.bak\nIf anything breaks, delete save.001 and rename the backup.'},
    'pick_slot': {'zh': '请先在列表中选中一个格子', 'en': 'Select a slot first'},
    'pick_item': {'zh': '空格子请先搜索并选择一个物品', 'en': 'Pick an item for the empty slot first'},
    'notice': {'zh': '提示', 'en': 'Notice'},
    'slot_empty_hint': {'zh': '格 {} 是空的: 搜索并选择物品后点“应用到格子”即可添加',
                        'en': 'Slot {} is empty: search & pick an item, then click "Apply to Slot"'},
    'money_set': {'zh': '金钱已改为 {} (记得点“保存修改”)', 'en': 'Money set to {} (remember to Save Changes)'},
    'slot_set': {'zh': '格 {} 已修改 (记得点“保存修改”)', 'en': 'Slot {} updated (remember to Save Changes)'},
    'love_set': {'zh': 'NPC {} 好感度已修改 (记得点“保存修改”)', 'en': 'NPC {} affection updated (remember to Save Changes)'},
    'love_maxed': {'zh': '全部村民好感度已拉满 2100 (记得点“保存修改”)', 'en': 'All villagers maxed to 2100 (remember to Save Changes)'},
    'day_set': {'zh': '游戏天数已修改 (记得点“保存修改”)', 'en': 'Game day updated (remember to Save Changes)'},
    'time_info': {'zh': '时刻 {:02d}:{:02d} | 按30天/季: {}季第{}天 | 按28天/季: {}季第{}天',
                  'en': 'Time {:02d}:{:02d} | 30d/season: {} day {} | 28d/season: {} day {}'},
    'seasons': {'zh': '春夏秋冬', 'en': ['Spring', 'Summer', 'Autumn', 'Winter']},
    'tab_animal': {'zh': '家畜 / 动物', 'en': 'Animals'},
    'sect_livestock': {'zh': '家畜 (好感 0-2000, 鸡/鸭等小动物上限 1500)',
                       'en': 'Livestock (affection 0-2000, small animals cap 1500)'},
    'sect_creature': {'zh': '野生动物 / 猫咪 (好感 0-12000 = 游戏内 0-120 ×100; 摸=+300, 喂=+400)',
                      'en': 'Wild animals / Cats (0-12000 = in-game 0-120 x100; pet=+300, feed=+400)'},
    'col_animal_no': {'zh': '#', 'en': '#'},
    'col_species': {'zh': '品种', 'en': 'Species'},
    'col_animal_name': {'zh': '名字', 'en': 'Name'},
    'col_animal_love': {'zh': '好感/2000', 'en': 'Affection/2000'},
    'col_mood': {'zh': '心情', 'en': 'Mood'},
    'col_creature': {'zh': '生物', 'en': 'Creature'},
    'col_like': {'zh': '好感/12000', 'en': 'Likeability/12000'},
    'apply_animal': {'zh': '应用到选中家畜', 'en': 'Apply to Animal'},
    'apply_creature': {'zh': '应用到选中生物', 'en': 'Apply to Creature'},
    'max_all_animal': {'zh': '家畜全满', 'en': 'Max All Livestock'},
    'max_all_cat': {'zh': '猫咪全满', 'en': 'Max All Cats'},
    'animal_set': {'zh': '家畜 {} 好感已修改 (记得点“保存修改”)', 'en': 'Animal {} updated (remember to Save Changes)'},
    'creature_set': {'zh': '生物 {} 好感已修改 (记得点“保存修改”)', 'en': 'Creature {} updated (remember to Save Changes)'},
    'animal_maxed': {'zh': '全部家畜好感已拉满 (记得点“保存修改”)', 'en': 'All livestock maxed (remember to Save Changes)'},
    'cat_maxed': {'zh': '全部猫咪好感已拉满 12000 (记得点“保存修改”)', 'en': 'All cats maxed to 12000 (remember to Save Changes)'},
}


def T(key):
    return STRINGS[key][LANG]


def set_lang(lang):
    global LANG
    LANG = lang if lang in ('zh', 'en') else 'zh'


def season_name(idx):
    s = STRINGS['seasons'][LANG]
    return s[idx]
