#!/usr/bin/env python3
"""YKCMP_V1 (NIS) save (de)compressor. Types 4 and 8."""
import struct, sys

try:
    import lz4.block as _lz4_block
except ImportError:  # pure-python fallback still works, just compresses worse
    _lz4_block = None


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


def type4_decompress(src, expected):
    """Decode the original YKCMP LZ codec used by save.lst."""
    out = bytearray()
    pos = 0
    while pos < len(src) and len(out) < expected:
        opcode = src[pos]
        pos += 1
        if opcode < 0x80:
            length = opcode
            if pos + length > len(src):
                raise ValueError('YKCMP type 4 literal exceeds input')
            out.extend(src[pos:pos + length])
            pos += length
            continue
        if opcode < 0xc0:
            length = ((opcode >> 4) & 3) + 1
            distance = (opcode & 15) + 1
        elif opcode < 0xe0:
            if pos >= len(src):
                raise ValueError('truncated YKCMP type 4 back-reference')
            length = opcode - 0xc0 + 2
            distance = src[pos] + 1
            pos += 1
        else:
            if pos + 2 > len(src):
                raise ValueError('truncated YKCMP type 4 long back-reference')
            arg1, arg2 = src[pos], src[pos + 1]
            pos += 2
            length = ((opcode - 0xe0) << 4) + (arg1 >> 4) + 3
            distance = ((arg1 & 15) << 8) + arg2 + 1
        if distance > len(out):
            raise ValueError('invalid YKCMP type 4 back-reference')
        for _ in range(length):
            out.append(out[-distance])
    if len(out) != expected or pos != len(src):
        raise ValueError(f'YKCMP type 4 size mismatch: {len(out)} != {expected}')
    return bytes(out)


def type4_compress(src):
    """Greedy encoder for the original YKCMP LZ codec."""
    src = bytes(src)
    out = bytearray()
    literals = bytearray()

    def flush():
        while literals:
            length = min(len(literals), 0x7f)
            out.append(length)
            out.extend(literals[:length])
            del literals[:length]

    pos = 0
    while pos < len(src):
        best_length = 0
        best_distance = 0
        start = max(0, pos - 4096)
        for candidate in range(pos - 1, start - 1, -1):
            distance = pos - candidate
            length = 0
            while (length < 514 and pos + length < len(src)
                   and src[candidate + length % distance] == src[pos + length]):
                length += 1
            if length > best_length:
                best_length, best_distance = length, distance
        if best_length >= 3 or (best_length >= 2 and best_distance <= 256):
            flush()
            if best_distance <= 16 and best_length <= 4:
                use = best_length
                out.append(0x80 | ((use - 1) << 4) | (best_distance - 1))
            elif best_distance <= 256 and best_length <= 33:
                use = best_length
                out.extend((0xc0 + use - 2, best_distance - 1))
            else:
                use = min(best_length, 514)
                value = use - 3
                out.extend((0xe0 + (value >> 4),
                            ((value & 15) << 4) | ((best_distance - 1) >> 8),
                            (best_distance - 1) & 0xff))
            pos += use
        else:
            literals.append(src[pos])
            pos += 1
            if len(literals) == 0x7f:
                flush()
    flush()
    return bytes(out)


def decompress_container(data):
    if data[:8] != b'YKCMP_V1':
        raise ValueError('not a YKCMP_V1 container')
    typ, csize, dsize = struct.unpack_from('<III', data, 8)
    payload = data[0x14:csize]
    if typ == 4:
        return typ, type4_decompress(payload, dsize)
    if typ == 8:
        return typ, lz4_decompress(payload, dsize)
    raise ValueError(f'unsupported YKCMP type {typ}')


def compress_container(raw, typ=4):
    if typ == 4:
        payload = type4_compress(raw)
    elif typ == 8:
        payload = lz4_compress(raw)
    else:
        raise ValueError(f'unsupported YKCMP type {typ}')
    return b'YKCMP_V1' + struct.pack('<III', typ, len(payload) + 0x14,
                                      len(raw)) + payload

def lz4_compress(src):
    # Prefer the real LZ4 library (raw block, high compression) -- required for
    # long-play saves whose data would not fit the fixed file size with the
    # fallback literal+zero-RLE encoder below.
    if _lz4_block is not None:
        return _lz4_block.compress(bytes(src), mode='high_compression',
                                   store_size=False)
    return _lz4_compress_fallback(src)


def _lz4_compress_fallback(src):
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
