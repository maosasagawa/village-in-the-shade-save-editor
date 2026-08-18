#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静谧田园 (Village in the Shade) 存档修改器 GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from vits.savedata import SaveData, find_saves
from vits.items_db import ITEMS
from vits.npcs_db import NPCS, npc_name, love_level

RANK_NAMES = {0: '无/铜', 1: '1', 2: '2', 3: '3', 4: '4'}


def item_name(iid):
    e = ITEMS.get(iid)
    return e[0] if e else f'未知物品 {iid}'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('静谧田园 存档修改器 v1.2  (Village in the Shade)')
        self.geometry('860x600')
        self.save = None
        self._build()
        self._autoload()

    def _build(self):
        top = ttk.Frame(self); top.pack(fill='x', padx=8, pady=6)
        ttk.Button(top, text='打开存档...', command=self.open_save).pack(side='left')
        self.save_combo = ttk.Combobox(top, width=52, state='readonly')
        self.save_combo.pack(side='left', padx=6)
        self.save_combo.bind('<<ComboboxSelected>>',
                             lambda e: self.load(self.save_combo.get()))
        self.path_var = tk.StringVar(value='(未加载)')
        ttk.Button(top, text='保存修改', command=self.write_save).pack(side='right')

        mf = ttk.LabelFrame(self, text='金钱'); mf.pack(fill='x', padx=8, pady=4)
        self.money_var = tk.StringVar()
        ttk.Entry(mf, textvariable=self.money_var, width=14).pack(side='left', padx=6, pady=4)
        ttk.Button(mf, text='应用', command=self.apply_money).pack(side='left')

        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True, padx=8, pady=4)
        body = ttk.Frame(nb); nb.add(body, text='背包')
        npctab = ttk.Frame(nb); nb.add(npctab, text='村民好感 / 时间')
        self._build_npc_tab(npctab)
        cols = ('slot', 'id', 'name', 'count', 'rank')
        self.tree = ttk.Treeview(body, columns=cols, show='headings', selectmode='browse')
        for c, w, t in (('slot', 50, '格'), ('id', 90, '物品ID'), ('name', 320, '名称'),
                        ('count', 70, '数量'), ('rank', 60, '星级')):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor='w')
        vsb = ttk.Scrollbar(body, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='left', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        ef = ttk.LabelFrame(self, text='编辑选中格子'); ef.pack(fill='x', padx=8, pady=6)
        ttk.Label(ef, text='搜索物品:').grid(row=0, column=0, padx=4, pady=4, sticky='e')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        ttk.Entry(ef, textvariable=self.search_var, width=24).grid(row=0, column=1, padx=4)
        self.item_combo = ttk.Combobox(ef, width=44, state='readonly')
        self.item_combo.grid(row=0, column=2, padx=4, columnspan=3, sticky='w')
        ttk.Label(ef, text='数量:').grid(row=1, column=0, padx=4, sticky='e')
        self.count_var = tk.StringVar()
        ttk.Spinbox(ef, from_=1, to=9999, textvariable=self.count_var, width=8).grid(row=1, column=1, sticky='w', padx=4)
        ttk.Label(ef, text='星级(0-4):').grid(row=1, column=2, padx=4, sticky='e')
        self.rank_var = tk.StringVar()
        ttk.Spinbox(ef, from_=0, to=4, textvariable=self.rank_var, width=6).grid(row=1, column=3, sticky='w', padx=4)
        ttk.Button(ef, text='应用到格子', command=self.apply_slot).grid(row=1, column=4, padx=10)
        self._refresh_combo('')

        self.status = tk.StringVar(value='提示: 修改前请关闭游戏; 首次保存会自动备份 save.001.bak')
        ttk.Label(self, textvariable=self.status, foreground='#666').pack(fill='x', padx=8, pady=4)

    def _build_npc_tab(self, tab):
        tf = ttk.LabelFrame(tab, text='游戏时间'); tf.pack(fill='x', padx=4, pady=4)
        self.day_var = tk.StringVar()
        ttk.Label(tf, text='第').pack(side='left', padx=(8,2))
        ttk.Entry(tf, textvariable=self.day_var, width=6).pack(side='left')
        ttk.Label(tf, text='天').pack(side='left', padx=2)
        self.time_info = tk.StringVar()
        ttk.Label(tf, textvariable=self.time_info, foreground='#666').pack(side='left', padx=10)
        ttk.Button(tf, text='应用天数', command=self.apply_day).pack(side='right', padx=8)

        nf = ttk.Frame(tab); nf.pack(fill='both', expand=True, padx=4, pady=4)
        cols = ('id', 'name', 'role', 'love', 'level')
        self.npc_tree = ttk.Treeview(nf, columns=cols, show='headings', selectmode='browse')
        for c, w, t in (('id', 60, 'ID'), ('name', 120, '名字'), ('role', 120, '身份'),
                        ('love', 110, '好感度/2100'), ('level', 60, '等级')):
            self.npc_tree.heading(c, text=t)
            self.npc_tree.column(c, width=w, anchor='w')
        vsb = ttk.Scrollbar(nf, orient='vertical', command=self.npc_tree.yview)
        self.npc_tree.configure(yscrollcommand=vsb.set)
        self.npc_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='left', fill='y')
        ef = ttk.Frame(tab); ef.pack(fill='x', padx=4, pady=4)
        ttk.Label(ef, text='好感度 (0-2100, 等级段 100/300/600/1000/1500/2100):').pack(side='left', padx=4)
        self.love_var = tk.StringVar()
        ttk.Spinbox(ef, from_=0, to=2100, textvariable=self.love_var, width=8).pack(side='left', padx=4)
        ttk.Button(ef, text='应用到选中村民', command=self.apply_love).pack(side='left', padx=8)
        ttk.Button(ef, text='全部拉满', command=self.max_all_love).pack(side='left', padx=8)
        self.npc_tree.bind('<<TreeviewSelect>>', self.on_npc_select)

    def refresh_npcs(self):
        if not self.save:
            return
        self.npc_tree.delete(*self.npc_tree.get_children())
        for did, lv in self.save.npcs:
            info = NPCS.get(did, ('?', '?', '?'))
            v = lv['value']
            self.npc_tree.insert('', 'end', iid=str(did),
                                 values=(did, info[0], info[2], v, f'Lv{love_level(v)}'))
        sec = self.save.game_seconds['value']
        day = sec // 86400
        self.day_var.set(str(day))
        self.time_info.set(f'时刻 {sec%86400//3600:02d}:{sec%86400%3600//60:02d} | '
                           f'按30天/季: {"春夏秋冬"[day//30%4]}季第{day%30+1}天 | '
                           f'按28天/季: {"春夏秋冬"[day//28%4]}季第{day%28+1}天')

    def on_npc_select(self, _ev=None):
        sel = self.npc_tree.selection()
        if sel and self.save:
            for did, lv in self.save.npcs:
                if str(did) == sel[0]:
                    self.love_var.set(str(lv['value']))

    def apply_love(self):
        sel = self.npc_tree.selection()
        if not sel or not self.save:
            return
        try:
            self.save.set_npc_love(int(sel[0]), int(self.love_var.get()))
        except Exception as e:
            messagebox.showerror('错误', str(e)); return
        self.refresh_npcs()
        self.status.set(f'NPC {sel[0]} 好感度已修改 (记得点“保存修改”)')

    def max_all_love(self):
        if not self.save:
            return
        for did, _lv in self.save.npcs:
            self.save.set_npc_love(did, 2100)
        self.refresh_npcs()
        self.status.set('全部村民好感度已拉满 2100 (记得点“保存修改”)')

    def apply_day(self):
        if not self.save:
            return
        try:
            self.save.set_game_day(int(self.day_var.get()))
        except Exception as e:
            messagebox.showerror('错误', str(e)); return
        self.refresh_npcs()
        self.status.set('游戏天数已修改 (记得点“保存修改”)')

    # ---- data ----
    def _autoload(self):
        saves = find_saves()
        self.save_combo['values'] = saves
        if saves:
            self.save_combo.set(saves[0])
            self.load(saves[0])

    def open_save(self):
        init = os.path.dirname(find_saves()[0]) if find_saves() else os.path.expanduser('~')
        p = filedialog.askopenfilename(initialdir=init, title='选择 save.001',
                                       filetypes=[('存档', 'save.*'), ('所有文件', '*')])
        if p:
            self.load(p)

    def load(self, path):
        try:
            self.save = SaveData(path)
        except Exception as e:
            messagebox.showerror('打开失败', str(e))
            return
        self.path_var.set(path)
        self.money_var.set(str(self.save.money))
        self.refresh_tree()
        self.refresh_npcs()
        self.status.set(f'已加载: {len(self.save.slots)} 个背包格')

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.save.slots:
            if s.empty:
                self.tree.insert('', 'end', iid=str(s.index),
                                 values=(s.index, '-', '(空)', '-', '-'))
            else:
                self.tree.insert('', 'end', iid=str(s.index),
                                 values=(s.index, s.item_id, item_name(s.item_id),
                                         s.count, s.rank))

    # ---- events ----
    def on_select(self, _ev=None):
        s = self._sel()
        if not s:
            return
        if s.empty:
            self.count_var.set('1')
            self.rank_var.set('0')
            self.search_var.set('')
            self.item_combo.set('')
            self.status.set(f'格 {s.index} 是空的: 搜索并选择物品后点“应用到格子”即可添加')
            return
        self.count_var.set(str(s.count))
        self.rank_var.set(str(s.rank))
        name = item_name(s.item_id)
        self.search_var.set('')
        self.item_combo.set(f'{s.item_id} {name}')

    def _sel(self):
        sel = self.tree.selection()
        if not sel or not self.save:
            return None
        return next((s for s in self.save.slots if str(s.index) == sel[0]), None)

    def on_search(self, *_):
        self._refresh_combo(self.search_var.get().strip())

    def _refresh_combo(self, q):
        vals = []
        for iid, (zh, en) in ITEMS.items():
            if not q or q in zh or q.lower() in en.lower() or q == str(iid):
                vals.append(f'{iid} {zh}')
            if len(vals) >= 300:
                break
        self.item_combo['values'] = vals

    # ---- apply ----
    def apply_money(self):
        if not self.save:
            return
        try:
            self.save.money = int(self.money_var.get())
        except Exception as e:
            messagebox.showerror('错误', str(e))
            return
        self.status.set(f'金钱已改为 {self.save.money} (记得点“保存修改”)')

    def apply_slot(self):
        s = self._sel()
        if not s:
            messagebox.showinfo('提示', '请先在列表中选中一个格子')
            return
        try:
            iid = None
            combo = self.item_combo.get().strip()
            if combo:
                iid = int(combo.split()[0])
            if s.empty:
                if iid is None:
                    messagebox.showinfo('提示', '空格子请先搜索并选择一个物品')
                    return
                self.save.fill_slot(s.index, iid,
                                    count=int(self.count_var.get()),
                                    rank=int(self.rank_var.get()))
            else:
                self.save.set_slot(s, item_id=iid,
                                   count=int(self.count_var.get()),
                                   rank=int(self.rank_var.get()))
        except Exception as e:
            messagebox.showerror('错误', str(e))
            return
        self.refresh_tree()
        self.status.set(f'格 {s.index} 已修改 (记得点“保存修改”)')

    def write_save(self):
        if not self.save:
            return
        try:
            self.save.write()
        except Exception as e:
            messagebox.showerror('保存失败', str(e))
            return
        messagebox.showinfo('完成', '已写入存档。\n首次修改已自动备份为 save.001.bak\n'
                            '如出现问题，删除 save.001 并将备份改名恢复即可。')


if __name__ == '__main__':
    App().mainloop()
