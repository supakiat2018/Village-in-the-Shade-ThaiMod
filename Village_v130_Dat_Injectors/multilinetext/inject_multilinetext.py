#!/usr/bin/env python3
"""Safe Append & Re-point injector for multilinetext.dat (PC Steam v1.30).

usage: inject_multilinetext.py <multilinetext.dat> <translation_PUA.csv> <out.dat>

Layout: Header 12B <num_records, sum_records, blob_size> LE | records | blob
Record: uint32 rec_size, then rec_size bytes = uint32 words w[]
  w[2,3]  = Key (Record_Key)
  w[4]    = number of lines N
  line n (1-based): JP slot = w[5+(n-1)*14], w[6+(n-1)*14]   (offset, length into blob)
                    next slot (w[7+(n-1)*14], ...) is EN and is left untouched
CSV columns used: Record_Key, Line_Index, Original_JP, Thai_PUA
Only the JP (offset,length) pair of each line is rewritten; Header[2] (blob_size) is updated.
"""
import sys, csv, struct

def main(dat_p, csv_p, out_p):
    d = bytearray(open(dat_p, 'rb').read())
    n, sum_rec, bs = struct.unpack('<III', d[:12])
    rec_end = len(d) - bs
    blob = bytes(d[rec_end:])
    assert blob[-1] == 0
    rows = list(csv.DictReader(open(csv_p, newline='', encoding='utf-8-sig')))
    by = {(r['Record_Key'], int(r['Line_Index'])): r for r in rows}
    assert len(by) == len(rows), 'duplicate (Record_Key, Line_Index) in CSV'

    new = bytearray(); cache = {}
    def put(t):
        if t not in cache:
            e = t.encode('utf-8'); cache[t] = (bs + len(new), len(e)); new.extend(e + b'\x00')
        return cache[t]

    pos = 12; used = 0
    for k in range(n):
        rs = struct.unpack_from('<I', d, pos)[0]; base = pos + 4
        w = struct.unpack_from('<%dI' % (rs // 4), d, base)
        key = blob[w[2]:w[2] + w[3]].decode('utf-8')
        N = w[4]
        assert 5 + (N - 1) * 14 + 1 < len(w), f'{key}: line count {N} exceeds record'
        for i in range(1, N + 1):
            o_i = 5 + (i - 1) * 14
            jp = blob[w[o_i]:w[o_i] + w[o_i + 1]].decode('utf-8')
            r = by[(key, i)]
            assert jp == r['Original_JP'], f'{key} line {i}: JP mismatch {jp!r} vs {r["Original_JP"]!r}'
            assert r['Thai_PUA'].strip(), f'{key} line {i}: empty Thai_PUA'
            o, l = put(r['Thai_PUA'])
            struct.pack_into('<II', d, base + o_i * 4, o, l)
            used += 1
        pos = base + rs
    assert pos == rec_end and used == len(rows), f'used {used} of {len(rows)} CSV rows'

    struct.pack_into('<I', d, 8, bs + len(new))
    out = bytes(d) + bytes(new)
    open(out_p, 'wb').write(out)
    print(f'{n} records, {used} lines patched, {len(cache)} unique strings, blob {bs} -> {bs+len(new)}, size {len(out)}')

if __name__ == '__main__':
    main(*sys.argv[1:4])
