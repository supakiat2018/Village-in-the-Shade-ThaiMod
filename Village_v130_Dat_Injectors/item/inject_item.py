#!/usr/bin/env python3
"""
inject_item.py - ฉีดข้อความไทย (คอลัมน์ *_pua) ลงช่องภาษาญี่ปุ่น (JP Slot) ใน item.dat
ของเกม Village in the Shade (Steam PC v1.30)  ด้วยวิธี Safe Append

โครงสร้างไฟล์ (little-endian u32):
  Header 12 byte : [0]=จำนวนเรคคอร์ด(3078)  [1]=? (ไม่แตะ)  [2]=ขนาด String Blob
  เรคคอร์ด x N ต่อกันตั้งแต่ byte 12 ไปจนถึง BLOB_BASE (= ขนาดไฟล์ - blob_size):
      u32 size            ขนาดเรคคอร์ด (ไม่รวมตัวมันเอง; 536 หรือ 544 ...) -> ตัวถัดไป = pos+4+size
      pair KEY            (offset,length) ที่ +12
      pair x7 name        ที่ +36   (ลำดับภาษา: JP, EN, FR, ES, ZH-TW, KO, ZH-CN)
      pair x7 pattern     ที่ +92
      pair x7 desc1       ที่ +148
      pair x7 desc2       ที่ +204
      pair x7 desc3       ที่ +260
  String Blob : UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, length ไม่รวม \\0

วิธีฉีด: ต่อสตริงไทยท้าย blob -> แก้เฉพาะ pair ช่อง JP ของ 5 ฟิลด์ -> อัปเดต header[2]
(ไม่มี offset อื่นเลื่อน, เรคคอร์ดที่ไม่มีใน CSV คงเดิม, ช่องที่ *_pua ว่างคงเดิม)

แก้อัตโนมัติ: แท็ก <value N> ที่ช่องว่างหาย (<value1>) -> <value 1>  (ตามรูปแบบที่เกมใช้)

ใช้งาน:  python3 inject_item.py item.dat item_PUA.csv item_out.dat
"""
import csv
import re
import struct
import sys

csv.field_size_limit(10 ** 9)
HDR_SIZE = 12
FIELDS = [('name', 36), ('pattern', 92), ('desc1', 148), ('desc2', 204), ('desc3', 260)]
FIX_VALUE = re.compile(r'<value\s*(\d+)>')          # <value1> / <value  1> -> <value 1>
MARKUP = re.compile(r'<[^>]*>')
TAG_OK = re.compile(r'<value \d+>')


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

    # เดินเรคคอร์ด
    recs, pos = {}, HDR_SIZE
    for _ in range(count):
        size = struct.unpack_from('<I', d, pos)[0]
        o, l = struct.unpack_from('<II', d, pos + 12)
        recs[rd(o, l)] = pos
        pos += 4 + size
    if pos != base:
        raise ValueError(f"เดินเรคคอร์ดจบที่ {pos} แต่ blob เริ่มที่ {base}: ไม่ใช่โครงสร้างที่คาดไว้")
    print(f"เรคคอร์ดใน .dat: {count}, blob base = {base}")

    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    pool, injected, skipped_empty, fixed = {}, 0, 0, []
    end = len(d)

    for x in rows:
        key = x['key']
        if key not in recs:
            raise ValueError(f"key {key} ไม่มีใน .dat")
        r = recs[key]
        for name, off_in_rec in FIELDS:
            th = x[name + '_pua']
            p = r + off_in_rec                              # pair ของ JP Slot
            o, l = struct.unpack_from('<II', d, p)
            if rd(o, l) != x[name + '_jp']:
                raise ValueError(f"{key}/{name}: JP ใน CSV ไม่ตรงกับ .dat")
            if not th:
                skipped_empty += 1
                continue
            new = FIX_VALUE.sub(r'<value \1>', th)
            if new != th:
                fixed.append((x['id'], key, name, th, new))
                th = new
            if '\x00' in th:
                raise ValueError(f"{key}/{name}: มี NUL")
            if MARKUP.findall(th) != MARKUP.findall(x[name + '_jp']) or \
               not all(TAG_OK.fullmatch(t) for t in MARKUP.findall(th)):
                raise ValueError(f"{key}/{name}: แท็กไม่ตรงกับต้นฉบับ {th!r}")
            b = th.encode('utf-8')
            if b not in pool:                               # สตริงซ้ำใช้ที่เดียวกัน
                pool[b] = end - base
                d.extend(b + b'\x00')
                end += len(b) + 1
            struct.pack_into('<II', d, p, pool[b], len(b))
            injected += 1

    struct.pack_into('<I', d, 8, len(d) - base)
    open(dst, 'wb').write(d)
    print(f"ฉีด {injected} ช่อง (สตริงไม่ซ้ำ {len(pool)}), ข้ามช่องว่าง {skipped_empty}, "
          f"เรคคอร์ดที่ไม่มีใน CSV คงเดิม {count - len(rows)}")
    for f in fixed:
        print(f"แก้แท็ก id={f[0]} {f[1]}/{f[2]}: {f[3]!r} -> {f[4]!r}")
    print(f"{src} {orig_len} -> {dst} {len(d)} bytes")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
