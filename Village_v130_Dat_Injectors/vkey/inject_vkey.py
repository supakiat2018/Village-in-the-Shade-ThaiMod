#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_vkey.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ vkey.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_vkey.py vkey.dat vkey_ตารางคำแปลไทย_PUA.csv [out.dat]

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์: [0]=count=16, [1]=ผลรวม rec_size=1536 (=16*96), [2]=blob_size=1669
Record: ทุกเรคคอร์ด rec_size=96 (24 คำ) -> เรคคอร์ด i เริ่มที่ 12 + i*100
BLOB_BASE = 12 + 16*100 = 1612 (0x64C)

Payload (w[0] = คำแรกหลัง rec_size):
    w[0]      ID ประจำคำสั่ง ไม่ซ้ำกัน 1000..1014, 1016 (ไม่มี 1015)   <-- ใช้จับคู่กับคอลัมน์ id ใน CSV
    w[2]      ตัวเลข (ไม่ใช่พอยน์เตอร์ w[3]=0) ค่าต่างกันทุกเรคคอร์ด เช่น 121, 83, 97 ... (น่าจะเป็นรหัสปุ่ม/ค่าผูกปุ่ม)
    w[4]      ตัวเลข = 1000 ทุกเรคคอร์ด ยกเว้น rec 15 (ID 1016) = 1001  (น่าจะเป็นกลุ่ม/หมวด ไม่ใช่ ID ประจำปุ่ม)
    w[6,7]    JP   <-- ช่องที่ฉีด
    w[8,9]    EN    w[10,11] FR    w[12,13] ES
    w[14,15]  ZH    w[16,17] KO    w[18,19] ZH(เต็ม)
    w[20..23] 0
    *** ไฟล์นี้ไม่มีสตริง key ***  (ต่างจากไฟล์อื่น) จับคู่ด้วย w[0] เท่านั้น

ลำดับเรคคอร์ดในไฟล์: ID 1000..1016 เรียงตามปกติ (rec 6 = 1006, rec 7 = 1007)
ลำดับสตริงใน blob และแถวใน CSV: 1007 มาก่อน 1006 (CSV index 6 = id 1007, index 7 = id 1006)
-> จับคู่ด้วย id เสมอ ห้ามจับคู่ด้วยลำดับ

CSV นี้ไม่มีคอลัมน์ JP/EN จึงตรวจเทียบข้อความเดิมโดยตรงไม่ได้
-> สคริปต์ตรวจว่า w[6,7] เป็นอักษรญี่ปุ่นและมี EN (อักษรละติน) ตามหลังที่ w[8,9] แล้วพิมพ์ JP / EN / th_plain
   เทียบกันให้ตรวจด้วยตา และตรวจคอลัมน์ bytes ใน CSV = ความยาว UTF-8 ของ th_pua
"""
import csv
import re
import struct
import sys
from pathlib import Path

HDR = 12
SLOT_ID_WORD = 0
SLOT_JP, SLOT_EN = 6, 8
CHECK_SLOTS = (8, 10, 12, 14, 16, 18)  # EN FR ES ZH KO ZH ต้องอ่านได้เท่าเดิมหลังฉีด
JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
LAT_RE = re.compile(r"[A-Za-z]")


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
    outp = Path(sys.argv[3]) if len(sys.argv) > 3 else dat.with_name("vkey_patched.dat")

    orig = dat.read_bytes()
    cnt, tot, bs, recs, base = parse(orig)
    rows = list(csv.DictReader(open(csvp, encoding="utf-8-sig", newline="")))
    by_id = {int(r["id"]): r for r in rows}
    assert len(rows) == cnt == len(by_id), f"CSV {len(rows)} แถว / .dat {cnt} เรคคอร์ด / id ไม่ซ้ำ {len(by_id)}"
    ids = [r["w"][SLOT_ID_WORD] for r in recs]
    assert len(set(ids)) == cnt and set(ids) == set(by_id), f"id ใน .dat {ids} ไม่ตรงกับ CSV {sorted(by_id)}"

    # ---------- 1) ตรวจก่อนแก้ ----------
    plan = []
    for i, r in enumerate(recs):
        w = r["w"]
        assert r["size"] == 96, f"rec {i}: rec_size {r['size']} != 96"
        rid = w[SLOT_ID_WORD]
        row = by_id[rid]
        jp = rd(orig, base, w[SLOT_JP], w[SLOT_JP + 1])
        en = rd(orig, base, w[SLOT_EN], w[SLOT_EN + 1])
        assert JP_RE.search(jp), f"rec {i}: w[6,7] ไม่ใช่ญี่ปุ่น {jp!r}"
        assert LAT_RE.search(en), f"rec {i}: w[8,9] ไม่ใช่ EN {en!r}"
        th = row["th_pua"]
        assert th, f"rec {i} (id {rid}): th_pua ว่าง"
        assert len(th.encode("utf-8")) == int(row["bytes"]), f"id {rid}: bytes ใน CSV ไม่ตรงความยาว UTF-8"
        plan.append(th)
        print(f"rec {i:2d} id={rid} off={w[SLOT_JP]:4d} len={w[SLOT_JP + 1]:2d} | {jp} | {en} | {row['th_plain']}")

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
        for k in CHECK_SLOTS:
            assert rd(orig, base, ra["w"][k], ra["w"][k + 1]) == rd(d2, base2, rb["w"][k], rb["w"][k + 1])
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ w[6,7], ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
