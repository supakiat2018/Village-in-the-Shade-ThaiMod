#!/usr/bin/env python3
"""Safe Append & Re-point injector for gameeffect.dat (PC Steam v1.30).

usage: inject_gameeffect.py <gameeffect.dat> <translation_PUA.csv> <out.dat>

Layout: Header 12B <num_records, sum_records, blob_size> LE | records | blob
Record: uint32 rec_size, then rec_size bytes = uint32 words w[0..]
  w[2,3]=Key(Effect_ID)  w[4,5]=Name JP slot  w[6,7]=Description JP slot  (offset,length into blob)
CSV columns used: Effect_ID, ชื่อ_JP, คำอธิบาย_JP, ชื่อ_PUA, คำอธิบาย_PUA (rows 1:1 with records, in order)
Only w[4,5] and w[6,7] are rewritten; Header[2] (blob_size) is updated. Everything else is untouched.
"""
import sys, csv, struct

def main(dat_p, csv_p, out_p):
    d = bytearray(open(dat_p, 'rb').read())
    n, sum_rec, bs = struct.unpack('<III', d[:12])
    rec_end = len(d) - bs
    blob = bytes(d[rec_end:])
    assert blob[-1] == 0 or bs == 0
    rows = list(csv.DictReader(open(csv_p, newline='', encoding='utf-8-sig')))
    assert len(rows) == n, f'CSV rows {len(rows)} != records {n}'

    new = bytearray(); cache = {}
    def put(text):
        if text not in cache:
            e = text.encode('utf-8')
            cache[text] = (bs + len(new), len(e))
            new.extend(e + b'\x00')
        return cache[text]
    def s(off, ln): return blob[off:off + ln].decode('utf-8')

    pos = 12
    for k in range(n):
        rs = struct.unpack_from('<I', d, pos)[0]
        base = pos + 4
        w = list(struct.unpack_from('<%dI' % (rs // 4), d, base))
        r = rows[k]
        assert s(w[2], w[3]) == r['Effect_ID'], f'rec {k}: key mismatch'
        assert s(w[4], w[5]) == r['ชื่อ_JP'], f'rec {k}: name JP mismatch'
        assert s(w[6], w[7]) == r['คำอธิบาย_JP'], f'rec {k}: desc JP mismatch'
        for slot, col in ((4, 'ชื่อ_PUA'), (6, 'คำอธิบาย_PUA')):
            t = r[col]
            assert t.strip(), f'rec {k}: empty {col}'
            o, l = put(t)
            struct.pack_into('<II', d, base + slot * 4, o, l)
        pos = base + rs
    assert pos == rec_end, 'record region does not end at blob start'

    struct.pack_into('<I', d, 8, bs + len(new))
    out = bytes(d) + bytes(new)
    open(out_p, 'wb').write(out)
    print(f'{n} records patched, {len(cache)} unique strings, blob {bs} -> {bs+len(new)}, size {len(out)}')

if __name__ == '__main__':
    main(*sys.argv[1:4])
