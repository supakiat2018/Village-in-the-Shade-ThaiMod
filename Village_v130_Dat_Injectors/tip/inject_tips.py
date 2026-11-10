#!/usr/bin/env python3
"""
inject_tips.py - ฉีดข้อความไทย (คอลัมน์ Thai_PUA) ลงช่องภาษาญี่ปุ่น (Slot 0) ใน tips.dat
ของเกม Village in the Shade (Steam PC v1.30)

โครงสร้างไฟล์ tips.dat (little-endian, ทุกค่าเป็น u32):
  Header   : [0]=จำนวนทิป(76)  [1]=?  [2]=ขนาด string blob  [3]=?  [4]=?  [5]=?
  ตารางทิป เริ่มที่ 0x18 ต่อเนื่องกัน ทิปละ:
      8 pairs   (offset,length)  = KEY + ชื่อทิป 7 ภาษา   (Slot 0 = JP)
      u32       = จำนวนบรรทัด n
      n*7 pairs (offset,length)  = ข้อความ 7 ภาษาต่อบรรทัด (Slot 0 = JP)
      64 bytes  = metadata ท้ายทิป (ไม่แตะ)
  String blob : เริ่มที่ BLOB_BASE (=ท้ายตาราง) เป็น UTF-8 ลงท้ายด้วย \\0
  offset ของทุก pair นับจาก BLOB_BASE, length = จำนวน byte (ไม่รวม \\0)

วิธีฉีด: ต่อสตริงไทย (UTF-8 + \\0) ท้าย blob, แก้เฉพาะ pair ของ Slot 0 ให้ชี้ไปที่ใหม่,
และอัปเดตขนาด blob ใน header[2]  -> ไม่มี offset อื่นเลื่อน

ใช้งาน:
  python3 inject_tips.py tips.dat tips_PUA.csv tips_out.dat
"""
import csv
import re
import struct
import sys

BLOB_BASE = 21132          # 0x528C : จุดเริ่ม string blob (ท้ายตาราง pointer)
TABLE_START = 24           # 0x18   : จุดเริ่มตารางทิปแรก
HDR_BLOB_SIZE = 2          # header[2] = ขนาด blob (ไฟล์ - BLOB_BASE)
NUM_LANGS = 7
TIP_META = 64              # ขนาด metadata ท้ายทิป

# แท็กคำสั่งปุ่ม: ต้องมี space ครบ เช่น <cmd CMD_UNIT_MOVE_STICK -offsetY -5>
TAG_OK = re.compile(r'<cmd CMD_[A-Z0-9_]+(?: CMD_[A-Z0-9_]+)*(?: -offsetY -?\d+)?>')


def read_str(d, off, ln):
    a = BLOB_BASE + off
    if d[a + ln] != 0:
        raise ValueError(f"string ที่ offset {off} ไม่ได้ลงท้ายด้วย NUL")
    return d[a:a + ln].decode('utf-8')


def parse_tips(d):
    """คืน list ของทิป: key, ตำแหน่ง pair (ไฟล์) ของ title/lines Slot 0"""
    tips = []
    pos = TABLE_START
    while pos < BLOB_BASE - 100:
        off, ln = struct.unpack_from('<II', d, pos)
        if d[BLOB_BASE + off:BLOB_BASE + off + 5] != b'TIPS_':
            break
        n = struct.unpack_from('<I', d, pos + 8 * 8)[0]
        lines0 = [pos + 68 + 56 * j for j in range(n)]   # pair Slot 0 ของแต่ละบรรทัด
        tips.append({'key': read_str(d, off, ln), 'title0': pos + 8, 'lines0': lines0})
        pos += 68 + n * 56 + TIP_META
    return tips


def check_tags(text, where):
    """ตรวจว่าแท็ก <cmd ...> ทุกตัวครบ ช่องว่างไม่หาย"""
    found = TAG_OK.findall(text)
    if text.count('<') != len(found) or text.count('>') != len(found):
        raise ValueError(f"{where}: แท็กผิดรูป/ช่องว่างหาย -> {text!r}")
    if '<cmdCMD' in text:
        raise ValueError(f"{where}: พบ <cmdCMD (ช่องว่างหาย)")


def main(src, csv_path, dst):
    d = bytearray(open(src, 'rb').read())
    assert struct.unpack_from('<I', d, HDR_BLOB_SIZE * 4)[0] == len(d) - BLOB_BASE, \
        "header[2] ไม่ตรงกับขนาด blob: ไม่ใช่ tips.dat เวอร์ชันนี้"

    rows = {}
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            rows[(r['Tip_Key'], r['Item_Type'])] = r

    tips = parse_tips(bytes(d))
    print(f"พบ {len(tips)} ทิปใน .dat, {len(rows)} แถวใน CSV")

    blob_end = len(d)
    injected = skipped = 0

    def inject(pair_pos, row, label):
        nonlocal blob_end, injected
        # ตรวจว่าแถว CSV ตรงกับ Slot 0 เดิม (ต้นฉบับ JP)
        off, ln = struct.unpack_from('<II', d, pair_pos)
        orig = read_str(d, off, ln)
        if orig != row['Original_JP']:
            raise ValueError(f"{label}: JP ใน CSV ไม่ตรงกับ .dat\n  dat={orig!r}\n  csv={row['Original_JP']!r}")
        th = row['Thai_PUA']
        if not th:
            raise ValueError(f"{label}: Thai_PUA ว่าง")
        if '\x00' in th:
            raise ValueError(f"{label}: มี NUL ในข้อความ")
        check_tags(th, label)
        b = th.encode('utf-8')
        new_off = blob_end - BLOB_BASE
        d.extend(b + b'\x00')
        blob_end += len(b) + 1
        struct.pack_into('<II', d, pair_pos, new_off, len(b))   # (Offset, Length) ใหม่
        injected += 1

    for t in tips:
        key = t['key']
        if (key, 'TITLE') not in rows:
            print(f"ข้าม {key}: ไม่มีใน CSV (คงภาษาญี่ปุ่นเดิม)")
            skipped += 1
            continue
        inject(t['title0'], rows[(key, 'TITLE')], f"{key}/TITLE")
        for j, p in enumerate(t['lines0'], 1):
            row = rows.get((key, f'LINE_{j}'))
            if row is None:
                raise ValueError(f"{key}: ไม่มี LINE_{j} ใน CSV")
            inject(p, row, f"{key}/LINE_{j}")

    struct.pack_into('<I', d, HDR_BLOB_SIZE * 4, len(d) - BLOB_BASE)
    open(dst, 'wb').write(d)
    print(f"ฉีดแล้ว {injected} ข้อความ, ข้าม {skipped} ทิป -> {dst} ({len(d)} bytes)")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
