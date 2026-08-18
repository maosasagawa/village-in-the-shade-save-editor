# -*- coding: utf-8 -*-
"""Save data model for Village in the Shade (静谧田园).

File format:
  YKCMP_V1 container (type 8 = raw LZ4 block) -> 20 MiB 'SER' tree.
  SER record: [type u8][name-offset u32][size u32][payload]
    type 0 leaf, 1 array(+u32 count), 2 object, 3 map(+u32 count),
    4 pointer(+u32 addr), 5 string(+u32 len)
Only fixed-size leaf values are patched in place, so no size fixups needed.
"""
import os, shutil, struct

from .ykcmp import lz4_compress, lz4_decompress
from .ser import Ser


def default_save_dirs():
    """Candidate save directories on Windows / Steam Deck (Proton)."""
    dirs = []
    appdata = os.environ.get('APPDATA')
    if appdata:
        dirs.append(os.path.join(appdata, 'Nippon Ichi Software, Inc', 'Honogurashinoniwa'))
    dirs.append(os.path.expanduser(
        '~/.local/share/Steam/steamapps/compatdata/3934250/pfx/drive_c/users/'
        'steamuser/AppData/Roaming/Nippon Ichi Software, Inc/Honogurashinoniwa'))
    return [d for d in dirs if os.path.isdir(d)]


def find_saves():
    """Return list of save.* files found in default locations."""
    out = []
    for d in default_save_dirs():
        for root, _dirs, files in os.walk(d):
            for fn in sorted(files):
                if fn.startswith('save.') and fn != 'save.lst':
                    out.append(os.path.join(root, fn))
    return out


class Slot:
    def __init__(self, index, id_rec, count_rec, rank_rec, quality_rec):
        self.index = index
        self._id = id_rec
        self._count = count_rec
        self._rank = rank_rec
        self._quality = quality_rec

    @property
    def empty(self):
        return self._id is None

    item_id = property(lambda s: s._id['value'] if s._id else None)
    count = property(lambda s: s._count['value'] if s._count else None)
    rank = property(lambda s: s._rank['value'] if s._rank else None)
    quality = property(lambda s: s._quality['value'] if s._quality else None)


