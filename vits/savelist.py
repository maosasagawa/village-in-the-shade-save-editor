# -*- coding: utf-8 -*-
"""save.lst parsing and safe save-slot/language cloning."""
from dataclasses import dataclass
from datetime import datetime
import os
import re
import shutil
import struct

from .ser import Ser
from .ykcmp import compress_container, decompress_container


SLOT_RANGES = ((1, 5), (6, 10), (11, 15))
SLOT_BASE_IDS = (1, 6, 11)
LANGUAGES = {
    'jp': (0, 40, '日本語', 'Japanese'),
    'en': (1, 41, '英語', 'English'),
    'fr': (2, 42, '法語', 'French'),
    'es': (3, 43, '西班牙語', 'Spanish'),
    'tc': (4, 45, '繁體中文', 'Traditional Chinese'),
    'ko': (5, 46, '韓語', 'Korean'),
}
LANGUAGE_BY_ID = {value[0]: (code,) + value[2:]
                  for code, value in LANGUAGES.items()}


def slot_for_number(number):
    for index, (start, end) in enumerate(SLOT_RANGES, 1):
        if start <= number <= end:
            return index


def save_number(path):
    match = re.fullmatch(r'save\.(\d{3})', os.path.basename(path))
    return int(match.group(1)) if match else None


@dataclass
class SaveListEntry:
    number: int
    date: int
    time: int
    title: bytes
    second: bytes
    extra: bytes

    @property
    def slot(self):
        return slot_for_number(self.number)

    @property
    def language_id(self):
        ser = Ser(self.extra)
        top = []
        ser.parse(0x19, 0x19 + ser.stream_len, out=top)
        rec = next((item for item in top if item['name'] == 'languageID'), None)
        return rec['value'] if rec else None

    def set_language(self, language_id):
        raw = bytearray(self.extra)
        ser = Ser(bytes(raw))
        top = []
        ser.parse(0x19, 0x19 + ser.stream_len, out=top)
        rec = next((item for item in top if item['name'] == 'languageID'), None)
        if not rec or rec['size'] != 4:
            raise ValueError('save.lst entry has no languageID')
        struct.pack_into('<i', raw, rec['off'] + 9, language_id)
        self.extra = bytes(raw)

    def serialize(self):
        return (struct.pack('<IIII', self.number, self.date, self.time,
                            len(self.title)) + self.title
                + struct.pack('<I', len(self.second)) + self.second
                + struct.pack('<I', len(self.extra)) + self.extra)

    def clone(self, number, language_id):
        now = datetime.now()
        entry = SaveListEntry(number, int(now.strftime('%Y%m%d')),
                              int(now.strftime('%H%M%S')), self.title,
                              self.second, self.extra)
        entry.set_language(language_id)
        return entry


class SaveList:
    def __init__(self, path):
        self.path = path
        typ, raw = decompress_container(open(path, 'rb').read())
        if typ != 4:
            raise ValueError('save.lst is not YKCMP type 4')
        self.entries = self._parse(raw)

    @staticmethod
    def _parse(raw):
        if len(raw) < 4:
            raise ValueError('truncated save.lst')
        count = struct.unpack_from('<I', raw, 0)[0]
        entries = []
        pos = 4
        for _ in range(count):
            if pos + 16 > len(raw):
                raise ValueError('truncated save.lst entry')
            number, date, time, length = struct.unpack_from('<IIII', raw, pos)
            pos += 16
            title = raw[pos:pos + length]
            pos += length
            length = struct.unpack_from('<I', raw, pos)[0]
            pos += 4
            second = raw[pos:pos + length]
            pos += length
            length = struct.unpack_from('<I', raw, pos)[0]
            pos += 4
            extra = raw[pos:pos + length]
            pos += length
            if len(title) == 0 or len(extra) != length:
                raise ValueError('invalid save.lst entry')
            entries.append(SaveListEntry(number, date, time, title, second, extra))
        if pos != len(raw):
            raise ValueError('unused bytes in save.lst')
        return entries

    def current_slots(self):
        result = {}
        for entry in self.entries:
            slot = entry.slot
            if slot is None:
                continue
            previous = result.get(slot)
            if previous is None or (entry.date, entry.time) > (previous.date, previous.time):
                result[slot] = entry
        return result

    def entry_for_number(self, number):
        return next((entry for entry in self.entries if entry.number == number), None)

    def raw(self):
        return struct.pack('<I', len(self.entries)) + b''.join(
            entry.serialize() for entry in self.entries)

    def write(self, backup=True):
        blob = compress_container(self.raw(), 4)
        # Verify both codec and parser before replacing the real index.
        _typ, check = decompress_container(blob)
        self._parse(check)
        if backup and os.path.exists(self.path) and not os.path.exists(self.path + '.bak'):
            shutil.copy2(self.path, self.path + '.bak')
        temp = self.path + '.tmp-editor'
        with open(temp, 'wb') as stream:
            stream.write(blob)
        os.replace(temp, self.path)


class SlotOccupiedError(ValueError):
    pass


def _backup(path):
    candidate = path + '.bak'
    if os.path.exists(candidate):
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        candidate = path + f'.bak.{stamp}'
        index = 2
        while os.path.exists(candidate):
            candidate = path + f'.bak.{stamp}.{index}'
            index += 1
    shutil.copy2(path, candidate)
    return candidate


def copy_to_slot(source_path, target_slot, language_code, replace=False):
    """Clone an indexed save into another official slot and set its language."""
    from .savedata import SaveData

    if target_slot not in (1, 2, 3):
        raise ValueError('target slot must be 1, 2 or 3')
    if language_code not in LANGUAGES:
        raise ValueError(f'unsupported language {language_code}')
    directory = os.path.dirname(source_path)
    listing = SaveList(os.path.join(directory, 'save.lst'))
    source_number = save_number(source_path)
    source_entry = listing.entry_for_number(source_number)
    if source_entry is None:
        raise ValueError('source save is not indexed by save.lst')
    if source_entry.slot == target_slot:
        raise ValueError('source and target slots are the same')
    slots = listing.current_slots()
    target_entry = slots.get(target_slot)
    if target_entry and not replace:
        raise SlotOccupiedError(f'slot {target_slot} is occupied')
    target_number = target_entry.number if target_entry else SLOT_BASE_IDS[target_slot - 1]
    target_path = os.path.join(directory, f'save.{target_number:03d}')
    language_id, _flag, _zh, _en = LANGUAGES[language_code]

    original_list = open(listing.path, 'rb').read()
    original_target = open(target_path, 'rb').read() if os.path.exists(target_path) else None
    try:
        _backup(listing.path)
        if original_target is not None:
            _backup(target_path)
        shutil.copy2(source_path, target_path)
        target_save = SaveData(target_path)
        target_save.set_game_language(language_id)
        target_save.write(backup=False)

        listing.entries = [entry for entry in listing.entries
                           if entry.slot != target_slot]
        listing.entries.append(source_entry.clone(target_number, language_id))
        listing.entries.sort(key=lambda entry: entry.number)
        listing.write(backup=False)
    except Exception:
        with open(listing.path, 'wb') as stream:
            stream.write(original_list)
        if original_target is None:
            if os.path.exists(target_path):
                os.remove(target_path)
        else:
            with open(target_path, 'wb') as stream:
                stream.write(original_target)
        raise
    return target_path
