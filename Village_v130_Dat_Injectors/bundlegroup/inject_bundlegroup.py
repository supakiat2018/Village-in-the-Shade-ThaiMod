#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_bundlegroup.py
ฉีดคำแปลไทย (PUA) ลงช่อง JP ของ bundlegroup.dat (Village in the Shade PC v1.30)
ด้วยวิธี Safe Append & Re-point (ไม่เขียนทับ String Blob เดิม)

การใช้งาน:
    python inject_bundlegroup.py bundlegroup.dat bundlegroup_ตารางคำแปลไทย_PUA.csv [out.dat]

โครงสร้างที่ตรวจพบจากไฟล์จริง (Little-Endian)
---------------------------------------------
Header 12 ไบต์ ที่ offset 0x00:
    [0] count       = 18
    [1] total_payload = 2448 (= 18 * 136, ไม่เปลี่ยน)
    [2] blob_size   = 3100  <-- ตัวเดียวที่ต้องแก้หลังต่อท้าย Blob

Record (ทุกเรคคอร์ดเหมือนกัน): uint32 rec_size = 136 + payload 34 คำ (uint32)
    ขนาดต่อเรคคอร์ด = 4 + 136 = 140 ไบต์
    เรคคอร์ด i เริ่มที่ 12 + i*140

    BLOB_BASE = 12 + 18*140 = 2532 (0x09E4)

Payload word index (นับจาก 0 หลัง rec_size):
    w[0]      ตัวเลข (ประเภท/ไอดีภายใน)
    w[1]      0
    w[2],w[3]   (off,len)  key  เช่น BUNDLE_GROUP_ID_SPRING_01
    w[4],w[5]   (off,len)  tag_jp  เช่น 狐のお社・春_01
    w[6]      ตัวเลข (ไม่ใช่พอยน์เตอร์ -- ห้ามแตะ)
    w[7],w[8]   (off,len)  *** JP SLOT ***  เช่น 狐の社／春   <-- ช่องที่ฉีด
    w[9],w[10]  (off,len)  EN
    w[11],w[12] (off,len)  FR
    w[13],w[14] (off,len)  ES
    w[15],w[16] (off,len)  ZH (จีนตัวย่อ)
    w[17],w[18] (off,len)  KO
    w[19],w[20] (off,len)  ZH (จีนตัวเต็ม)
    w[21..33]   ตัวเลขอื่นๆ

    ตำแหน่งไบต์ของ JP slot ในไฟล์ = 12 + i*140 + 4 + 7*4  = 44 + i*140  (offset)
                                                     และ +4 = 48 + i*140  (length)

offset ของสตริง JP เดิม (นับจาก BLOB_BASE) ที่พบ:
    rec 0: 48   rec 1: 237  rec 2: 431  rec 3: 623  rec 4: 819  rec 5: 991
    rec 6: 1163 rec 7: 1335 rec 8: 1507 rec 9: 1678 rec10: 1834 rec11: 1988
    rec12: 2136 rec13: 2279 rec14: 2460 rec15: 2639 rec16: 2812 rec17: 2962
