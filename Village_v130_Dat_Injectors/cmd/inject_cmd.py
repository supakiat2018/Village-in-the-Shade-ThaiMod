#!/usr/bin/env python3
"""Safe Append & Re-point injector for cmd.dat (Village in the Shade PC v1.30).
Variable-size records; Key=w[2,3], JP slot=w[7,8] (re-pointed), EN=w[9,10] untouched.
Matching is by position (1:1) and cross-checked by Key + JP + EN against the CSV.
usage: inject_cmd.py in.dat table.csv out.dat"""
import struct, csv, sys
src, csvp, dst = sys.argv[1:4]
d = open(src, 'rb').read()
n, psum, bsz = struct.unpack_from('<3I', d, 0)
base = len(d) - bsz
assert base == 12 + n*4 + psum, "BLOB_BASE mismatch"
rows = list(csv.DictReader(open(csvp, encoding='utf-8-sig', newline='')))
assert len(rows) == n, "row count != record count"
S = lambda w, i: d[base+w[i]:base+w[i]+w[i+1]].decode('utf-8')
out = bytearray(d[:base]); blob = bytearray(d[base:]); p = 12; done = skipped = 0
for i in range(n):
    sz = struct.unpack_from('<I', d, p)[0]
    w = struct.unpack_from('<%dI' % (sz//4), d, p+4)
    r = rows[i]
    assert int(r['Index']) == i and S(w, 2) == r['Key'] and S(w, 7) == r['ต้นฉบับ_JP'] and S(w, 9) == r['MODEN_EN'], f"mismatch at {i}"
    th = r['Thai_PUA']
    if r['Status'] == 'Empty_Untouched' or not th:
        assert w[8] == 0; skipped += 1     # keep EMPTY as-is
    else:
        b = th.encode('utf-8'); new_off = len(blob); blob += b + b'\0'
        struct.pack_into('<2I', out, p + 4 + 7*4, new_off, len(b))   # only w[7], w[8]
        done += 1
    p += 4 + sz
assert p == base
struct.pack_into('<I', out, 8, len(blob))     # header[2] = blob_size
open(dst, 'wb').write(bytes(out) + bytes(blob))
print(f"injected={done} untouched={skipped} blob {bsz}->{len(blob)} size {len(d)}->{len(out)+len(blob)}")
