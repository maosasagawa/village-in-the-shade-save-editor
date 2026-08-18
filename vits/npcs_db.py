# -*- coding: utf-8 -*-
"""NPC database extracted from data.dat (CHARA table + gamedefine)."""

# id: (zh name, en name, zh role, en role)
NPCS = {
    1010: ('帷', 'Tobari', '孤兒', 'Orphan'),
    1020: ('木助', 'Kisuke', '木匠', 'Carpenter'),
    1030: ('四郎治', 'Shiroji', '樵夫', 'Lumberjack'),
    1040: ('林', 'Rin', '村長', 'Village Head'),
    1050: ('駒子', 'Komako', '獵人', 'Hunter'),
    1060: ('茶梅', 'Sazanka', '雜貨店', 'General Store'),
    1070: ('六角', 'Rokkaku', '大叔', 'Old Man'),
    1080: ('今野', 'Konno', '秘書', 'Secretary'),
    1090: ('名護', 'Nago', '市役所職員', 'City Hall Staff'),
    1100: ('洋', 'Yoh', '幼女', 'Girl'),
    1110: ('裕太', 'Yuta', '青年', 'Young Man'),
    1120: ('堇怜', 'Sumire', '少年', 'Boy'),
    1130: ('蓮實', 'Hasumi', '女醫', 'Doctor'),
    1140: ('琪娜娜', 'Chinana', '露天商', 'Street Vendor'),
    1150: ('幽靈少女', 'Ghost Girl', '幽靈少女', 'Ghost Girl'),
    1160: ('母親', 'Mother', '母親', 'Mother'),
}

# 好感度等级上限 (gamedefine: NPC_LOVE_LEVEL1..6_MAX)
LOVE_LEVEL_MAX = [100, 300, 600, 1000, 1500, 2100]
LOVE_MAX = 2100
# 对话 +10 / 完成委托 +30 / 选项成功 +30 (NPC_LOVE_ADD_*)


def npc_name(nid, lang='zh'):
    e = NPCS.get(nid)
    if not e:
        return f'NPC{nid}'
    return e[0] if lang == 'zh' else e[1]


def love_level(v):
    for i, mx in enumerate(LOVE_LEVEL_MAX, 1):
        if v <= mx:
            return i
    return len(LOVE_LEVEL_MAX)
