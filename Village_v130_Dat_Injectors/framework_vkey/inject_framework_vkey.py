#!/usr/bin/env python3
"""Safe Append & Re-point injector for framework_vkey.dat (Village in the Shade v1.30).
usage: inject_framework_vkey.py in.dat pua.csv out.dat"""
import struct, csv, sys
src, csvp, dst = sys.argv[1:4]
d = open(src, 'rb').read()
n, psum, bsz = struct.unpack_from('<3I', d, 0)
base = len(d) - bsz
assert base == 12 + n*4 + psum, "BLOB_BASE mismatch"
recs, p = [], 12
for _ in range(n):
    sz = struct.unpack_from('<I', d, p)[0]; assert sz == 96
    recs.append(p + 4); p += 4 + sz
assert p == base
tbl = {}
with open(csvp, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        assert r['id'] not in tbl; tbl[int(r['id'])] = r
        assert len(r['th_pua'].encode('utf-8')) == int(r['bytes']), r['id']
blob = bytearray(d[base:]); out = bytearray(d[:base]); done = skipped = 0; used = set()
for off in recs:
    w = list(struct.unpack_from('<24I', d, off))
    r = tbl.get(w[0])
    if r is None: skipped += 1; continue      # EMPTY / not in table: untouched
    b = r['th_pua'].encode('utf-8')
    new_off = len(blob); blob += b + b'\0'
    struct.pack_into('<2I', out, off + 6*4, new_off, len(b))   # only w[6], w[7]
    used.add(w[0]); done += 1
assert used == set(tbl), set(tbl) - used
struct.pack_into('<I', out, 8, len(blob))     # header[2] = blob_size
open(dst, 'wb').write(bytes(out) + bytes(blob))
print(f"injected={done} untouched={skipped} blob {bsz}->{len(blob)} size {len(d)}->{len(out)+len(blob)}")
