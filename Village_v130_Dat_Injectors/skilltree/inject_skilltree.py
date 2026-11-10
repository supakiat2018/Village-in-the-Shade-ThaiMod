#!/usr/bin/env python3
"""
inject_skilltree.py - ฉีดข้อความไทย (PUA) ลงช่องภาษาญี่ปุ่น (JP Slot) ใน skilltree.dat
ของเกม Village in the Shade (Steam PC v1.30) ด้วยวิธี Safe Append & Re-point

โครงสร้างไฟล์ (little-endian u32):
  Header 12 byte : [0]=จำนวนเรคคอร์ด(80)  [1]=? (ไม่แตะ)  [2]=ขนาด String Blob
  เรคคอร์ดขนาดละ 244 ต่อกันตั้งแต่ byte 12 จนถึง BLOB_BASE (= ขนาดไฟล์ - blob_size):
      u32 size(=244)     ตัวถัดไป = pos+4+size
      u32 ID             ที่ +4  (นับจาก 1)
      pair KEY           (offset,length) ที่ +12
      +20  : ชื่อสั้น  (มีเฉพาะ JP; ภาษาอื่นว่าง)          <- ชื่อสั้น_PUA
      +120 : ชื่อเต็ม  7 pair (JP, EN, FR, ES, ZH-TW, KO, ZH-CN)  <- ชื่อเต็ม_PUA
      +176 : คำอธิบาย  7 pair เหมือนกัน                    <- คำอธิบาย_PUA
  String Blob : UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, length ไม่รวม \\0

วิธีฉีด: ต่อสตริงไทยท้าย blob -> แก้เฉพาะ pair JP 3 ช่อง -> อัปเดต header[2]
จับคู่แถว CSV ด้วยคอลัมน์ key (ตรวจ en_title/en_desc เทียบช่อง EN ใน .dat เป็นคำเตือน)

ใช้งาน:  python3 inject_skilltree.py skilltree.dat skilltree_PUA.csv skilltree_out.dat
"""
import csv
import re
import struct
import sys

csv.field_size_limit(10 ** 9)
SLOTS = [('ชื่อสั้น_PUA', 20, None), ('ชื่อเต็ม_PUA', 120, 'en_title'), ('คำอธิบาย_PUA', 176, 'en_desc')]
MARKUP = re.compile(r'[<>]')


def main(src, csv_path, dst):
    d = bytearray(open(src, 'rb').read())
    count, _, blob_size = struct.unpack_from('<3I', d, 0)
    base = len(d) - blob_size
    orig_len = len(d)

    def rd(off, ln):
        a = base + off
        if d[a + ln] != 0:
            raise ValueError("สตริงไม่ลงท้ายด้วย NUL")
        return d[a:a + ln].decode('utf-8')

    recs, pos = {}, 12
    for _ in range(count):
        size = struct.unpack_from('<I', d, pos)[0]
        o, l = struct.unpack_from('<II', d, pos + 12)
        recs[rd(o, l)] = pos
        pos += 4 + size
    if pos != base:
        raise ValueError(f"เดินเรคคอร์ดจบที่ {pos} แต่ blob เริ่มที่ {base}")
    print(f"เรคคอร์ดใน .dat: {count}, blob base = {base}")

    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    pool, injected, warns = {}, 0, []
    end = len(d)
    for x in rows:
        key = x['key']
        if key not in recs:
            raise ValueError(f"key {key} ไม่มีใน .dat")
        r = recs[key]
        for col, rel, en_col in SLOTS:
            th = x[col]
            p = r + rel
            o, l = struct.unpack_from('<II', d, p)
            if l == 0:
                raise ValueError(f"{key}/{col}: ช่อง JP ใน .dat ว่าง")
            if en_col:
                eo, el = struct.unpack_from('<II', d, p + 8)
                if rd(eo, el) != x[en_col]:
                    warns.append(f"{key}: {en_col} ใน CSV ต่างจาก EN ใน .dat ({x[en_col]!r} vs {rd(eo, el)!r})")
            if not th:
                raise ValueError(f"{key}/{col}: ค่า PUA ว่าง")
            if '\x00' in th or MARKUP.search(th):
                raise ValueError(f"{key}/{col}: พบ NUL หรือแท็ก <> ที่ไม่คาดไว้ {th!r}")
            b = th.encode('utf-8')
            if b not in pool:
                pool[b] = end - base
                d.extend(b + b'\x00')
                end += len(b) + 1
            struct.pack_into('<II', d, p, pool[b], len(b))
            injected += 1

    struct.pack_into('<I', d, 8, len(d) - base)
    open(dst, 'wb').write(d)
    print(f"ฉีด {injected} ช่อง (สตริงไม่ซ้ำ {len(pool)}), เรคคอร์ดที่ไม่มีใน CSV: {count - len(rows)}")
    for w in warns:
        print("คำเตือน:", w)
    print(f"{orig_len} -> {len(d)} bytes ({dst})")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
