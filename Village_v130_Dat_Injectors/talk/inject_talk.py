#!/usr/bin/env python3
"""Safe Append & Re-point injector for talk.dat (v1.30).

usage: inject_talk.py <talk.dat> <translation.csv> <offsets.csv> <out.dat>
  translation.csv : columns Index, Key, ต้นฉบับ_JP, ..., คำแปลไทย_PUA
  offsets.csv     : columns Index, TALK_ID, Offset_Hex, Japanese  (blob-relative offset of the JP string)
Rows are joined by Index; Key/JP are cross-checked. Header: <num_records,sum_records,blob_size> LE.
"""
import sys, csv, struct

def main(dat_p, tr_p, off_p, out_p):
    d = open(dat_p, 'rb').read()
    n, s, bs = struct.unpack('<III', d[:12])
    rt = len(d) - 12 - bs
    blob = d[12 + rt:]
    assert len(blob) == bs and blob[-1] == 0
    table = bytearray(d[12:12 + rt])

    tr = {r['Index']: r for r in csv.DictReader(open(tr_p, newline='', encoding='utf-8-sig'))}
    offs = list(csv.DictReader(open(off_p, newline='', encoding='utf-8-sig')))
    jobs = {}
    for o in offs:
        r = tr[o['Index']]
        assert r['Key'] == o['TALK_ID'], f"Key mismatch at Index {o['Index']}"
        off = int(o['Offset_Hex'], 16)
        assert off not in jobs and 0 <= off < bs
        end = blob.find(b'\x00', off)
        jobs[off] = (end - off, r['คำแปลไทย_PUA'])
    assert len(jobs) == len(tr), 'row count mismatch'

    words = struct.unpack('<%dI' % (rt // 4), bytes(table[:(rt // 4) * 4]))
    slots = {}
    for i in range(len(words) - 1):
        o = words[i]
        if o in jobs and words[i + 1] == jobs[o][0]:
            slots[o] = i
    missing = set(jobs) - set(slots)
    assert not missing, f'{len(missing)} offsets without a matching (offset,length) pointer'

    new = bytearray(); cache = {}
    for o, i in slots.items():
        t = jobs[o][1]
        if t not in cache:
            e = t.encode('utf-8')
            cache[t] = (bs + len(new), len(e))
            new += e + b'\x00'
        no, nl = cache[t]
        struct.pack_into('<II', table, i * 4, no, nl)

    out = struct.pack('<III', n, s, bs + len(new)) + bytes(table) + blob + bytes(new)
    assert out[12 + rt:12 + rt + bs] == blob
    open(out_p, 'wb').write(out)
    print(f'patched {len(slots)} pointer pairs, {len(cache)} unique strings, blob {bs} -> {bs+len(new)}, size {len(out)}')

if __name__ == '__main__':
    main(*sys.argv[1:5])
