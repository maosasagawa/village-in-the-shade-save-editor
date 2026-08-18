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


def name_of(iid):
    e = ITEMS.get(iid)
    return e[0] if e else f'?{iid}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['dump', 'set-money', 'set-slot', 'find'])
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
