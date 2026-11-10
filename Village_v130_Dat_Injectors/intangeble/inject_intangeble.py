#!/usr/bin/env python3
"""Safe Append & Re-point injector for intangeble.dat (Village in the Shade PC v1.30).
Fixed rec_size=116 (29 words). Key=w[2,3], JP slot=w[4,5] (re-pointed), EN=w[6,7] untouched.
CSV rows (422) match records 0..421 by position, cross-checked by Key + JP.
Record 422 (INTANGEBLE_ID_RELEASE_SEEDER, new in v1.30) is not in the CSV; its Thai_PUA is supplied below.
usage: inject_intangeble.py in.dat table.csv out.dat"""
import struct, csv, sys
src, csvp, dst = sys.argv[1:4]
EXTRA = {422: ("INTANGEBLE_ID_RELEASE_SEEDER", "種まき機を入手した！",
               "ไบเคองหานเมดแว!")}
d = open(src, 'rb').read()
n, psum, bsz = struct.unpack_from('<3I', d, 0)
base = len(d) - bsz
assert base == 12 + n*4 + psum, "BLOB_BASE mismatch"
rows = list(csv.DictReader(open(csvp, encoding='utf-8-sig', newline='')))
assert len(rows) + len(EXTRA) == n, "row count mismatch"
S = lambda w, i: d[base+w[i]:base+w[i]+w[i+1]].decode('utf-8')
out = bytearray(d[:base]); blob = bytearray(d[base:]); p = 12; done = 0
for i in range(n):
    sz = struct.unpack_from('<I', d, p)[0]; assert sz == 116
    w = struct.unpack_from('<29I', d, p+4)
    if i in EXTRA: key, jp, th = EXTRA[i]
    else: r = rows[i]; key, jp, th = r['Key'], r['ต้นฉบับ_JP'], r['Thai_PUA']
    assert S(w, 2) == key and S(w, 4) == jp, f"mismatch at {i}"
    b = th.encode('utf-8'); assert b, f"empty Thai_PUA at {i}"
    new_off = len(blob); blob += b + b'\0'
    struct.pack_into('<2I', out, p + 4 + 4*4, new_off, len(b))   # only w[4], w[5]
    done += 1; p += 4 + sz
assert p == base
struct.pack_into('<I', out, 8, len(blob))     # header[2] = blob_size
open(dst, 'wb').write(bytes(out) + bytes(blob))
print(f"injected={done} blob {bsz}->{len(blob)} size {len(d)}->{len(out)+len(blob)}")