(สคริปต์ตรวจค่าเหล่านี้กับ jp_orig ในตาราง CSV ทุกแถวก่อนแก้ไฟล์)
"""
import csv
import shutil
import struct
import sys
from pathlib import Path

HDR_SIZE = 12
JP_OFF_WORD = 7          # w[7] = offset, w[8] = length
JP_LEN_WORD = 8
KEY_OFF_WORD = 2
KEY_LEN_WORD = 3
# ช่องภาษาอื่นที่ใช้ตรวจว่ายังอ่านได้เหมือนเดิมหลังฉีด
OTHER_SLOTS = {"key": (2, 3), "tag_jp": (4, 5), "en": (9, 10), "fr": (11, 12),
               "es": (13, 14), "zh1": (15, 16), "ko": (17, 18), "zh2": (19, 20)}


def parse(data: bytes):
    count, total, blob_size = struct.unpack_from("<III", data, 0)
    recs, p = [], HDR_SIZE
    for _ in range(count):
        rec_size = struct.unpack_from("<I", data, p)[0]
        words = list(struct.unpack_from("<%dI" % (rec_size // 4), data, p + 4))
        recs.append({"pos": p, "size": rec_size, "words": words})
        p += 4 + rec_size
    blob_base = p
    assert len(data) == blob_base + blob_size, "ขนาดไฟล์ไม่ตรงกับ header blob_size"
    return count, total, blob_size, recs, blob_base


def read_str(data, blob_base, off, ln):
    s = data[blob_base + off: blob_base + off + ln]
    assert data[blob_base + off + ln: blob_base + off + ln + 1] == b"\0", "สตริงไม่ลงท้ายด้วย \\0"
    return s.decode("utf-8")


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    dat_path, csv_path = Path(sys.argv[1]), Path(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else dat_path.with_name("bundlegroup_patched.dat")

    orig = dat_path.read_bytes()
    count, total, blob_size, recs, blob_base = parse(orig)
    rows = load_csv(csv_path)
    assert len(rows) == count, f"CSV {len(rows)} แถว แต่ .dat มี {count} เรคคอร์ด"

    # ---- 1) ตรวจ key + jp_orig ทุกแถวก่อนแก้ไฟล์ ----
    for i, (rec, row) in enumerate(zip(recs, rows)):
        w = rec["words"]
        key = read_str(orig, blob_base, w[KEY_OFF_WORD], w[KEY_LEN_WORD])
        jp = read_str(orig, blob_base, w[JP_OFF_WORD], w[JP_LEN_WORD])
        assert key == row["key"], f"rec {i}: key ไม่ตรง {key!r} != {row['key']!r}"
        assert jp == row["jp_orig"], f"rec {i}: JP ไม่ตรง {jp!r} != {row['jp_orig']!r}"
        print(f"rec {i:2d} JP slot @file+{rec['pos'] + 4 + JP_OFF_WORD * 4:#06x} "
              f"old_off={w[JP_OFF_WORD]:5d} old_len={w[JP_LEN_WORD]:3d}  {jp}")

    # ---- 2) Safe Append & Re-point ----
    out = bytearray(orig)
    new_blob_tail = bytearray()
    cur = blob_size                       # offset (นับจาก BLOB_BASE) ที่สตริงใหม่ตัวแรกจะเริ่ม
    for i, (rec, row) in enumerate(zip(recs, rows)):
        th = row["ชื่อกลุ่ม_PUA"]
        assert th, f"rec {i}: ช่อง PUA ว่าง"
        b = th.encode("utf-8")
        new_off, new_len = cur, len(b)
        new_blob_tail += b + b"\0"
        cur += new_len + 1
        # แก้เฉพาะคู่ (offset,length) ของ JP slot
        base = rec["pos"] + 4
        struct.pack_into("<II", out, base + JP_OFF_WORD * 4, new_off, new_len)
        print(f"rec {i:2d} -> new_off={new_off} new_len={new_len}")

    out += new_blob_tail
    # อัปเดต Header[2] = blob_size ใหม่ (Header[1] เป็นผลรวมขนาด payload ของเรคคอร์ด จึงไม่เปลี่ยน)
    struct.pack_into("<I", out, 8, cur)
    out_path.write_bytes(out)
    print(f"เขียน {out_path}  blob_size {blob_size} -> {cur}  ไฟล์ {len(orig)} -> {len(out)} ไบต์")

    # ---- 3) ตรวจสอบหลังฉีด ----
    d2 = bytes(out)
    c2, t2, bs2, r2, bb2 = parse(d2)
    assert (c2, t2) == (count, total) and bb2 == blob_base and bs2 == cur
    assert d2[blob_base:blob_base + blob_size] == orig[blob_base:blob_base + blob_size], "Blob เดิมถูกแก้!"
    for i, (ra, rb, row) in enumerate(zip(recs, r2, rows)):
        wa, wb = ra["words"], rb["words"]
        diff = [k for k in range(len(wa)) if wa[k] != wb[k]]
        assert diff == [JP_OFF_WORD, JP_LEN_WORD], f"rec {i}: มีคำที่เปลี่ยนนอกเหนือ JP slot: {diff}"
        assert read_str(d2, bb2, wb[JP_OFF_WORD], wb[JP_LEN_WORD]) == row["ชื่อกลุ่ม_PUA"]
        for name, (a, b) in OTHER_SLOTS.items():
            assert read_str(orig, blob_base, wa[a], wa[b]) == read_str(d2, bb2, wb[a], wb[b]), (i, name)
    print("ตรวจสอบผ่านทั้งหมด: Blob เดิมไม่เปลี่ยน, เปลี่ยนเฉพาะ JP slot, ภาษาอื่นอ่านได้เหมือนเดิม")


if __name__ == "__main__":
    main()
