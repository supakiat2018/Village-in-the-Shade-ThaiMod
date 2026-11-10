#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_itemtype.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ itemtype.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_itemtype.py itemtype.dat itemtype_ตารางคำแปลไทย_PUA.csv [out.dat] [--slot 6|4]

    --slot 6 (ค่าเริ่มต้น)  แก้พอยน์เตอร์ w[6,7]  = ช่องภาษาญี่ปุ่นที่เป็น "ภาษา" จริง (แนะนำ)
    --slot 4               แก้พอยน์เตอร์ w[4,5]  = ช่อง tag/label ตามที่ระบุในโจทย์เดิม

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=7, [1]=ผลรวม rec_size=784 (=7*112), [2]=blob_size=352
Record: ทุกเรคคอร์ด rec_size=112 (28 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*116
BLOB_BASE = 12 + 7*116 = 824 (0x338)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ไอดี (0..6)      w[1] = 0
    w[2,3]    key  ITEM_TYPE_*
    w[4,5]    tag / label ภายใน (ข้อความ JP เหมือน w[6,7] ทุกเรคคอร์ด แต่ offset คนละที่)
    w[6,7]    ชื่อประเภท JP   <-- ช่องภาษา JP จริง
    w[8,9]    EN      w[10,11] FR      w[12,13] ES
    w[14,15]  ZH      w[16,17] KO      w[18,19] ZH(เต็ม)
    w[20..27] ตัวเลข/แฟลก (ไม่ใช่พอยน์เตอร์ ห้ามแตะ)

เหตุผลที่แนะนำ w[6,7]: ลำดับภาษาเหมือนไฟล์ bundlegroup.dat/character.dat เป๊ะ
    (key, tag, JP, EN, FR, ES, ZH, KO, ZH) และช่อง JP จะมีช่อง EN ต่อท้ายที่ +2 เสมอ
    ส่วน w[4,5] อยู่ตำแหน่งเดียวกับ tag_jp ของ bundlegroup ซึ่งเป็น label ไม่ใช่ข้อความที่แสดง

offset เดิม (นับจาก BLOB_BASE) ที่ตรวจพบ  [w[4,5] / w[6,7]]:
    rec0 CONSUME 18/28   rec1 TOOL 107/114   rec2 HAT 141/148   rec3 SHOES 177/184
    rec4 RING 212/219    rec5 GIMMICK 250/263 rec6 NUM 296/321
(สคริปต์ตรวจค่าเหล่านี้กับ jp_orig ในตาราง CSV ทุกแถวก่อนแก้ไฟล์)

หมายเหตุ: rec6 ITEM_TYPE_NUM เป็นค่านับจำนวนประเภท (sentinel) ไม่น่าจะถูกแสดงในเกม แต่ฉีดตามตาราง
"""
import argparse
import csv
import struct
from pathlib import Path

HDR = 12
SLOT_LABEL = 4
SLOT_JP = 6
SLOT_KEY = 2
SLOT_EN = 8


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
    ap = argparse.ArgumentParser()
    ap.add_argument("dat"); ap.add_argument("csv"); ap.add_argument("out", nargs="?")
    ap.add_argument("--slot", type=int, choices=(4, 6), default=6)
    a = ap.parse_args()
    dat, csvp = Path(a.dat), Path(a.csv)
    outp = Path(a.out) if a.out else dat.with_name("itemtype_patched.dat")
    slot = a.slot

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    assert len(rows) == cnt, f"CSV {len(rows)} แถว != {cnt} เรคคอร์ด"

    # ---------- 1) ตรวจก่อนแก้ ----------
    for i, (r, row) in enumerate(zip(recs, rows)):
        w = r["w"]
        assert r["size"] == 112, f"rec {i}: rec_size {r['size']} != 112"
        assert rd(orig, base, w[2], w[3]) == row["key"], f"rec {i}: key ไม่ตรง"
        t4 = rd(orig, base, w[4], w[5])
        t6 = rd(orig, base, w[6], w[7])
        assert t4 == row["jp_orig"], f"rec {i}: w[4,5] {t4!r} != jp_orig"
        assert t6 == row["jp_orig"], f"rec {i}: w[6,7] {t6!r} != jp_orig"
        assert w[4] != w[6], f"rec {i}: w[4,5] กับ w[6,7] ใช้ offset เดียวกัน (แก้แล้วจะกระทบกัน)"
        assert row["ชื่อประเภท_PUA"], f"rec {i}: ช่อง PUA ว่าง"
        print(f"rec {i} {row['key']:20s} w[4,5]=({w[4]},{w[5]}) w[6,7]=({w[6]},{w[7]}) '{t6}'  -> แก้ w[{slot},{slot + 1}]")

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    for i, (r, row) in enumerate(zip(recs, rows)):
        b = row["ชื่อประเภท_PUA"].encode("utf-8")
        struct.pack_into("<II", out, r["pos"] + 4 + slot * 4, cur, len(b))
        tail += b + b"\0"
        print(f"rec {i} -> new_off={cur} new_len={len(b)}")
        cur += len(b) + 1
    out += tail
    struct.pack_into("<I", out, 8, cur)  # Header[2]
    outp.write_bytes(out)
    print(f"blob_size {bs} -> {cur}; ไฟล์ {len(orig)} -> {len(out)} ไบต์ -> {outp}  (slot w[{slot},{slot + 1}])")

    # ---------- 3) ตรวจหลังฉีด ----------
    d2 = bytes(out)
    c2, t2, bs2, r2, base2 = parse(d2)
    assert (c2, t2, base2, bs2) == (cnt, tot, base, cur)
    assert d2[base:base + bs] == orig[base:base + bs], "Blob เดิมถูกแก้!"
    for i, (ra, rb, row) in enumerate(zip(recs, r2, rows)):
        diff = {k for k in range(len(ra["w"])) if ra["w"][k] != rb["w"][k]}
        assert diff <= {slot, slot + 1}, f"rec {i}: มีคำเปลี่ยนนอกช่อง {sorted(diff)}"
        assert ra["w"][slot] != rb["w"][slot], f"rec {i}: offset ไม่เปลี่ยน"
        assert rd(d2, base2, rb["w"][slot], rb["w"][slot + 1]) == row["ชื่อประเภท_PUA"]
        # ช่องอื่นทั้งหมด (key, อีกช่องของ JP, EN, FR, ES, ZH, KO) อ่านได้เท่าเดิม
        for k in range(2, 20, 2):
            if k != slot:
                assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะช่องที่เลือก, ช่องอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
