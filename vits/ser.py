#!/usr/bin/env python3
"""Parser for NIS 'SER' serialized save data (Village in the Shade)."""
import struct, sys, json

class Ser:
    def __init__(self, raw):
        self.raw = raw
        assert raw[:4] == b'SER\0'
        self.total, self.strtab = struct.unpack_from('<II', raw, 8)
        # 0x14: u8 pad?, u32 stream length
        self.stream_len = struct.unpack_from('<I', raw, 0x15)[0]
        self.names = {}
    def name(self, nid):
        if nid not in self.names:
            base = self.strtab + nid
            if base >= len(self.raw) or nid > 0x100000:
                return f'<bad:{nid:#x}>'
            end = self.raw.find(b'\0', base, base + 256)
            if end < 0: return f'<bad:{nid:#x}>'
            self.names[nid] = self.raw[base:end].decode('utf-8', 'replace')
        return self.names[nid]
    def _looks_like_records(self, pos, end):
        # heuristic: first byte is a small type and name id resolves inside strtab
        if end - pos < 9: return False
        typ = self.raw[pos]
        nid = struct.unpack_from('<I', self.raw, pos+1)[0]
        return typ <= 5 and self.strtab + nid < len(self.raw) and nid < 0x20000

    def parse(self, pos, end, depth=0, out=None, maxdepth=99):
        while pos < end:
            typ = self.raw[pos]
            nid, size = struct.unpack_from('<II', self.raw, pos+1)
            if typ > 5 or size > end - pos:
                if out is not None:
                    out.append({'type': -1, 'name': f'<garbage@{pos:#x}>', 'off': pos,
                                'size': end-pos, 'data': self.raw[pos:min(pos+64,end)]})
                return out
            hdr_end = pos + 9
            nm = self.name(nid)
            rec = {'type': typ, 'name': nm, 'off': pos, 'size': size}
            if out is not None: out.append(rec)
            if typ == 2:  # object: size = total child bytes
                rec['children'] = []
                self.parse(hdr_end, hdr_end + size, depth+1, rec['children'], maxdepth)
                pos = hdr_end + size
            elif typ in (1, 3):  # 1=array, 3=map: extra u32 count, size = element bytes
                count = struct.unpack_from('<I', self.raw, hdr_end)[0]
                rec['count'] = count
                body = hdr_end + 4
                nxt = body + size
                if typ == 3 or (size and count and self._looks_like_records(body, nxt)):
                    rec['children'] = []
                    self.parse(body, nxt, depth+1, rec['children'], maxdepth)
                else:
                    rec['data'] = self.raw[body:body+size]
                pos = nxt
            elif typ == 4:  # pointer: extra u32 addr, then size bytes of contents
                addr = struct.unpack_from('<I', self.raw, hdr_end)[0]
                rec['addr'] = addr
                body = hdr_end + 4
                nxt = body + size
                if nxt > body:
                    rec['children'] = []
                    self.parse(body, nxt, depth+1, rec['children'], maxdepth)
                pos = nxt
            else:
                payload = self.raw[hdr_end:hdr_end+size]
                rec['data'] = payload
                if typ == 0:
                    if size == 1: rec['value'] = payload[0]
                    elif size == 4: rec['value'] = struct.unpack('<i', payload)[0]
                    elif size == 8: rec['value'] = struct.unpack('<q', payload)[0]
                elif typ == 5 and size >= 4:
                    slen = struct.unpack_from('<I', payload)[0]
                    rec['value'] = payload[4:4+slen].decode('utf-8','replace')
                pos = hdr_end + size
        return out

def fmt(rec, indent=0, f=sys.stdout):
    pad = '  ' * indent
    if rec['type'] == 2 or 'children' in rec:
        cnt = f" count={rec['count']}" if 'count' in rec else ''
        f.write(f"{pad}{rec['name']} {{  # t{rec['type']} off={rec['off']:#x}{cnt}\n")
        for c in rec['children']:
            fmt(c, indent+1, f)
        f.write(f"{pad}}}\n")
    else:
        v = rec.get('value')
        if v is None:
            v = rec['data'].hex(' ')
        f.write(f"{pad}{rec['name']} = {v!r}  (t{rec['type']}, off={rec['off']:#x}, sz={rec['size']})\n")

if __name__ == '__main__':
    raw = open(sys.argv[1], 'rb').read()
    s = Ser(raw)
    top = []
    s.parse(0x19, 0x19 + s.stream_len, out=top)
    want = sys.argv[2] if len(sys.argv) > 2 else None
    def walk(recs, path=''):
        for r in recs:
            p = path + '/' + r['name']
            if want and r['name'] == want:
                fmt(r)
                print('PATH:', p)
            if r['type'] == 2:
                walk(r['children'], p)
    if want:
        walk(top)
    else:
        for r in top:
            print(f"{r['name']}  (t{r['type']}, off={r['off']:#x}, sz={r['size']})")
