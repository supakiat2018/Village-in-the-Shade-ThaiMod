#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_whistle.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ whistle.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_whistle.py whistle.dat whistle_ตารางคำแปลไทย_PUA.csv [out.dat]

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=11, [1]=ผลรวม rec_size=3300 (=11*300), [2]=blob_size=4326
Record: ทุกเรคคอร์ด rec_size=300 (75 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*304
BLOB_BASE = 12 + 11*304 = 3356 (0xD1C)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ไอดี (1..11)       w[1] = 0
    w[2,3]    key WHISTLE_ID_*
    w[4,5]    JP   <-- ช่องที่ฉีด (ภาษาเริ่มที่ w[4,5] ตรงตามที่ระบุ)
    w[6,7]    EN      w[8,9] FR      w[10,11] ES
    w[12,13]  ZH      w[14,15] KO    w[16,17] ZH(เต็ม)
    w[18..24] ตัวเลข (เช่น 6000+i, 8001..8006, 1153..)  ห้ามแตะ
    w[25,26]  "whistle" (ชนิด; เฉพาะ rec 0,1,4,9)   w[27,28] ชื่อ id ภายใน เช่น call_dog
              (เป็นตัวระบุของเกม ไม่ใช่ข้อความแสดงผล ห้ามแปล/แตะ)
    w[29,30], w[43,44], w[57,58]  ข้อความ placeholder "あいうえお...全２５文字" (ไม่แตะ)
    ที่เหลือเป็นพอยน์เตอร์ไปสตริงว่าง/ตัวเลข

offset JP เดิม (นับจาก BLOB_BASE):
    rec0 20   rec1 424  rec2 859  rec3 1264 rec4 1609 rec5 2026
    rec6 2405 rec7 2782 rec8 3155 rec9 3522 rec10 3931
(สคริปต์ตรวจ key / ชื่อ_JP / ชื่อ_EN กับตาราง CSV ทุกแถวก่อนแก้ไฟล์)
"""
import csv
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY, SLOT_JP, SLOT_EN = 2, 4, 6


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


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    dat, csvp = Path(sys.argv[1]), Path(sys.argv[2])
    outp = Path(sys.argv[3]) if len(sys.argv) > 3 else dat.with_name("whistle_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_key = {r["Whistle_ID"]: r for r in rows}
    assert len(rows) == cnt == len(by_key), f"CSV {len(rows)} แถว / .dat {cnt} เรคคอร์ด / key ไม่ซ้ำ {len(by_key)}"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = []
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 300, f"rec {i}: rec_size {r['size']} != 300"
        key = rd(orig, base, w[2], w[3])
        assert key in by_key, f"rec {i}: key {key!r} ไม่มีในตาราง"
        row = by_key[key]
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        assert jp == row["ชื่อ_JP"], f"rec {i}: JP {jp!r} != {row['ชื่อ_JP']!r}"
        assert en == row["ชื่อ_EN"], f"rec {i}: EN {en!r} != {row['ชื่อ_EN']!r}"
        assert row["ชื่อ_PUA"], f"rec {i}: ช่อง PUA ว่าง"
        plan.append(row["ชื่อ_PUA"])
        print(f"rec {i:2d} JP w[4,5]=({w[4]},{w[5]}) {key:32s} {jp}")

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    for i, th in enumerate(plan):
        b = th.encode("utf-8")
        struct.pack_into("<II", out, recs[i]["pos"] + 4 + SLOT_JP * 4, cur, len(b))
        tail += b + b"\0"
        print(f"rec {i:2d} -> new_off={cur} new_len={len(b)}")
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
        for k in range(2, 18, 2):  # key, EN, FR, ES, ZH, KO, ZH เดิมอ่านได้เท่าเดิม
            if k != SLOT_JP:
                assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[4,5], ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
