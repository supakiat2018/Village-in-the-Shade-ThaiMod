#!/usr/bin/env python3
"""
inject_crops.py - ฉีดข้อความไทย (คอลัมน์ Thai_PUA) ลงช่องภาษาญี่ปุ่น (JP Slot) ใน crops.dat
ของเกม Village in the Shade (Steam PC v1.30) ด้วยวิธี Safe Append & Re-point

โครงสร้างไฟล์ (little-endian u32):
  Header 12 byte : [0]=จำนวนเรคคอร์ด(162)  [1]=? (ไม่แตะ)  [2]=ขนาด String Blob
  เรคคอร์ดขนาดไม่เท่ากัน ต่อกันตั้งแต่ byte 12 จนถึง BLOB_BASE (= ขนาดไฟล์ - blob_size):
      u32 size            ตัวถัดไป = pos+4+size
      pair KEY            (offset,length) ที่ +12  เช่น CROPS_ID_ONION
      ... ช่องชื่อ 7 ภาษา (JP, EN, FR, ES, ZH-TW, KO, ZH-CN) ที่ +28 (และอีกหลายชุดในเรคคอร์ด
          เดียวกัน เช่น พันธุ์ "祟られ..", ถั่วแขก x3) ตำแหน่งไม่คงที่ตามชนิดเรคคอร์ด
  String Blob : UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, length ไม่รวม \\0

คอลัมน์ Key ใน CSV (DIFF_TOKEN_n) ไม่ใช่ key ของเกม จึงจับคู่ด้วย "ลำดับ + ต้นฉบับ_JP":
สแกนหา pair ที่เป็นช่อง JP ของชื่อ (ข้อความ == ต้นฉบับ_JP และ pair ถัดไปเป็นสตริงถูกต้อง)
ตามลำดับในไฟล์ แล้วจับคู่ 1:1 กับแถว CSV ตามลำดับ - ต้องครบพอดีและ JP ตรงทุกแถว ไม่งั้นหยุด

วิธีฉีด: ต่อสตริงไทยท้าย blob -> แก้เฉพาะ pair JP -> อัปเดต header[2]  (ไม่มี offset อื่นเลื่อน)

ใช้งาน:  python3 inject_crops.py crops.dat crops_PUA.csv crops_out.dat
"""
import csv
import struct
import sys

csv.field_size_limit(10 ** 9)


def main(src, csv_path, dst):
    d = bytearray(open(src, 'rb').read())
    count, _, blob_size = struct.unpack_from('<3I', d, 0)
    base = len(d) - blob_size
    orig_len = len(d)

    def rd(p):
        a, l = struct.unpack_from('<II', d, p)
        if base + a + l >= len(d) or d[base + a + l] != 0 or (a and d[base + a - 1] != 0):
            return None
        try:
            return d[base + a:base + a + l].decode('utf-8')
        except UnicodeDecodeError:
            return None

    recs, pos = [], 12
    for _ in range(count):
        size = struct.unpack_from('<I', d, pos)[0]
        recs.append((pos, size))
        pos += 4 + size
    if pos != base:
        raise ValueError(f"เดินเรคคอร์ดจบที่ {pos} แต่ blob เริ่มที่ {base}")
    print(f"เรคคอร์ดใน .dat: {count}, blob base = {base}")

    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    jps = {x['ต้นฉบับ_JP'] for x in rows}

    # ช่อง JP ของชื่อ: ข้อความตรง JP ใน CSV และอีก 6 pair ถัดไป (EN..ZH-CN) เป็นสตริงถูกต้อง
    cands = []
    for r, sz in recs:
        for p in range(r + 4, r + 4 + sz - 55, 4):
            s = rd(p)
            if s and s in jps and all(rd(p + 8 * k) is not None for k in range(1, 7)):
                cands.append((p, s))
    print(f"ช่อง JP ที่พบในไฟล์: {len(cands)}  แถว CSV: {len(rows)}")
    if len(cands) != len(rows):
        raise ValueError("จำนวนช่อง JP ในไฟล์ไม่เท่ากับจำนวนแถว CSV")

    pool, injected, empty = {}, 0, 0
    end = len(d)
    for x, (p, s) in zip(rows, cands):
        if s != x['ต้นฉบับ_JP']:
            raise ValueError(f"ลำดับไม่ตรง: {x['Key']} JP={x['ต้นฉบับ_JP']!r} แต่ไฟล์={s!r}")
        th = x['Thai_PUA']
        if not th:
            empty += 1
            continue
        if '\x00' in th:
            raise ValueError(f"{x['Key']}: มี NUL")
        b = th.encode('utf-8')
        if b not in pool:
            pool[b] = end - base
            d.extend(b + b'\x00')
            end += len(b) + 1
        struct.pack_into('<II', d, p, pool[b], len(b))
        injected += 1

    struct.pack_into('<I', d, 8, len(d) - base)
    open(dst, 'wb').write(d)
    print(f"ฉีด {injected} ข้อความ (ไม่ซ้ำ {len(pool)}), ข้ามแถวว่าง {empty}")
    print(f"{orig_len} -> {len(d)} bytes ({dst})")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
