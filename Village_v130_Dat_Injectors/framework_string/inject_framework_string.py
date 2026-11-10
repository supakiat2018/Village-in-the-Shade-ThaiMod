#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_framework_string.py
ฉีดข้อความ th_final (สัญลักษณ์/ตัวย่อตัวเลข ไม่ผ่าน PUA) ลงช่อง JP ของ framework_string.dat
(Village in the Shade PC v1.30) ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_framework_string.py framework_string.dat framework_string_ตารางคำแปลไทย_พร้อมฉีด.csv [out.dat] [--skip-empty-jp]

    --skip-empty-jp  ไม่ฉีดเรคคอร์ดที่ช่อง JP เดิมว่าง (rec 8 STR_ID_NUM_FLOOR_7) คงให้ว่างเหมือนต้นฉบับ

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=9, [1]=ผลรวม rec_size=792 (=9*88), [2]=blob_size=353
Record: ทุกเรคคอร์ด rec_size=88 (22 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*92
BLOB_BASE = 12 + 9*92 = 840 (0x348)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ID (1..9)      w[1] = 0
    w[2,3]    key STR_ID_*
    w[4,5]    JP   <-- ช่องที่ฉีด   (rec 8: length = 0 เป็นสตริงว่างที่ offset 342)
    w[6,7]    EN    w[8,9] FR    w[10,11] ES (ในไฟล์นี้เป็นตัวอักษรญี่ปุ่นเดิม)
    w[12,13]  ZH(เต็ม)    w[14,15] KO    w[16,17] ZH(ย่อ)
    w[18..21] 0

offset JP เดิม (นับจาก BLOB_BASE): rec0=14 rec1=45 rec2=80 rec3=123 rec4=166 rec5=209 rec6=252 rec7=297 rec8=342(len 0)
"""
import csv
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_KEY, SLOT_JP, SLOT_EN = 2, 4, 6
SLOT_ZH, SLOT_KO = 12, 14
CHECK_SLOTS = (2, 6, 8, 10, 12, 14, 16)  # key, EN, FR, ES, ZH, KO, ZH ต้องอ่านได้เท่าเดิมหลังฉีด


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
    skip_empty = "--skip-empty-jp" in sys.argv
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    dat, csvp = Path(args[0]), Path(args[1])
    outp = Path(args[2]) if len(args) > 2 else dat.with_name("framework_string_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_key = {r["key"]: r for r in rows}
    assert len(rows) == cnt == len(by_key), f"CSV {len(rows)} แถว / .dat {cnt} เรคคอร์ด / key ไม่ซ้ำ {len(by_key)}"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = {}
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 88, f"rec {i}: rec_size {r['size']} != 88"
        key = rd(orig, base, w[SLOT_KEY], w[SLOT_KEY + 1])
        assert key in by_key, f"rec {i}: key {key!r} ไม่มีในตาราง"
        row = by_key[key]
        assert w[0] == int(row["id"]), f"rec {i}: id {w[0]} != {row['id']}"
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        assert jp == row["jp_orig"], f"rec {i}: JP {jp!r} != {row['jp_orig']!r}"
        note = ""
        # EN เป็นการตรวจแบบเตือน (ไม่หยุด): CSV rec 0,1 เก็บ en_moden เป็นตัวเต็มความกว้าง (／ ＆) ส่วนในไฟล์เป็น ASCII (/ &)
        # และ rec 8 CSV ว่าง แต่ในไฟล์ EN = "Sx"; ตัวตัดสินการจับคู่คือ key + id + jp_orig
        if row["en_moden"] != en:
            note = f"  [EN ในไฟล์={en!r} ต่างจาก CSV en_moden={row['en_moden']!r}]"
        for col, slot in (("zh", SLOT_ZH), ("ko", SLOT_KO)):
            if row[col]:
                assert rd(orig, base, w[slot], w[slot + 1]) == row[col], f"rec {i}: {col} ไม่ตรง"
        th = row["th_final"]
        assert th, f"rec {i}: th_final ว่าง"
        if jp == "" and skip_empty:
            print(f"rec {i} {key}: ข้าม (JP เดิมว่าง, --skip-empty-jp)")
            continue
        plan[i] = th
        print(f"rec {i} id={w[0]} {key:20s} JP w[4,5]=({w[4]},{w[5]}) {jp!r} -> {th!r}{note}")

    # ---------- 2) Safe Append & Re-point ----------
    out = bytearray(orig)
    tail = bytearray()
    cur = bs
    for i, th in plan.items():
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
        if i in plan:
            assert diff <= {SLOT_JP, SLOT_JP + 1} and ra["w"][SLOT_JP] != rb["w"][SLOT_JP], f"rec {i}: {sorted(diff)}"
            assert rd(d2, base2, rb["w"][SLOT_JP], rb["w"][SLOT_JP + 1]) == plan[i]
        else:
            assert not diff, f"rec {i}: ไม่ควรเปลี่ยน"
        for k in CHECK_SLOTS:
            assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[4,5], key/ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
