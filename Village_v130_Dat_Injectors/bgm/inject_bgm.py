#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_bgm.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ bgm.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_bgm.py bgm.dat bgm_ตารางคำแปลไทย_PUA.csv [out.dat]

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=38, [1]=ผลรวม rec_size=4560 (=38*120), [2]=blob_size=7697
Record: ทุกเรคคอร์ด rec_size=120 (30 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*124
BLOB_BASE = 12 + 38*124 = 4724 (0x1274)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ไอดี (1..38)
    w[2,3]    key BGM_ID_*
    w[8,9]    ชื่อไฟล์เสียง เช่น BGM01.wav     (ตัวระบุระบบ ห้ามแตะ)
    w[10,11]  พาธไฟล์เสียง data/bgm/bgmNN.nlsd (ตัวระบุระบบ ห้ามแตะ)
    w[16,17]  JP   <-- ช่องที่ฉีด
    w[18,19]  EN    w[20,21] FR    w[22,23] ES
    w[24,25]  ZH    w[26,27] KO    w[28,29] ZH(เต็ม)
    w[12..15] ตัวเลข (เช่น w[15]=48000 น่าจะเป็น sample rate; w[13],w[14] น่าจะเกี่ยวกับเสียง/ลูป ยังไม่ยืนยัน) ห้ามแตะ
    (rec 0 มี w[12]=100,w[13]=0 ต่างจากเรคคอร์ดอื่น เป็นค่าตัวเลข ไม่แตะ)

offset JP เดิม (นับจาก BLOB_BASE): rec0=39, rec1=347, rec2=564, ... rec37=7546
(สคริปต์พิมพ์ครบทุกเรคคอร์ดตอนรัน และตรวจ key / ไฟล์เสียง / ชื่อ_JP / ชื่อ_EN กับตาราง CSV ทุกแถวก่อนแก้ไฟล์)
"""
import csv
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY, SLOT_FILE, SLOT_PATH, SLOT_JP, SLOT_EN = 2, 8, 10, 16, 18
CHECK_SLOTS = (2, 8, 10, 18, 20, 22, 24, 26, 28)  # ช่องที่ต้องอ่านได้เท่าเดิมหลังฉีด


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
    outp = Path(sys.argv[3]) if len(sys.argv) > 3 else dat.with_name("bgm_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_key = {r["BGM_ID"]: r for r in rows}
    assert len(rows) == cnt == len(by_key), f"CSV {len(rows)} แถว / .dat {cnt} เรคคอร์ด / key ไม่ซ้ำ {len(by_key)}"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = []
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 120, f"rec {i}: rec_size {r['size']} != 120"
        key = rd(orig, base, w[SLOT_KEY], w[SLOT_KEY + 1])
        assert key in by_key, f"rec {i}: key {key!r} ไม่มีในตาราง"
        row = by_key[key]
        assert rd(orig, base, w[SLOT_FILE], w[SLOT_FILE + 1]) == row["ไฟล์เสียง"], f"rec {i}: ชื่อไฟล์เสียงไม่ตรง"
        path = rd(orig, base, w[SLOT_PATH], w[SLOT_PATH + 1])
        assert path.startswith("data/bgm/") and path.endswith(".nlsd"), f"rec {i}: พาธผิดรูป {path!r}"
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        assert jp == row["ชื่อ_JP"], f"rec {i}: JP {jp!r} != {row['ชื่อ_JP']!r}"
        assert en == row["ชื่อ_EN"], f"rec {i}: EN {en!r} != {row['ชื่อ_EN']!r}"
        assert row["ชื่อ_PUA"], f"rec {i}: ช่อง PUA ว่าง"
        plan.append(row["ชื่อ_PUA"])
        print(f"rec {i:2d} JP w[16,17]=({w[16]},{w[17]}) {key:28s} {jp}")

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
        for k in CHECK_SLOTS:  # key, ไฟล์เสียง, พาธ, EN, FR, ES, ZH, KO, ZH เดิมอ่านได้เท่าเดิม
            assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[16,17], ไฟล์เสียง/พาธ/ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
