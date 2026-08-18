#!/usr/bin/env python3
"""YKCMP_V1 (NIS) save (de)compressor. Type 8 = raw LZ4 block."""
import struct, sys

def lz4_decompress(src, expected=None):
    dst = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]; i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]; i += 1
                lit += b
                if b != 255: break
        dst += src[i:i+lit]; i += lit
        if i >= n: break  # last block ends with literals
        off = src[i] | (src[i+1] << 8); i += 2
        mlen = (token & 15) + 4
        if (token & 15) == 15:
            while True:
                b = src[i]; i += 1
                mlen += b
                if b != 255: break
        pos = len(dst) - off
        for _ in range(mlen):
            dst.append(dst[pos]); pos += 1
        if expected and len(dst) >= expected: break
    return bytes(dst)

def lz4_compress(src):
    # Valid LZ4 block: real data as literals, trailing zero-fill as RLE match
    # (offset=1). Final sequence is literal-only per spec.
    end = len(src)
    while end > 0 and src[end-1] == 0:
        end -= 1
    data = src[:end]
    zeros = len(src) - end
    out = bytearray()
    def put_litlen(token_high, lit):
        if lit < 15:
            out.append((lit << 4) | token_high)
        else:
            out.append(0xF0 | token_high)
            rem = lit - 15
            while rem >= 255:
                out.append(255); rem -= 255
            out.append(rem)
    if zeros < 32:
        # no zero tail worth compressing: single literal-only sequence
        put_litlen(0, len(src))
        out += src
        return bytes(out)
    # seq1: literals = data + one zero byte, match offset=1 len=(zeros-1-tail)
    tail = 16  # final literal-only run
    lit = data + b'\x00'
    mlen = zeros - 1 - tail
    ml_token = 15 if mlen - 4 >= 15 else mlen - 4
    if len(lit) < 15:
        out.append((len(lit) << 4) | ml_token)
    else:
        out.append(0xF0 | ml_token)
        rem = len(lit) - 15
        while rem >= 255:
            out.append(255); rem -= 255
        out.append(rem)
    out += lit
    out += b'\x01\x00'  # match offset = 1
    if ml_token == 15:
        rem = mlen - 4 - 15
        while rem >= 255:
            out.append(255); rem -= 255
        out.append(rem)
    # final sequence: literal-only zeros
    put_litlen(0, tail)
    out += b'\x00' * tail
    return bytes(out)

def unpack(path, outpath):
    data = open(path, 'rb').read()
    assert data[:8] == b'YKCMP_V1', 'not YKCMP'
    typ, csize, dsize = struct.unpack_from('<III', data, 8)
    print(f'type={typ} compressed={csize:#x} decompressed={dsize:#x}')
    assert typ == 8, f'only type 8 (LZ4) supported, got {typ}'
    raw = lz4_decompress(data[0x14:csize], dsize)
    print(f'decompressed {len(raw)} bytes')
    open(outpath, 'wb').write(raw)

def pack(path, outpath, padto=None):
    raw = open(path, 'rb').read()
    comp = lz4_compress(raw)
    hdr = b'YKCMP_V1' + struct.pack('<III', 8, len(comp) + 0x14, len(raw))
    blob = hdr + comp
    if padto and len(blob) < padto:
        blob += b'\0' * (padto - len(blob))
    open(outpath, 'wb').write(blob)
    print(f'packed {len(raw)} -> {len(blob)} bytes')

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'unpack':
        unpack(sys.argv[2], sys.argv[3])
    elif cmd == 'pack':
        pad = int(sys.argv[4], 0) if len(sys.argv) > 4 else None
        pack(sys.argv[2], sys.argv[3], pad)
