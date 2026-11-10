#!/usr/bin/env python3
"""
inject_quest.py - ฉีดข้อความไทย (คอลัมน์ Thai_PUA) ลงช่องภาษาญี่ปุ่น (JP Slot) ใน quest.dat
ของเกม Village in the Shade (Steam PC v1.30) ด้วยวิธี Safe Append & Re-point

โครงสร้างไฟล์ (little-endian u32):
  Header 12 byte : [0]=จำนวนเรคคอร์ด(83)  [1]=? (ไม่แตะ)  [2]=ขนาด String Blob
  เรคคอร์ดต่อกันตั้งแต่ byte 12 จนถึง BLOB_BASE (= ขนาดไฟล์ - blob_size):
      u32 size              ขนาดเรคคอร์ด (ไม่รวมตัวมันเอง)  ตัวถัดไป = pos+4+size
      u32 id, u32 0
      pair KEY              (offset,length) ที่ +12
      u32 0                 ที่ +20
      บรรทัดข้อความ (Line) ละ 7 pair (JP, EN, FR, ES, ZH-TW, KO, ZH-CN)
          Line 0..3  : เริ่มที่ +24 + 56*Line
          Line 5..   : เริ่มที่ +344 + 60*(Line-5)     (Line 4 เป็นโครงสร้างอื่น ไม่มีใน CSV)
  String Blob : UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, length ไม่รวม \\0
  pair แรกของแต่ละบรรทัด = JP Slot

วิธีฉีด: ต่อสตริงไทยท้าย blob -> แก้เฉพาะ pair JP ของแถวที่มีใน CSV -> อัปเดต header[2]
(ไม่มี offset อื่นเลื่อน)  จับคู่แถว CSV ด้วย (Key, Line)

ใช้งาน:  python3 inject_quest.py quest.dat quest_PUA.csv quest_out.dat
"""
import csv
import re
import struct
import sys

csv.field_size_limit(10 ** 9)
HDR_SIZE = 12
TAG = re.compile(r'<cmd CMD_[A-Z0-9_]+(?: CMD_[A-Z0-9_]+)*(?: -offsetY -?\d+)?>|<player>')
MARKUP = re.compile(r'<[^>]*>')


def line_pos(line):
    return 24 + 56 * line if line <= 3 else 344 + 60 * (line - 5)


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

    recs, pos = {}, HDR_SIZE
    for _ in range(count):
        size = struct.unpack_from('<I', d, pos)[0]
        o, l = struct.unpack_from('<II', d, pos + 12)
        recs[rd(o, l)] = (pos, size)
        pos += 4 + size
    if pos != base:
        raise ValueError(f"เดินเรคคอร์ดจบที่ {pos} แต่ blob เริ่มที่ {base}")
    print(f"เรคคอร์ดใน .dat: {count}, blob base = {base}")

    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    pool, injected, warns = {}, 0, []
    end = len(d)
    for x in rows:
        key, line, th = x['Key'], int(x['Line']), x['Thai_PUA']
        if key not in recs:
            raise ValueError(f"Key {key} ไม่มีใน .dat")
        r, size = recs[key]
        rel = line_pos(line)
        if rel + 56 > 4 + size:
            raise ValueError(f"{key}/{line}: ตำแหน่งเกินขอบเรคคอร์ด")
        p = r + rel
        o, l = struct.unpack_from('<II', d, p)
        if rd(o, l) != x['ต้นฉบับ_JP']:
            raise ValueError(f"{key}/{line}: JP ใน CSV ไม่ตรงกับ .dat")
        if not th:
            continue
        if '\x00' in th:
            raise ValueError(f"{key}/{line}: มี NUL")
        tags = MARKUP.findall(th)
        if not all(TAG.fullmatch(t) for t in tags) or th.count('<') != len(tags) or th.count('>') != len(tags):
            raise ValueError(f"{key}/{line}: แท็กผิดรูป/ช่องว่างหาย {th!r}")
        if tags != MARKUP.findall(x['ต้นฉบับ_JP']):
            warns.append(f"{key}/{line}: แท็กไทยต่างจาก JP {MARKUP.findall(x['ต้นฉบับ_JP'])} -> {tags}")
        b = th.encode('utf-8')
        if b not in pool:
            pool[b] = end - base
            d.extend(b + b'\x00')
            end += len(b) + 1
        struct.pack_into('<II', d, p, pool[b], len(b))
        injected += 1

    struct.pack_into('<I', d, 8, len(d) - base)
    open(dst, 'wb').write(d)
    print(f"ฉีด {injected} ข้อความ (ไม่ซ้ำ {len(pool)}), เรคคอร์ดที่ไม่มีใน CSV: {count - len({x['Key'] for x in rows})}")
    for w in warns:
        print("คำเตือน:", w)
    print(f"{orig_len} -> {len(d)} bytes ({dst})")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
