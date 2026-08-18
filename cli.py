#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静谧田园 存档修改器 - 命令行版
用法:
  python cli.py dump [--save PATH]
  python cli.py set-money 999999
  python cli.py set-slot 0 --count 99 --rank 4 --id 20030
  python cli.py find 肥料            # 搜索物品ID
"""
import argparse, sys

from vits.savedata import SaveData, find_saves
from vits.items_db import ITEMS
from vits.npcs_db import npc_name, love_level, LOVE_LEVEL_MAX


def name_of(iid):
    e = ITEMS.get(iid)
    return e[0] if e else f'?{iid}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['dump', 'set-money', 'set-slot', 'find', 'npc', 'set-npc', 'set-day'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--save')
    ap.add_argument('--count', type=int)
    ap.add_argument('--rank', type=int)
    ap.add_argument('--id', type=int)
    a = ap.parse_args()

    if a.cmd == 'find':
        q = a.args[0] if a.args else ''
        for iid, (zh, en) in ITEMS.items():
            if q in zh or q.lower() in en.lower() or q == str(iid):
                print(f'{iid}\t{zh}\t{en}')
        return

    path = a.save or (find_saves() or [None])[0]
    if not path:
        sys.exit('找不到存档，请用 --save 指定')
    sd = SaveData(path)
    print(f'存档: {path}')

    if a.cmd == 'npc':
        sec = sd.game_seconds['value']
        day = sec // 86400
        print(f'游戏时间: 第{day}天 {sec%86400//3600:02d}:{sec%86400%3600//60:02d}'
              f'  (季节: 按30天/季={"春夏秋冬"[day//30%4]}第{day%30+1}天, 按28天/季={"春夏秋冬"[day//28%4]}第{day%28+1}天)')
        print(f'好感度等级段: {LOVE_LEVEL_MAX} (对话+10/委托+30/选项+30)')
        for did, lv in sd.npcs:
            v = lv['value']
            print(f'  {did}  {npc_name(did):6s}  {v:>5} / 2100  Lv{love_level(v)}')
        return
    if a.cmd == 'set-npc':
        nid, val = int(a.args[0]), int(a.args[1])
        sd.set_npc_love(nid, val)
        print(f'NPC {nid} ({npc_name(nid)}) 好感度 -> {val}')
        sd.write(); print('已保存'); return
    if a.cmd == 'set-day':
        sd.set_game_day(int(a.args[0]))
        print(f'游戏日 -> 第{a.args[0]}天 (时刻保留)')
        sd.write(); print('已保存'); return
    if a.cmd == 'dump':
        print(f'金钱: {sd.money}\n')
        print(f'{"格":>3} {"物品ID":>8} {"数量":>5} {"星级":>3}  名称')
        for s in sd.slots:
            if s.empty:
                print(f'{s.index:>3}  (空)')
            else:
                print(f'{s.index:>3} {s.item_id:>8} {s.count:>5} {s.rank:>3}  {name_of(s.item_id)}')
        return
    if a.cmd == 'set-money':
        sd.money = int(a.args[0])
        print(f'金钱 -> {sd.money}')
    elif a.cmd == 'set-slot':
        idx = int(a.args[0])
        slot = next((s for s in sd.slots if s.index == idx), None)
        if slot is None:
            sys.exit(f'没有第 {idx} 格')
        if slot.empty:
            if a.id is None:
                sys.exit('空格子需要用 --id 指定物品')
            slot = sd.fill_slot(idx, a.id, a.count or 1, a.rank or 0)
            print(f'空格 {idx} 已填入 {a.id}({name_of(a.id)})')
        else:
            sd.set_slot(slot, item_id=a.id, count=a.count, rank=a.rank)
        print(f'格 {idx} -> id={slot.item_id}({name_of(slot.item_id)}) '
              f'count={slot.count} rank={slot.rank}')
    sd.write()
    print('已保存 (首次修改自动备份 .bak)')


if __name__ == '__main__':
    main()
