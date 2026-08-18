# -*- coding: utf-8 -*-
"""NPC database extracted from data.dat (CHARA table + gamedefine)."""

# id: (zh name, ja name, role)
NPCS = {
    1010: ('帷', 'トバリ', '孤兒'),
    1020: ('木助', 'キスケ', '木匠'),
    1030: ('四郎治', 'シロージ', '樵夫'),
    1040: ('林', 'リン', '村長'),
    1050: ('駒子', 'コマコ', '獵人'),
    1060: ('茶梅', 'サザンカ', '雜貨店'),
    1070: ('六角', 'ロッカク', '大叔'),
    1080: ('今野', 'コンノ', '秘書'),
    1090: ('名護', 'ナゴ', '市役所職員'),
    1100: ('洋', 'ヨウ', '幼女'),
    1110: ('裕太', 'ユータ', '青年'),
    1120: ('堇怜', 'スミレ', '少年'),
    1130: ('蓮實', 'ハスミ', '女醫'),
    1140: ('琪娜娜', 'チナナ', '露天商'),
    1150: ('幽靈少女', 'ゴーストガール', '幽靈少女'),
    1160: ('母親', 'マザー', '母親'),
}

# 好感度等级上限 (来自 gamedefine: NPC_LOVE_LEVEL1..6_MAX)
LOVE_LEVEL_MAX = [100, 300, 600, 1000, 1500, 2100]
LOVE_MAX = 2100
# 对话 +10 / 完成委托 +30 / 选项成功 +30 (NPC_LOVE_ADD_*)


def npc_name(nid):
    e = NPCS.get(nid)
    return e[0] if e else f'NPC{nid}'


def love_level(v):
    for i, mx in enumerate(LOVE_LEVEL_MAX, 1):
        if v <= mx:
            return i
    return len(LOVE_LEVEL_MAX)
