#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_framework_vkeycategory.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ framework_vkeycategory.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_framework_vkeycategory.py framework_vkeycategory.dat framework_vkeycategory_ตารางคำแปลไทย_PUA.csv [out.dat] [--mapping Mapping.json]

    --mapping Mapping.json  (ไม่บังคับ) ตรวจเพิ่มว่า Thai_PUA ในตาราง = Thai_Final แปลงผ่าน Mapping.json แล้วได้ข้อความเดียวกัน

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian) -- รูปแบบเดียวกับ bundlegroup.dat
---------------------------------------------
Header 12 ไบต์: [0]=count=4, [1]=ผลรวม rec_size=336 (=4*84), [2]=blob_size=426
Record: ทุกเรคคอร์ด rec_size=84 (21 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*88
BLOB_BASE = 12 + 4*88 = 364 (0x16C)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      Category ID (1..4)     w[1] = 0
    w[2,3]    key VKEY_CATEGORY_*
    w[4,5]    tag ภาษาญี่ปุ่นภายใน (ข้อความเหมือน JP แต่ offset คนละที่)  ไม่แตะ
    w[6]      ตัวเลข (1,0,2,3) ไม่ใช่พอยน์เตอร์ ไม่แตะ
    w[7,8]    JP   <-- ช่องที่ฉีด
    w[9,10]   EN    w[11,12] FR    w[13,14] ZH    w[15,16] ZH(เต็ม)    w[17,18] KO
    w[19,20]  (offset,0) สตริงว่าง

offset JP เดิม (นับจาก BLOB_BASE): rec0=29, rec1=110, rec2=219, rec3=333
(w[4,5] เดิม: 22, 94, 203, 317 -- ไม่แตะ)
"""
import csv
import json
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY, SLOT_TAG, SLOT_JP, SLOT_EN = 2, 4, 7, 9
CHECK_SLOTS = (2, 4, 9, 11, 13, 15, 17)  # key, tag, EN, FR, ZH, ZH, KO ต้องอ่านได้เท่าเดิมหลังฉีด


def parse(d):
    cnt, tot, bs = struct.unpack_from("<III", d, 0)
    recs, p = [], HDR
    for _ in range(cnt):
        rs = struct.unpack_from("<I", d, p)[0]
        recs.append({"pos": p, "size": rs, "w": list(struct.unpack_from("<%dI" % (rs // 4), d, p + 4))})
        p += 4 + rs
    assert tot == sum(r["size"] for r in recs), "Header[1] ไม่เท่าผลรวม rec_size"
    assert len(d) == p + bs, "ขนาดไฟล์ไม่ตรง blob_size"
    return cnt, tot, bs, recs, p


def rd(d, base, off, ln):
    assert d[base + off + ln] == 0, "สตริงไม่ลงท้าย \\0"
    return d[base + off: base + off + ln].decode("utf-8")


def to_pua(s, m):
    out, i = [], 0
    while i < len(s):
        for n in (3, 2):
            k = s[i:i + n]
            if len(k) == n and k in m:
                out.append(m[k]); i += n; break
        else:
            out.append(s[i]); i += 1
    return "".join(out)


def main():
    argv = sys.argv[1:]
    mapping = None
    if "--mapping" in argv:
        j = argv.index("--mapping")
        mapping = json.load(open(argv[j + 1], encoding="utf-8"))
        del argv[j:j + 2]
    if len(argv) < 2:
        print(__doc__); sys.exit(1)
    dat, csvp = Path(argv[0]), Path(argv[1])
    outp = Path(argv[2]) if len(argv) > 2 else dat.with_name("framework_vkeycategory_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_key = {r["Key"]: r for r in rows}
    assert len(rows) == cnt == len(by_key), f"CSV {len(rows)} แถว / .dat {cnt} เรคคอร์ด / key ไม่ซ้ำ {len(by_key)}"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = []
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 84, f"rec {i}: rec_size {r['size']} != 84"
        key = rd(orig, base, w[SLOT_KEY], w[SLOT_KEY + 1])
        assert key in by_key, f"rec {i}: key {key!r} ไม่มีในตาราง"
        row = by_key[key]
        assert w[0] == int(row["Category_ID"]), f"rec {i}: Category_ID {w[0]} != {row['Category_ID']}"
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        tag = rd(orig, base, w[SLOT_TAG], w[SLOT_TAG + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        assert jp == row["Original_JP"], f"rec {i}: JP {jp!r} != {row['Original_JP']!r}"
        assert en == row["MODEN_EN"], f"rec {i}: EN {en!r} != {row['MODEN_EN']!r}"
        assert w[SLOT_TAG] != w[SLOT_JP], f"rec {i}: tag กับ JP ใช้ offset เดียวกัน"
        th = row["Thai_PUA"]
        assert th, f"rec {i}: Thai_PUA ว่าง"
        if mapping is not None:
            assert to_pua(row["Thai_Final"], mapping) == th, f"rec {i}: Thai_PUA ไม่ตรงกับ Thai_Final ผ่าน Mapping.json"
        plan.append(th)
        print(f"rec {i} id={w[0]} {key:28s} JP w[7,8]=({w[7]},{w[8]}) {jp} | tag w[4,5]=({w[4]},{w[5]}) {tag} | {en}")
    if mapping is not None:
        print("Thai_PUA ตรงกับ Thai_Final ผ่าน Mapping.json ครบทุกแถว")

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    for i, th in enumerate(plan):
        b = th.encode("utf-8")
        struct.pack_into("<II", out, recs[i]["pos"] + 4 + SLOT_JP * 4, cur, len(b))
        tail += b + b"\0"
        print(f"rec {i} -> new_off={cur} new_len={len(b)}")
        cur += len(b) + 1
    out += tail
    struct.pack_into("<I", out, 8, cur)  # Header[2]
    outp.write_bytes(out)
    print(f"ฉีด {len(plan)} สตริง; blob_size {bs} -> {cur}; ไฟล์ {len(orig)} -> {len(out)} ไบต์ -> {outp}")

    # ---------- 3) ตรวจหลังฉีด ----------
    d2 = bytes(out)
    c2, t2, bs2, r2, base2 = parse(d2)
    assert (c2, t2, base2, bs2) == (cnt, tot, base, cur)
    assert d2[base:base + bs] == orig[base:base + bs], "Blob เดิมถูกแก้!"
    for i, (ra, rb) in enumerate(zip(recs, r2)):
        diff = {k for k in range(len(ra["w"])) if ra["w"][k] != rb["w"][k]}
        assert diff <= {SLOT_JP, SLOT_JP + 1} and ra["w"][SLOT_JP] != rb["w"][SLOT_JP], f"rec {i}: {sorted(diff)}"
        assert rd(d2, base2, rb["w"][SLOT_JP], rb["w"][SLOT_JP + 1]) == plan[i]
        for k in CHECK_SLOTS:
            assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[7,8], key/tag/ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