class SaveData:
    def __init__(self, path):
        self.path = path
        data = open(path, 'rb').read()
        if data[:8] != b'YKCMP_V1':
            raise ValueError('不是 YKCMP_V1 存档文件')
        typ, csize, dsize = struct.unpack_from('<III', data, 8)
        if typ != 8:
            raise ValueError(f'不支持的压缩类型 {typ}')
        self.filesize = len(data)
        self.raw = bytearray(lz4_decompress(data[0x14:csize], dsize))
        self._parse()

    # ---- parsing ----
    def _parse(self):
        self.ser = Ser(bytes(self.raw))
        self.top = []
        self.ser.parse(0x19, 0x19 + self.ser.stream_len, out=self.top)
        money = self._find(self.top, 'money_')
        self._money = self._get(money, 'this->value_') if money else None
        self.slots = self._collect_slots('inventoryItemList_')
        self.tool_slots = self._collect_slots('toolItemList_')

    def _collect_slots(self, list_name):
        inv = self._find(self.top, list_name)
        slots = []
        if not inv:
            return slots
        for slot in inv.get('children', []):
            p = slot['children'][0] if slot.get('children') else None
            try:
                idx = int(slot['name'])
            except ValueError:
                idx = len(slots)
            if not p or not p.get('children'):
                slots.append(Slot(idx, None, None, None, None))
                continue
            d = self._get(p, 'pData_')
            sc = self._get(p, 'stackCount_')
            slots.append(Slot(
                idx,
                self._get(d, 'dataID') if d else None,
                self._get(sc, 'this->value_') if sc else None,
                self._get(p, 'rank_'),
                self._get(p, 'qualityUpValue_'),
            ))
        return slots

    def _find(self, recs, name):
        for r in recs:
            if r['name'] == name:
                return r
            if 'children' in r:
                got = self._find(r['children'], name)
                if got:
                    return got

    @staticmethod
    def _get(obj, name):
        for c in (obj or {}).get('children', []):
            if c['name'] == name:
                return c

    # ---- editing (in-place, fixed size) ----
    def _patch(self, rec, value, size):
        off = rec['off'] + 9
        struct.pack_into({1: '<b', 4: '<i', 8: '<q'}[size], self.raw, off, value)
        rec['value'] = value

    @property
    def money(self):
        return self._money['value'] if self._money else None

    @money.setter
    def money(self, v):
        if not 0 <= v <= 999_999_999:
            raise ValueError('金钱范围 0 ~ 999999999')
        self._patch(self._money, v, 8)

    def set_slot(self, slot, item_id=None, count=None, rank=None, quality=None):
        if slot.empty:
            raise ValueError('空格子暂不支持添加物品，请先在游戏内放入任意物品占位')
        if item_id is not None:
            self._patch(slot._id, int(item_id), 8)
        if count is not None:
            if not 1 <= count <= 9999:
                raise ValueError('数量范围 1 ~ 9999')
            self._patch(slot._count, int(count), 4)
        if rank is not None:
            if not 0 <= rank <= 4:
                raise ValueError('星级范围 0 ~ 4')
            self._patch(slot._rank, int(rank), 4)
        if quality is not None:
            self._patch(slot._quality, int(quality), 4)

    # ---- empty slot filling (record insertion) ----
    def _path_to(self, target):
        """Ancestor chain (root..parent) leading to record `target`."""
        def walk(recs, path):
            for r in recs:
                if r is target:
                    return list(path)
                if 'children' in r:
                    path.append(r)
                    got = walk(r['children'], path)
                    path.pop()
                    if got is not None:
                        return got
            return None
        return walk(self.top, [])

    def _all_t4_addrs(self):
        addrs = set()
        def walk(recs):
            for r in recs:
                if r['type'] == 4:
                    addrs.add(r.get('addr', 0))
                if 'children' in r:
                    walk(r['children'])
        walk(self.top)
        return addrs

    def _next_unique_id(self):
        gen = self._find(self.top, 'statusUniqueIDGenerator_')
        val = self._get(gen, 'idSeed_')
        uid = val['value']
        self._patch(val, uid + 1, val['size'])
        return uid

    def fill_slot(self, index, item_id, count=1, rank=0):
        """Create an item in an empty inventory slot by splicing a copy of a
        non-empty slot record, then fixing all ancestor sizes + header."""
        inv = self._find(self.top, 'inventoryItemList_')
        slot_rec = self._get(inv, str(index))
        if slot_rec is None:
            raise ValueError(f'没有第 {index} 格')
        if slot_rec['size'] != 0:
            raise ValueError(f'第 {index} 格不是空的')
        donor = min((c for c in inv['children'] if c['size'] > 0),
                    key=lambda c: c['size'], default=None)
        if donor is None:
            raise ValueError('背包全空，找不到可复制的模板格')
        uid = self._next_unique_id()  # patches generator in raw

        # donor record bytes: [t4][name][size][addr][payload...]
        d0 = donor['off']
        dlen = 9 + 4 + donor['size']
        blob = bytearray(self.raw[d0:d0 + dlen])
        struct.pack_into('<I', blob, 1, struct.unpack_from('<I', self.raw, slot_rec['off'] + 1)[0])
        new_addr = (max(a for a in self._all_t4_addrs() if a != 0xffffffff) + 1) & 0xffffffff
        struct.pack_into('<I', blob, 9, new_addr)

        # splice over the 13-byte null-pointer record
        s0, s1 = slot_rec['off'], slot_rec['off'] + 13
        delta = len(blob) - (s1 - s0)
        total, strtab = struct.unpack_from('<II', self.raw, 8)
        if self.raw[-delta:] != b'\0' * delta:
            raise ValueError('缓冲区尾部空间不足')
        ancestors = self._path_to(slot_rec)
        if ancestors is None:
            raise RuntimeError('内部错误: 找不到记录路径')
        # fix ancestor size fields (u32 at off+5)
        for anc in ancestors:
            sz = struct.unpack_from('<I', self.raw, anc['off'] + 5)[0]
            struct.pack_into('<I', self.raw, anc['off'] + 5, sz + delta)
        # fix header: total @0x08, strtab @0x0C, stream_len @0x15
        struct.pack_into('<II', self.raw, 8, total + delta, strtab + delta)
        sl = struct.unpack_from('<I', self.raw, 0x15)[0]
        struct.pack_into('<I', self.raw, 0x15, sl + delta)
        self.raw[s0:s1] = blob
        del self.raw[len(self.raw) - delta:]  # keep buffer at 20 MiB

        # reparse (offsets shifted) and patch the new item's fields
        self._parse()
        slot = next(s for s in self.slots if s.index == index)
        if slot.empty:
            raise RuntimeError('内部错误: 填充失败')
        self._patch(slot._id, int(item_id), 8)
        self._patch(slot._count, int(count), 4)
        self._patch(slot._rank, int(rank), 4)
        self._patch(slot._quality, 0, 4)
        # fresh uniqueID
        inv = self._find(self.top, 'inventoryItemList_')
        rec = self._get(inv, str(index))
        p = rec['children'][0]
        u = self._get(p, 'uniqueID_')
        self._patch(u, uid, u['size'])
        return slot

    # ---- writing ----
    def write(self, path=None, backup=True):
        path = path or self.path
        comp = lz4_compress(bytes(self.raw))
        blob = b'YKCMP_V1' + struct.pack('<III', 8, len(comp) + 0x14, len(self.raw)) + comp
        if len(blob) > self.filesize:
            raise ValueError('压缩后大小超过原文件，拒绝写入')
        blob += b'\0' * (self.filesize - len(blob))
        if backup and os.path.exists(path):
            bak = path + '.bak'
            if not os.path.exists(bak):
                shutil.copy2(path, bak)
        with open(path, 'wb') as f:
            f.write(blob)
