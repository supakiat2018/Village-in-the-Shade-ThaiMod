#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_character.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ character.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_character.py character.dat character_ตารางคำแปลไทย_PUA.csv [out.dat]

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=16, [1]=ผลรวม rec_size=11752, [2]=blob_size=21461
Record: uint32 rec_size + payload (rec_size/4 คำ)  *** ขนาดไม่เท่ากัน ***
    rec_size = 740 (185 คำ): rec 0, 3, 4, 9, 11
    rec_size = 732 (183 คำ): rec 1, 2, 5, 6, 7, 8, 10, 12, 13, 14, 15
BLOB_BASE = 12 + sum(4 + rec_size) = 11828 (0x2E34)

ตำแหน่งพอยน์เตอร์ (offset,length) ใน payload (นับ w[0] = คำแรกหลัง rec_size):
    w[2,3]    key CHARA_ID_*
    w[4,5]    บทบาท (JP)               <-- ฉีด
    w[6,7]    ชื่อตัวละคร (JP)          <-- ฉีด    (w[8..19] = EN, EN, EN, ZH, KO, ZH)
    w[70,71]  คำอธิบาย 1 (JP)           <-- ฉีด    (w[72..83]  = EN FR ES ZH KO ZH)
    w[84,85]  คำอธิบาย 2 (JP)           <-- ฉีด    (w[92..97]  = ZH KO ZH)
    w[98,99]  คำอธิบาย 3 (JP)           <-- ฉีด    (w[106..111] = ZH KO ZH)
    คำทักทาย (JP)  <-- ฉีด  *** ตำแหน่งขึ้นกับขนาดเรคคอร์ด ***
        rec_size 740 -> w[167,168]   (EN ต่อที่ w[169,170] ... KO w[177,178], ZH w[179,180])
        rec_size 732 -> w[165,166]   (EN ต่อที่ w[167,168] ... )
    (เรคคอร์ด 732 ไบต์ขาดไป 2 คำ ก่อนถึงช่องคำทักทาย จึงเลื่อนไป 2 คำ)

เรคคอร์ด 14 (CHARA_ID_GHOST_GIRL) และ 15 (CHARA_ID_MOTHER) เป็น Dummy:
    ช่อง JP ทั้งหมดยาว 0 ไบต์ และในตารางคำแปลก็ว่าง -> สคริปต์ข้าม ไม่แตะ

