#!/usr/bin/env python3
"""Safe Append & Re-point injector for gamesetting.dat (PC Steam v1.30).

usage: inject_gamesetting.py <gamesetting.dat> <translation.csv> <out.dat> [--include-nonjp-slots]

Layout: Header 12B <num_records, sum_records, blob_size> LE | records | blob
Record: uint32 rec_size, then uint32 words w[]; w[2,3] = Key (SETTING_*).
Text is stored as 7-language groups of 14 words (7 x (offset,length)): JP, EN, FR, ES, zh-TW, KO, zh-CN.

Matching (as agreed): scan every (offset,length) pointer pair in each record whose blob string is
null-terminated and equals a CSV `ต้นฉบับ_JP` text; the hits, in file order, must equal the CSV rows 1:1
(Index order) -- the script aborts otherwise. Each hit is classified as a true JP slot (first pair of a
7-string contiguous group) or not. Only JP slots are re-pointed by default; hits that sit in another
language's slot (they hold Japanese text there) are left untouched unless --include-nonjp-slots is given.
CSV columns used: ต้นฉบับ_JP, Thai_PUA. Header[2] (blob_size) is updated.
"""
import sys, csv, struct

def main(dat_p, csv_p, out_p, include_nonjp=False):
    d = bytearray(open(dat_p, 'rb').read())
    n, sum_rec, bs = struct.unpack('<III', d[:12])
    rec_end = len(d) - bs
    blob = bytes(d[rec_end:])
    assert blob[-1] == 0
    rows = list(csv.DictReader(open(csv_p, newline='', encoding='utf-8-sig')))
    rows.sort(key=lambda r: int(r['Index']))
    jpset = {r['ต้นฉบับ_JP'] for r in rows}

    hits = []   # (word_abs_pos, key, text, is_jp_slot)
    pos = 12
    for k in range(n):
        rs = struct.unpack_from('<I', d, pos)[0]; base = pos + 4
        w = struct.unpack_from('<%dI' % (rs // 4), d, base)
        key = blob[w[2]:w[2] + w[3]].decode('utf-8')
        starts = set(); i = 4
        while i + 13 < len(w):
            if w[i + 1] > 0 and all(w[i + 2*j + 2] == w[i + 2*j] + w[i + 2*j + 1] + 1 for j in range(6)):
                starts.add(i); i += 14
            else:
                i += 1
        for i in range(4, len(w) - 1):
            o, l = w[i], w[i + 1]
            if 0 < l < 4096 and o + l < bs and blob[o + l] == 0 and (o == 0 or blob[o - 1] == 0):
                t = blob[o:o + l].decode('utf-8', 'replace')
                if t in jpset:
                    hits.append((base + i * 4, key, t, i in starts))
        pos = base + rs
    assert pos == rec_end, 'record region does not end at blob start'
    assert len(hits) == len(rows), f'{len(hits)} pointer hits vs {len(rows)} CSV rows'
    for h, r in zip(hits, rows):
        assert h[2] == r['ต้นฉบับ_JP'], f'order mismatch at Index {r["Index"]}: {h[2]!r} vs {r["ต้นฉบับ_JP"]!r}'

    new = bytearray(); cache = {}; patched = skipped = 0
    for (wp, key, t, is_jp), r in zip(hits, rows):
        if not is_jp and not include_nonjp:
            skipped += 1; print(f'  skip non-JP slot: {key} word@{wp} {t!r}'); continue
        th = r['Thai_PUA']; assert th.strip(), f'empty Thai_PUA at Index {r["Index"]}'
        if th not in cache:
            e = th.encode('utf-8'); cache[th] = (bs + len(new), len(e)); new.extend(e + b'\x00')
        struct.pack_into('<II', d, wp, *cache[th]); patched += 1

    struct.pack_into('<I', d, 8, bs + len(new))
    out = bytes(d) + bytes(new)
    open(out_p, 'wb').write(out)
    print(f'{n} records, {patched} slots patched, {skipped} non-JP slots left untouched, '
          f'{len(cache)} unique strings, blob {bs} -> {bs+len(new)}, size {len(out)}')

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(*a[:3], include_nonjp='--include-nonjp-slots' in sys.argv)
