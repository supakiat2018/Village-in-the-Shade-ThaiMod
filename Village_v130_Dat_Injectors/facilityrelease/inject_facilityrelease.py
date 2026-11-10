#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_facilityrelease.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ facilityrelease.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_facilityrelease.py facilityrelease.dat facilityrelease_ตารางคำแปลไทย_PUA.csv [out.dat] [--no-extra]

    --no-extra  ไม่ฉีดเรคคอร์ดที่ 16 (ADDITIONAL_FARMLAND) คงข้อความเดิมไว้

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=17, [1]=ผลรวม rec_size=1564 (=17*92), [2]=blob_size=5438
Record: ทุกเรคคอร์ด rec_size=92 (23 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*96
BLOB_BASE = 12 + 17*96 = 1644 (0x66C)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ไอดี (1..17)     w[1] = 0
    w[2,3]    key FACILITY_RELEASE_ID_*
    w[4,5]    JP   <-- ช่องที่ฉีด  (ไฟล์นี้ไม่มีช่อง tag คั่น ภาษาเริ่มที่ w[4,5] ตรงตามที่ระบุ)
    w[6,7]    EN      w[8,9] FR      w[10,11] ES
    w[12,13]  ZH      w[14,15] KO    w[16,17] ZH(เต็ม)
    w[18..22] ตัวเลข/แฟลก (ไม่ใช่พอยน์เตอร์ ห้ามแตะ)  เช่น w[18]=3200.. ; rec16 มี w[19]=120

offset JP เดิม (นับจาก BLOB_BASE):
    rec0 34   rec1 418  rec2 818  rec3 1146 rec4 1476 rec5 1766 rec6 2095 rec7 2457
    rec8 2826 rec9 3093 rec10 3399 rec11 3705 rec12 4024 rec13 4350 rec14 4623 rec15 4889
    rec16 5206
(สคริปต์ตรวจ key / jp_orig / EN กับตาราง CSV ทุกแถวก่อนแก้ไฟล์)

เรคคอร์ด 16 (FACILITY_RELEASE_ID_ADDITIONAL_FARMLAND, เพิ่มใน v1.30) ไม่มีในตาราง:
    JP และ EN เหมือน FARMLAND_EXPANTION_1/2 ทุกตัวอักษร สคริปต์จึงใช้ข้อความ PUA ของ
    FARMLAND_EXPANTION_1 (ตรวจก่อนว่า _1 กับ _2 เหมือนกัน)
"""
import csv
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY, SLOT_JP, SLOT_EN = 2, 4, 6
# key ที่ไม่มีในตาราง -> ยืมข้อความจาก key นี้ (ต้อง JP และ EN เหมือนกัน)
EXTRA = {"FACILITY_RELEASE_ID_ADDITIONAL_FARMLAND": "FACILITY_RELEASE_ID_FARMLAND_EXPANTION_1"}
SIBLING_CHECK = {"FACILITY_RELEASE_ID_FARMLAND_EXPANTION_1": "FACILITY_RELEASE_ID_FARMLAND_EXPANTION_2"}


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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_extra = "--no-extra" in sys.argv
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    dat, csvp = Path(args[0]), Path(args[1])
    outp = Path(args[2]) if len(args) > 2 else dat.with_name("facilityrelease_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_key = {r["key"]: r for r in rows}
    assert len(by_key) == len(rows), "key ในตารางซ้ำ"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = {}  # rec index -> ข้อความ PUA
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 92, f"rec {i}: rec_size {r['size']} != 92"
        key = rd(orig, base, w[SLOT_KEY], w[SLOT_KEY + 1])
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        if key in by_key:
            row, note = by_key[key], "ตาราง"
        elif key in EXTRA:
            src = by_key[EXTRA[key]]
            row, note = src, f"ไม่มีในตาราง -> ยืมจาก {EXTRA[key]}"
            assert jp == src["jp_orig"] and en == src["en_moden"], f"rec {i}: JP/EN ไม่เหมือนต้นแบบ"
            sib = by_key[SIBLING_CHECK[EXTRA[key]]]
            assert sib["ข้อความ_PUA"] == src["ข้อความ_PUA"] and sib["jp_orig"] == src["jp_orig"]
            if no_extra:
                print(f"rec {i:2d} {key}: ข้าม (--no-extra)")
                continue
        else:
            raise AssertionError(f"rec {i}: key {key!r} ไม่มีในตารางและไม่อยู่ใน EXTRA")
        assert jp == row["jp_orig"], f"rec {i}: JP ไม่ตรง {jp!r} != {row['jp_orig']!r}"
        assert en == row["en_moden"], f"rec {i}: EN ไม่ตรง {en!r} != {row['en_moden']!r}"
        assert row["ข้อความ_PUA"], f"rec {i}: ช่อง PUA ว่าง"
        plan[i] = row["ข้อความ_PUA"]
        print(f"rec {i:2d} JP w[4,5]=({w[4]},{w[5]}) {key:48s} [{note}]")
    missing = set(by_key) - {rd(orig, base, r["w"][2], r["w"][3]) for r in recs}
    assert not missing, f"แถวในตารางที่ไม่มีใน .dat: {missing}"

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    for i, th in plan.items():
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
        if i in plan:
            assert diff <= {SLOT_JP, SLOT_JP + 1} and ra["w"][SLOT_JP] != rb["w"][SLOT_JP], f"rec {i}: {sorted(diff)}"
            assert rd(d2, base2, rb["w"][SLOT_JP], rb["w"][SLOT_JP + 1]) == plan[i]
        else:
            assert not diff, f"rec {i}: ไม่ควรเปลี่ยน"
        for k in range(2, 18, 2):  # key, EN, FR, ES, ZH, KO, ZH เดิมอ่านได้เท่าเดิม
            if k != SLOT_JP:
                assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[4,5], ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