ข้อความคำทักทายมี <br> อยู่ในต้นฉบับ (เช่น rec 3,4,5,8,12) และตาราง PUA ก็คง <br> ไว้ -> ฉีดตามตาราง
"""
import csv
import re
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY = 2
FIELDS = [  # (ชื่อช่อง, คอลัมน์ CSV)
    ("role", "บทบาท_PUA"),
    ("name", "ชื่อ_PUA"),
    ("desc1", "คำอธิบาย1_PUA"),
    ("desc2", "คำอธิบาย2_PUA"),
    ("desc3", "คำอธิบาย3_PUA"),
    ("greet", "คำทักทาย_PUA"),
]
FIXED_SLOT = {"role": 4, "name": 6, "desc1": 70, "desc2": 84, "desc3": 98}
GREET_SLOT_BY_SIZE = {740: 167, 732: 165}
JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
LAT_RE = re.compile(r"[A-Za-z]")


def parse(d):
    cnt, tot, bs = struct.unpack_from("<III", d, 0)
    recs, p = [], HDR
    for _ in range(cnt):
        rs = struct.unpack_from("<I", d, p)[0]
        w = list(struct.unpack_from("<%dI" % (rs // 4), d, p + 4))
        recs.append({"pos": p, "size": rs, "w": w})
        p += 4 + rs
    assert tot == sum(r["size"] for r in recs), "Header[1] ไม่เท่าผลรวม rec_size"
    assert len(d) == p + bs, "ขนาดไฟล์ไม่ตรง blob_size"
    return cnt, tot, bs, recs, p


def rd(d, base, off, ln):
    assert d[base + off + ln] == 0, "สตริงไม่ลงท้าย \\0"
    return d[base + off: base + off + ln].decode("utf-8")


def slot_of(rec, field):
    return GREET_SLOT_BY_SIZE[rec["size"]] if field == "greet" else FIXED_SLOT[field]


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    dat, csvp = Path(sys.argv[1]), Path(sys.argv[2])
    outp = Path(sys.argv[3]) if len(sys.argv) > 3 else dat.with_name("character_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    assert len(rows) == cnt, f"CSV {len(rows)} แถว != {cnt} เรคคอร์ด"

    # ---------- 1) ตรวจโครงสร้าง/จับคู่ก่อนแก้ ----------
    for i, (r, row) in enumerate(zip(recs, rows)):
        w = r["w"]
        assert r["size"] in GREET_SLOT_BY_SIZE, f"rec {i}: rec_size {r['size']} ไม่รู้จัก"
        assert rd(orig, base, w[2], w[3]) == row["Character_ID"], f"rec {i}: key ไม่ตรง"
        assert rd(orig, base, w[6], w[7]) == row["ชื่อ_JP"], f"rec {i}: ชื่อ JP ไม่ตรง"
        assert rd(orig, base, w[8], w[9]) == row["ชื่อ_EN"], f"rec {i}: ชื่อ EN ไม่ตรง"
        for f, col in FIELDS:
            a = slot_of(r, f)
            off, ln = w[a], w[a + 1]
            t = rd(orig, base, off, ln)
            if row[col] == "":
                assert ln == 0, f"rec {i} {f}: CSV ว่างแต่ต้นฉบับมีข้อความ"
            else:
                assert ln > 0 and JP_RE.search(t), f"rec {i} {f}: ช่องนี้ไม่ใช่ญี่ปุ่น ({t!r})"
        # คำทักทาย/คำอธิบาย 1: ช่องถัดไป (+2) ต้องเป็นอังกฤษ ยืนยันว่าชี้ช่อง JP ถูกตำแหน่ง
        if rows[i]["คำทักทาย_PUA"]:
            for f in ("greet", "desc1"):
                a = slot_of(r, f)
                assert LAT_RE.search(rd(orig, base, w[a + 2], w[a + 3])), f"rec {i} {f}: ช่อง +2 ไม่ใช่ EN"
        info = {f: (slot_of(r, f), w[slot_of(r, f)], w[slot_of(r, f) + 1]) for f, _ in FIELDS}
        print(f"rec {i:2d} size={r['size']} {row['Character_ID']:32s} " +
              " ".join(f"{f}=w[{a}] off={o} len={l}" for f, (a, o, l) in info.items()))

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    touched = {}
    n_inj = 0
    for i, (r, row) in enumerate(zip(recs, rows)):
        touched[i] = set()
        for f, col in FIELDS:
            if row[col] == "":
                continue
            b = row[col].encode("utf-8")
            a = slot_of(r, f)
            struct.pack_into("<II", out, r["pos"] + 4 + a * 4, cur, len(b))
            tail += b + b"\0"
            touched[i] |= {a, a + 1}
            cur += len(b) + 1
            n_inj += 1
    out += tail
    struct.pack_into("<I", out, 8, cur)  # Header[2]
    outp.write_bytes(out)
    print(f"ฉีด {n_inj} สตริง; blob_size {bs} -> {cur}; ไฟล์ {len(orig)} -> {len(out)} ไบต์ -> {outp}")

    # ---------- 3) ตรวจหลังฉีด ----------
    d2 = bytes(out)
    c2, t2, bs2, r2, base2 = parse(d2)
    assert (c2, t2, base2, bs2) == (cnt, tot, base, cur)
    assert d2[base:base + bs] == orig[base:base + bs], "Blob เดิมถูกแก้!"
    assert d2[:8] == orig[:8]
    for i, (ra, rb, row) in enumerate(zip(recs, r2, rows)):
        assert ra["size"] == rb["size"]
        diff = {k for k in range(len(ra["w"])) if ra["w"][k] != rb["w"][k]}
        # length ใหม่อาจเท่าเดิมโดยบังเอิญ (เช่น rec 2 ชื่อ) จึงเช็กว่า "ที่เปลี่ยน" ต้องอยู่ในช่องที่ตั้งใจแก้เท่านั้น
        assert diff <= touched[i], f"rec {i}: มีคำเปลี่ยนนอกช่องที่ตั้งใจ {sorted(diff - touched[i])}"
        for f, col in FIELDS:
            if row[col]:
                a = slot_of(rb, f)
                assert ra["w"][a] != rb["w"][a], f"rec {i} {f}: offset ไม่เปลี่ยน"
        for f, col in FIELDS:
            if row[col]:
                a = slot_of(rb, f)
                assert rd(d2, base2, rb["w"][a], rb["w"][a + 1]) == row[col], f"rec {i} {f}"
    # สตริงเดิมทุกคู่ที่ไม่ได้แตะ (ภาษาอื่น/ key / ฯลฯ) ยังอ่านได้เท่าเดิม: คำใน payload เท่าเดิม + blob เดิมเท่าเดิม
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, payload เปลี่ยนเฉพาะช่อง JP ที่ฉีด, อ่านกลับตรงตาราง")


if __name__ == "__main__":
    main()
