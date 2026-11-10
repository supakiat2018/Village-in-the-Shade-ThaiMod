#!/usr/bin/env python3
"""Safe Append & Re-point injector for updatetext.dat (Village in the Shade PC v1.30).
Record: w[2,3]=Key, w[4]=line count, line i has 7 language pointer pairs (stride 14 words),
JP slot = w[5+14*i], w[6+14*i] (re-pointed); EN = w[7+14*i, 8+14*i] and others untouched.
Only lines listed in the CSV (matched by Record_Key + Line_Index + Original_JP) are changed;
<space> / empty lines are left as-is.
usage: inject_updatetext.py in.dat table.csv out.dat   (table = *_PUA.csv)"""
import struct, csv, sys
src, csvp, dst = sys.argv[1:4]
d = open(src, 'rb').read()
n, psum, bsz = struct.unpack_from('<3I', d, 0)
base = len(d) - bsz
assert base == 12 + n*4 + psum, "BLOB_BASE mismatch"
rows = list(csv.DictReader(open(csvp, encoding='utf-8-sig', newline='')))
S = lambda w, i: d[base+w[i]:base+w[i]+w[i+1]].decode('utf-8')
recs, p = {}, 12
for _ in range(n):
    sz = struct.unpack_from('<I', d, p)[0]
    w = struct.unpack_from('<%dI' % (sz//4), d, p+4)
    recs[S(w, 2)] = (p + 4, w); p += 4 + sz
assert p == base
out = bytearray(d[:base]); blob = bytearray(d[base:]); done = 0; seen = set()
for r in rows:
    key, li = r['Record_Key'], int(r['Line_Index'])
    pos, w = recs[key]
    assert 0 <= li < w[4] and (key, li) not in seen
    seen.add((key, li))
    assert S(w, 5 + 14*li) == r['Original_JP'], f"JP mismatch {key}#{li}"
    b = r['Thai_PUA'].encode('utf-8'); assert b
    new_off = len(blob); blob += b + b'\0'
    struct.pack_into('<2I', out, pos + 4*(5 + 14*li), new_off, len(b))   # only JP offset/length
    done += 1
struct.pack_into('<I', out, 8, len(blob))     # header[2] = blob_size
open(dst, 'wb').write(bytes(out) + bytes(blob))
print(f"injected={done} blob {bsz}->{len(blob)} size {len(d)}->{len(out)+len(blob)}")
