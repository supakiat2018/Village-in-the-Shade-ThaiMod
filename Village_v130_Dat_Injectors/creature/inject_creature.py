#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_creature.py - ฉีดคำแปลภาษาไทย (PUA) ลงช่อง JP ของ creature.dat
Village in the Shade (Steam 1.30)  |  โหมด Safe Append & Re-point

โครงสร้างไฟล์ (Little-Endian) ที่ตรวจสอบจากไฟล์จริง:
  Header 12 ไบต์ : [0]=จำนวนเรคคอร์ด  [1]=ผลรวมขนาด payload ของเรคคอร์ด  [2]=blob_size
  Records        : ต่อเนื่องกัน เรคคอร์ดละ  uint32 size + payload(size ไบต์)  (ขนาดไม่เท่ากัน)
                   payload: [+0]=id/hash  [+4]=0  [+8..]= 8 คู่ (offset,len) uint32
                   คู่ที่ 0 = Key, คู่ที่ 1 = JP, 2..7 = EN, FR, ES, ZH-TW, KO, ZH-CN
  String Blob    : ท้ายไฟล์ ยาว blob_size ไบต์  (BLOB_BASE = filesize - blob_size)
                   สตริง UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, len ไม่รวม \\0

วิธีใช้:
  python3 inject_creature.py creature.dat translations_PUA.csv creature_th.dat
  (ไม่ระบุ argument = ใช้ชื่อไฟล์ดีฟอลต์ในโฟลเดอร์ปัจจุบัน)
"""
import csv
import struct
import sys

RECORD_COUNT_EXPECT = 192
PAIR_START = 8          # ตำแหน่งเริ่มตารางพอยน์เตอร์ใน payload
JP_PAIR_INDEX = 1       # 0 = Key, 1 = JP
NUM_PAIRS = 8


def parse(data):
    cnt, rec_total, blob_size = struct.unpack_from("<3I", data, 0)
    base = len(data) - blob_size
    pos, recs = 12, []
    for _ in range(cnt):
        sz = struct.unpack_from("<I", data, pos)[0]
        recs.append(pos + 4)  # ตำแหน่งเริ่ม payload
        pos += 4 + sz
    if pos != base:
        raise SystemExit(f"โครงสร้างไม่ตรง: จบเรคคอร์ดที่ {pos} แต่ BLOB_BASE={base}")
    return cnt, rec_total, blob_size, base, recs


def read_str(data, base, off, ln):
    s, e = base + off, base + off + ln
    if data[e] != 0:
        raise SystemExit(f"สตริงที่ offset {off} ไม่ลงท้ายด้วย \\0")
    return data[s:e].decode("utf-8")


def pair_pos(payload, idx):
    return payload + PAIR_START + 8 * idx


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["Key"]: r for r in rows}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "creature.dat"
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "creature_ตารางคำแปลไทย_PUA.csv"
    dst = sys.argv[3] if len(sys.argv) > 3 else "creature_th.dat"

    data = bytearray(open(src, "rb").read())
    cnt, rec_total, blob_size, base, recs = parse(data)
    if cnt != RECORD_COUNT_EXPECT:
        print(f"[เตือน] จำนวนเรคคอร์ด {cnt} (คาดว่า {RECORD_COUNT_EXPECT})")

    table = load_csv(csv_path)
    new_blob = bytearray()
    injected, skipped, used = 0, [], set()

    for i, payload in enumerate(recs):
        pairs = [struct.unpack_from("<II", data, pair_pos(payload, k)) for k in range(NUM_PAIRS)]
        key = read_str(data, base, *pairs[0])
        jp = read_str(data, base, *pairs[JP_PAIR_INDEX])
        row = table.get(key)
        if row is None:
            skipped.append((i, key, "ไม่มีในตาราง"))
            continue
        if row["ต้นฉบับ_JP"] != jp:
            raise SystemExit(f"JP ไม่ตรง ที่ {key}: ไฟล์={jp!r} ตาราง={row['ต้นฉบับ_JP']!r}")
        th = row["Thai_PUA"]
        if not th:
            skipped.append((i, key, "Thai_PUA ว่าง"))
            continue
        raw = th.encode("utf-8")
        off = blob_size + len(new_blob)
        new_blob += raw + b"\x00"
        struct.pack_into("<II", data, pair_pos(payload, JP_PAIR_INDEX), off, len(raw))
        used.add(key)
        injected += 1

    unused = set(table) - used - {k for _, k, _ in skipped}
    data += new_blob
    struct.pack_into("<I", data, 8, blob_size + len(new_blob))  # Header[2]

    open(dst, "wb").write(data)

    # ---------- ตรวจสอบไฟล์ผลลัพธ์ ----------
    out = bytes(data)
    cnt2, rt2, bs2, base2, recs2 = parse(out)
    assert base2 == base, "BLOB_BASE ต้องไม่ขยับ"
    assert cnt2 == cnt and rt2 == rec_total
    orig = open(src, "rb").read()
    assert out[base:base + blob_size] == orig[base:], "blob เดิมต้องไม่เปลี่ยน"
    ok = 0
    for i, (p_old, p_new) in enumerate(zip(recs, recs2)):
        for k in range(NUM_PAIRS):
            a = read_str(orig, base, *struct.unpack_from("<II", orig, pair_pos(p_old, k)))
            b = read_str(out, base2, *struct.unpack_from("<II", out, pair_pos(p_new, k)))
            key = read_str(orig, base, *struct.unpack_from("<II", orig, pair_pos(p_old, 0)))
            if k == JP_PAIR_INDEX and key in used:
                assert b == table[key]["Thai_PUA"]
                ok += 1
            else:
                assert a == b, f"{key} slot {k} เปลี่ยนโดยไม่ตั้งใจ"
    print(f"ฉีดสำเร็จ {injected} รายการ (ตรวจย้อนกลับผ่าน {ok})")
    print(f"blob_size: {blob_size} -> {bs2}  | ขนาดไฟล์: {len(orig)} -> {len(out)}")
    for i, k, why in skipped:
        print(f"ข้าม record #{i} {k}: {why}")
    for k in sorted(unused):
        print(f"[เตือน] Key ในตารางที่ไม่พบในไฟล์: {k}")
    print("เขียนไฟล์:", dst)


if __name__ == "__main__":
    main()
