#!/usr/bin/env python3
"""
inject_string.py - ฉีดข้อความไทย (คอลัมน์ Thai_PUA) ลงช่องภาษาญี่ปุ่น (JP Slot) ใน string.dat
ของเกม Village in the Shade (Steam PC v1.30) ด้วยวิธี Safe Append & Re-point

โครงสร้างไฟล์ (little-endian u32):
  Header 12 byte : [0]=จำนวนเรคคอร์ด(408)  [1]=? (ไม่แตะ)  [2]=ขนาด String Blob
  เรคคอร์ดต่อกันตั้งแต่ byte 12 จนถึง BLOB_BASE (= ขนาดไฟล์ - blob_size) ขนาดเรคคอร์ดละ 88:
      u32 size(=88)        ตัวถัดไป = pos+4+size
      u32 ID (1000..)      ที่ +4
      pair KEY             (offset,length) ที่ +12
      pair x7              ที่ +20 : JP, EN, FR, ES, ZH-TW, KO, ZH-CN   (pair แรก = JP Slot)
  String Blob : UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, length ไม่รวม \\0

วิธีฉีด: ต่อสตริงไทยท้าย blob -> แก้เฉพาะ pair JP -> อัปเดต header[2]  (ไม่มี offset อื่นเลื่อน)
จับคู่แถว CSV ด้วย Key (ตรวจ ID ซ้ำอีกชั้น)

กฎพิเศษ:
 - แถวที่ Thai_PUA ว่าง หรือเหมือน JP ทุกตัวอักษร (เช่น "save", ".systemsave") -> ไม่แตะ
 - แถวที่ตารางคำแปลเลื่อนผิดบรรทัด (REALIGN / DROP ด้านล่าง) แก้ตามเนื้อหา
   ปิดได้ด้วย  --no-realign  (จะฉีดตาม CSV ตรง ๆ ซึ่งข้อความผิดบรรทัด)

ใช้งาน:  python3 inject_string.py string.dat string_PUA.csv string_out.dat [--no-realign]
"""
import csv
import re
import struct
import sys

csv.field_size_limit(10 ** 9)
HDR_SIZE = 12
JP_PAIR = 20

# ตารางคำแปลคอลัมน์ไทยของ 6 แถวนี้เลื่อนผิด 1 บรรทัด (ตรวจจากความหมาย EN/JP และจำนวน <value N>)
#   key ปลายทาง : key ที่ถือคำแปลที่ถูกต้องอยู่ใน CSV
REALIGN = {
    'STR_ID_CATALOG_TITLE':        'STR_ID_SAVE_FILE_LIST_DISP_NAME',   # แคตตาล็อกเฟอร์นิเจอร์
    'STR_ID_CATALOG_ORDER_HEADER': 'STR_ID_CATALOG_TITLE',              # เฟอร์นิเจอร์ที่สั่งในวันนี้
    'STR_ID_CATALOG_NUMBER':       'STR_ID_CATALOG_ORDER_HEADER',       # <value 1> ชิ้น
    'STR_ID_MEMO_CATALOG':         'STR_ID_CATALOG_NUMBER',             # แคตตาล็อกเฟอร์นิเจอร์
}
# ไม่มีคำแปลที่ถูกต้องในตาราง -> คง JP เดิม
DROP = {'STR_ID_SAVE_FILE_LIST_DISP_NAME', 'STR_ID_BIRTHDAY_SELECT'}

GOOD_TAGS = [
    r'<icon <value \d+> -?\d+ -?\d+>',
    r'<value \d+>',
    r'</?(?:br|half|c|size|strong)>',
    r'<c [a-z]+>',
    r'<size \d+(?:\.\d+)? \d+(?:\.\d+)?>',
    r'<player>',
    r'<cmd CMD_[A-Z0-9_]+(?: CMD_[A-Z0-9_]+)*(?: -offsetY -?\d+)?>',
]
GOOD = re.compile('|'.join(GOOD_TAGS))
ANY = re.compile(r'<icon <value \d+> -?\d+ -?\d+>|<[^<>]*>')


def tags_ok(text):
    """ทุก '<' '>' ต้องอยู่ในแท็กที่รู้จักและช่องว่างครบ"""
    rest = GOOD.sub('', text)
    return '<' not in rest and '>' not in rest


def main(src, csv_path, dst, realign=True):
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
        rid = struct.unpack_from('<I', d, pos + 4)[0]
        o, l = struct.unpack_from('<II', d, pos + 12)
        recs[rd(o, l)] = (pos, rid)
        pos += 4 + size
    if pos != base:
        raise ValueError(f"เดินเรคคอร์ดจบที่ {pos} แต่ blob เริ่มที่ {base}")
    print(f"เรคคอร์ดใน .dat: {count}, blob base = {base}")

    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    thai = {x['Key']: x['Thai_PUA'] for x in rows}
    pool, injected, same, empty, notes = {}, 0, 0, 0, []
    end = len(d)

    for x in rows:
        key = x['Key']
        if key not in recs:
            raise ValueError(f"Key {key} ไม่มีใน .dat")
        r, rid = recs[key]
        if str(rid) != x['ID']:
            raise ValueError(f"{key}: ID ไม่ตรง dat={rid} csv={x['ID']}")
        p = r + JP_PAIR
        o, l = struct.unpack_from('<II', d, p)
        jp = rd(o, l)
        if jp != x['ต้นฉบับ_JP']:
            raise ValueError(f"{key}: JP ใน CSV ไม่ตรงกับ .dat")

        th = thai[key]
        if realign:
            if key in DROP:
                notes.append(f"{key}: คำแปลใน CSV ผิดแถวและไม่มีคำแปลที่ถูก -> คง JP เดิม")
                continue
            if key in REALIGN:
                th = thai[REALIGN[key]]
                notes.append(f"{key}: ใช้คำแปลจากแถว {REALIGN[key]} (CSV เลื่อนบรรทัด)")
        if not th:
            empty += 1
            continue
        if th == jp:
            same += 1
            continue
        if '\x00' in th:
            raise ValueError(f"{key}: มี NUL")
        if not tags_ok(th):
            raise ValueError(f"{key}: แท็กผิดรูป/ช่องว่างหาย {th!r}")
        a, b = sorted(ANY.findall(jp)), sorted(ANY.findall(th))
        if a != b:
            notes.append(f"{key}: แท็กต่างจาก JP {a} -> {b}")
        bb = th.encode('utf-8')
        if bb not in pool:
            pool[bb] = end - base
            d.extend(bb + b'\x00')
            end += len(bb) + 1
        struct.pack_into('<II', d, p, pool[bb], len(bb))
        injected += 1

    struct.pack_into('<I', d, 8, len(d) - base)
    open(dst, 'wb').write(d)
    print(f"ฉีด {injected} ข้อความ (ไม่ซ้ำ {len(pool)}), ข้ามแถวว่าง {empty}, ข้ามแถวเหมือน JP {same}")
    for n in notes:
        print("หมายเหตุ:", n)
    print(f"{orig_len} -> {len(d)} bytes ({dst})")


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) != 3:
        sys.exit(__doc__)
    main(*a, realign='--no-realign' not in sys.argv)
