#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静谧田园 (Village in the Shade) 存档修改器 GUI / Save Editor GUI"""
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from vits.savedata import SaveData, find_saves
from vits.items_db import ITEMS
from vits.npcs_db import NPCS, love_level
from vits.animals_db import livestock_name, creature_name, CATS
from vits import i18n
from vits.i18n import T, season_name


PROJECT_URL = 'https://github.com/maosasagawa/village-in-the-shade-save-editor'


def item_name(iid):
    e = ITEMS.get(iid)
    if not e:
        return f'? {iid}'
    return e[0] if i18n.LANG == 'zh' else e[1]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.save = None
        self._build()
        self._autoload()

    # ---- UI ----
    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        self.title(T('title'))
        self.geometry('880x620')

        top = ttk.Frame(self); top.pack(fill='x', padx=8, pady=6)
        ttk.Button(top, text=T('open'), command=self.open_save).pack(side='left')
        self.save_combo = ttk.Combobox(top, width=46, state='readonly')
        self.save_combo.pack(side='left', padx=6)
        self.save_combo.bind('<<ComboboxSelected>>',
                             lambda e: self.load(self.save_combo.get()))
        self.lang_combo = ttk.Combobox(top, width=8, state='readonly',
                                       values=['中文', 'English'])
        self.lang_combo.set('中文' if i18n.LANG == 'zh' else 'English')
        self.lang_combo.pack(side='right', padx=4)
        self.lang_combo.bind('<<ComboboxSelected>>', self.on_lang)
        ttk.Button(top, text=T('save'), command=self.write_save).pack(side='right', padx=4)

        mf = ttk.LabelFrame(self, text=T('money')); mf.pack(fill='x', padx=8, pady=4)
        self.money_var = tk.StringVar()
        ttk.Entry(mf, textvariable=self.money_var, width=14).pack(side='left', padx=6, pady=4)
        ttk.Button(mf, text=T('apply'), command=self.apply_money).pack(side='left')

        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True, padx=8, pady=4)
        body = ttk.Frame(nb); nb.add(body, text=T('tab_inv'))
        npctab = ttk.Frame(nb); nb.add(npctab, text=T('tab_npc'))
        animtab = ttk.Frame(nb); nb.add(animtab, text=T('tab_animal'))
        self._build_inv_tab(body)
        self._build_npc_tab(npctab)
        self._build_animal_tab(animtab)

        bottom = ttk.Frame(self); bottom.pack(fill='x', padx=8, pady=4)
        self.status = tk.StringVar(value=T('hint'))
        ttk.Label(bottom, textvariable=self.status, foreground='#666').pack(side='left')
        link = ttk.Label(bottom, text=PROJECT_URL.replace('https://', ''),
                         foreground='#0066cc', cursor='hand2')
        link.pack(side='right')
        link.bind('<Button-1>', lambda e: webbrowser.open(PROJECT_URL))

    def _build_inv_tab(self, body):
        cols = ('slot', 'id', 'name', 'count', 'rank')
        tf = ttk.Frame(body); tf.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(tf, columns=cols, show='headings', selectmode='browse')
        for c, w, t in (('slot', 50, T('col_slot')), ('id', 90, T('col_id')),
                        ('name', 320, T('col_name')), ('count', 70, T('col_count')),
                        ('rank', 60, T('col_rank'))):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor='w')
        vsb = ttk.Scrollbar(tf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='left', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        ef = ttk.LabelFrame(body, text=T('edit_slot')); ef.pack(fill='x', pady=6)
        ttk.Label(ef, text=T('search_item')).grid(row=0, column=0, padx=4, pady=4, sticky='e')
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        ttk.Entry(ef, textvariable=self.search_var, width=24).grid(row=0, column=1, padx=4)
        self.item_combo = ttk.Combobox(ef, width=44, state='readonly')
        self.item_combo.grid(row=0, column=2, padx=4, columnspan=3, sticky='w')
        ttk.Label(ef, text=T('count')).grid(row=1, column=0, padx=4, sticky='e')
        self.count_var = tk.StringVar()
        ttk.Spinbox(ef, from_=1, to=9999, textvariable=self.count_var, width=8).grid(row=1, column=1, sticky='w', padx=4)
        ttk.Label(ef, text=T('rank04')).grid(row=1, column=2, padx=4, sticky='e')
        self.rank_var = tk.StringVar()
        ttk.Spinbox(ef, from_=0, to=4, textvariable=self.rank_var, width=6).grid(row=1, column=3, sticky='w', padx=4)
        ttk.Button(ef, text=T('apply_slot'), command=self.apply_slot).grid(row=1, column=4, padx=10)
        self._refresh_combo('')

    def _build_npc_tab(self, tab):
        tf = ttk.LabelFrame(tab, text=T('game_time')); tf.pack(fill='x', padx=4, pady=4)
        self.day_var = tk.StringVar()
        ttk.Label(tf, text=T('day_pre')).pack(side='left', padx=(8, 2))
        ttk.Entry(tf, textvariable=self.day_var, width=6).pack(side='left')
        ttk.Label(tf, text=T('day_post')).pack(side='left', padx=2)
        self.time_info = tk.StringVar()
        ttk.Label(tf, textvariable=self.time_info, foreground='#666').pack(side='left', padx=10)
        ttk.Button(tf, text=T('apply_day'), command=self.apply_day).pack(side='right', padx=8)

        nf = ttk.Frame(tab); nf.pack(fill='both', expand=True, padx=4, pady=4)
        cols = ('id', 'name', 'role', 'love', 'level')
        self.npc_tree = ttk.Treeview(nf, columns=cols, show='headings', selectmode='browse')
        for c, w, t in (('id', 60, T('col_npc_id')), ('name', 120, T('col_npc_name')),
                        ('role', 130, T('col_npc_role')), ('love', 110, T('col_love')),
                        ('level', 60, T('col_level'))):
            self.npc_tree.heading(c, text=t)
            self.npc_tree.column(c, width=w, anchor='w')
        vsb = ttk.Scrollbar(nf, orient='vertical', command=self.npc_tree.yview)
        self.npc_tree.configure(yscrollcommand=vsb.set)
        self.npc_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='left', fill='y')
        self.npc_tree.bind('<<TreeviewSelect>>', self.on_npc_select)

        ef = ttk.Frame(tab); ef.pack(fill='x', padx=4, pady=4)
        ttk.Label(ef, text=T('love_label')).pack(side='left', padx=4)
        self.love_var = tk.StringVar()
        ttk.Spinbox(ef, from_=0, to=2100, textvariable=self.love_var, width=8).pack(side='left', padx=4)
        ttk.Button(ef, text=T('apply_npc'), command=self.apply_love).pack(side='left', padx=8)
        ttk.Button(ef, text=T('max_all'), command=self.max_all_love).pack(side='left', padx=8)

    def _build_animal_tab(self, tab):
        lf = ttk.LabelFrame(tab, text=T('sect_livestock')); lf.pack(fill='both', expand=True, padx=4, pady=4)
        cols = ('no', 'species', 'name', 'love', 'mood')
        self.anim_tree = ttk.Treeview(lf, columns=cols, show='headings',
                                      selectmode='browse', height=7)
        for c, w, t in (('no', 40, T('col_animal_no')), ('species', 160, T('col_species')),
                        ('name', 120, T('col_animal_name')), ('love', 110, T('col_animal_love')),
                        ('mood', 70, T('col_mood'))):
            self.anim_tree.heading(c, text=t)
            self.anim_tree.column(c, width=w, anchor='w')
        self.anim_tree.pack(side='top', fill='both', expand=True)
        self.anim_tree.bind('<<TreeviewSelect>>', self.on_animal_select)
        af = ttk.Frame(lf); af.pack(fill='x', pady=3)
        self.anim_love_var = tk.StringVar()
        ttk.Spinbox(af, from_=0, to=2000, textvariable=self.anim_love_var, width=8).pack(side='left', padx=6)
        ttk.Button(af, text=T('apply_animal'), command=self.apply_animal).pack(side='left', padx=4)
        ttk.Button(af, text=T('max_all_animal'), command=self.max_all_animals).pack(side='left', padx=4)

        cf = ttk.LabelFrame(tab, text=T('sect_creature')); cf.pack(fill='both', expand=True, padx=4, pady=4)
        ccols = ('id', 'creature', 'like')
        self.crea_tree = ttk.Treeview(cf, columns=ccols, show='headings',
                                      selectmode='browse', height=7)
        for c, w, t in (('id', 100, 'ID'), ('creature', 200, T('col_creature')),
                        ('like', 120, T('col_like'))):
            self.crea_tree.heading(c, text=t)
            self.crea_tree.column(c, width=w, anchor='w')
        self.crea_tree.pack(side='top', fill='both', expand=True)
        self.crea_tree.bind('<<TreeviewSelect>>', self.on_creature_select)
        bf = ttk.Frame(cf); bf.pack(fill='x', pady=3)
        self.crea_like_var = tk.StringVar()
        ttk.Spinbox(bf, from_=0, to=12000, textvariable=self.crea_like_var, width=8).pack(side='left', padx=6)
        ttk.Button(bf, text=T('apply_creature'), command=self.apply_creature).pack(side='left', padx=4)
        ttk.Button(bf, text=T('max_all_cat'), command=self.max_all_cats).pack(side='left', padx=4)

    # ---- language ----
    def on_lang(self, _ev=None):
        i18n.set_lang('zh' if self.lang_combo.get() == '中文' else 'en')
        self._build()
        saves = find_saves()
        self.save_combo['values'] = saves
        if self.save:
            self.save_combo.set(self.save.path)
            self.money_var.set(str(self.save.money))
            self.refresh_tree()
            self.refresh_npcs()
            self.refresh_animals()

    # ---- data ----
    def _autoload(self):
        saves = find_saves()
        self.save_combo['values'] = saves
        if saves:
            self.save_combo.set(saves[0])
            self.load(saves[0])

    def open_save(self):
        init = os.path.dirname(find_saves()[0]) if find_saves() else os.path.expanduser('~')
        p = filedialog.askopenfilename(initialdir=init, title='save.001',
                                       filetypes=[('save', 'save.*'), ('*', '*')])
        if p:
            self.load(p)

    def load(self, path):
        try:
            self.save = SaveData(path)
        except Exception as e:
            messagebox.showerror(T('open_fail'), str(e))
            return
        self.money_var.set(str(self.save.money))
        self.refresh_tree()
        self.refresh_npcs()
        self.refresh_animals()
        self.status.set(T('loaded').format(len(self.save.slots)))

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.save.slots:
            if s.empty:
                self.tree.insert('', 'end', iid=str(s.index),
                                 values=(s.index, '-', T('empty'), '-', '-'))
            else:
                self.tree.insert('', 'end', iid=str(s.index),
                                 values=(s.index, s.item_id, item_name(s.item_id),
                                         s.count, s.rank))

    def refresh_npcs(self):
        if not self.save:
            return
        self.npc_tree.delete(*self.npc_tree.get_children())
        zh = i18n.LANG == 'zh'
        for did, lv in self.save.npcs:
            e = NPCS.get(did, ('?', '?', '?', '?'))
            v = lv['value']
            self.npc_tree.insert('', 'end', iid=str(did),
                                 values=(did, e[0] if zh else e[1], e[2] if zh else e[3],
                                         v, f'Lv{love_level(v)}'))
        sec = self.save.game_seconds['value']
        day = sec // 86400
        self.day_var.set(str(day))
        self.time_info.set(T('time_info').format(
            sec % 86400 // 3600, sec % 86400 % 3600 // 60,
            season_name(day // 30 % 4), day % 30 + 1,
            season_name(day // 28 % 4), day % 28 + 1))

    def refresh_animals(self):
        if not self.save:
            return
        lang = i18n.LANG
        self.anim_tree.delete(*self.anim_tree.get_children())
        for an in self.save.livestock:
            mood = an['mood']['value'] if an['mood'] else '-'
            self.anim_tree.insert('', 'end', iid=str(an['index']),
                                  values=(an['index'], livestock_name(an['species'], lang),
                                          an['name'], an['love']['value'], mood))
        self.crea_tree.delete(*self.crea_tree.get_children())
        rows = [(cid, rec) for cid, rec in self.save.creatures
                if rec['value'] or cid in CATS]
        rows.sort(key=lambda t: (t[0] not in CATS, -t[1]['value']))
        for cid, rec in rows:
            self.crea_tree.insert('', 'end', iid=str(cid),
                                  values=(cid, creature_name(cid, lang), rec['value']))

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
            self.status.set(T('slot_empty_hint').format(s.index))
            return
        self.count_var.set(str(s.count))
        self.rank_var.set(str(s.rank))
        self.search_var.set('')
        self.item_combo.set(f'{s.item_id} {item_name(s.item_id)}')

    def _sel(self):
        sel = self.tree.selection()
        if not sel or not self.save:
            return None
        return next((s for s in self.save.slots if str(s.index) == sel[0]), None)

    def on_search(self, *_):
        self._refresh_combo(self.search_var.get().strip())

    def _refresh_combo(self, q):
        vals = []
        zh = i18n.LANG == 'zh'
        for iid, (zn, en) in ITEMS.items():
            if not q or q in zn or q.lower() in en.lower() or q == str(iid):
                vals.append(f'{iid} {zn if zh else en}')
            if len(vals) >= 300:
                break
        self.item_combo['values'] = vals

    def on_npc_select(self, _ev=None):
        sel = self.npc_tree.selection()
        if sel and self.save:
            for did, lv in self.save.npcs:
                if str(did) == sel[0]:
                    self.love_var.set(str(lv['value']))

    def on_animal_select(self, _ev=None):
        sel = self.anim_tree.selection()
        if sel and self.save:
            an = self.save.livestock[int(sel[0])]
            self.anim_love_var.set(str(an['love']['value']))

    def on_creature_select(self, _ev=None):
        sel = self.crea_tree.selection()
        if sel and self.save:
            for cid, rec in self.save.creatures:
                if str(cid) == sel[0]:
                    self.crea_like_var.set(str(rec['value']))

    # ---- apply ----
    def apply_money(self):
        if not self.save:
            return
        try:
            self.save.money = int(self.money_var.get())
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.status.set(T('money_set').format(self.save.money))

    def apply_slot(self):
        s = self._sel()
        if not s:
            messagebox.showinfo(T('notice'), T('pick_slot'))
            return
        try:
            iid = None
            combo = self.item_combo.get().strip()
            if combo:
                iid = int(combo.split()[0])
            if s.empty:
                if iid is None:
                    messagebox.showinfo(T('notice'), T('pick_item'))
                    return
                self.save.fill_slot(s.index, iid,
                                    count=int(self.count_var.get()),
                                    rank=int(self.rank_var.get()))
            else:
                self.save.set_slot(s, item_id=iid,
                                   count=int(self.count_var.get()),
                                   rank=int(self.rank_var.get()))
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.refresh_tree()
        self.status.set(T('slot_set').format(s.index))

    def apply_love(self):
        sel = self.npc_tree.selection()
        if not sel or not self.save:
            return
        try:
            self.save.set_npc_love(int(sel[0]), int(self.love_var.get()))
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.refresh_npcs()
        self.status.set(T('love_set').format(sel[0]))

    def max_all_love(self):
        if not self.save:
            return
        for did, _lv in self.save.npcs:
            self.save.set_npc_love(did, 2100)
        self.refresh_npcs()
        self.status.set(T('love_maxed'))

    def apply_animal(self):
        sel = self.anim_tree.selection()
        if not sel or not self.save:
            return
        try:
            self.save.set_livestock_love(int(sel[0]), int(self.anim_love_var.get()))
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.refresh_animals()
        self.status.set(T('animal_set').format(sel[0]))

    def max_all_animals(self):
        if not self.save:
            return
        # 小动物(鸡鸭火鸡类 1-6,19-25,30)上限 1500, 其余 2000
        small = set(range(1, 7)) | set(range(19, 26)) | {30}
        for an in self.save.livestock:
            cap = 1500 if an['species'] in small else 2000
            self.save.set_livestock_love(an['index'], cap)
        self.refresh_animals()
        self.status.set(T('animal_maxed'))

    def apply_creature(self):
        sel = self.crea_tree.selection()
        if not sel or not self.save:
            return
        try:
            self.save.set_creature_like(int(sel[0]), int(self.crea_like_var.get()))
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.refresh_animals()
        self.status.set(T('creature_set').format(sel[0]))

    def max_all_cats(self):
        if not self.save:
            return
        for cid, _rec in self.save.creatures:
            if cid in CATS:
                self.save.set_creature_like(cid, 12000)
        self.refresh_animals()
        self.status.set(T('cat_maxed'))

    def apply_day(self):
        if not self.save:
            return
        try:
            self.save.set_game_day(int(self.day_var.get()))
        except Exception as e:
            messagebox.showerror(T('err'), str(e))
            return
        self.refresh_npcs()
        self.status.set(T('day_set'))

    def write_save(self):
        if not self.save:
            return
        try:
            self.save.write()
        except Exception as e:
            messagebox.showerror(T('save_fail'), str(e))
            return
        messagebox.showinfo(T('done'), T('saved_msg'))


if __name__ == '__main__':
    App().mainloop()
