#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_trophy.py - ฉีดคำแปลภาษาไทย (PUA) ลงช่อง JP ของ trophy.dat
Village in the Shade (Steam 1.30)  |  โหมด Safe Append & Re-point

โครงสร้างไฟล์ (Little-Endian) ที่ตรวจสอบจากไฟล์จริง:
  Header 12 ไบต์ : [0]=จำนวนเรคคอร์ด(52)  [1]=ผลรวมขนาด payload  [2]=blob_size
  Records        : uint32 size(=172) + payload 43 คำ (uint32) ต่อเนื่องกัน
  String Blob    : ท้ายไฟล์ ยาว blob_size (BLOB_BASE = filesize - blob_size)
                   สตริง UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, len ไม่รวม \\0

Payload (คำ uint32 w[i]):
  w[2],w[3] = Key (offset,len) เช่น TROPHY_ID_001
  ฟิลด์ข้อความ 2 ฟิลด์ ฟิลด์ละ 7 คู่ภาษา (off,len) เรียง JP,EN,FR,ES,ZH-TW,KO,ZH-CN
    ชื่อถ้วย     เริ่มที่ w[9]   (ตาราง: ชื่อถ้วย_PUA)
    คำอธิบาย    เริ่มที่ w[25]  (ตาราง: คำอธิบาย_PUA)
  ที่เหลือเป็นตัวเลข (ไม่แตะ)  |  ช่อง JP = คู่แรกของแต่ละฟิลด์ (แก้เฉพาะ 8 ไบต์/ฟิลด์)

ตารางไม่มีคอลัมน์ JP จึงจับคู่ด้วย key และตรวจว่า
  - ฟิลด์ที่ JP ในไฟล์ว่าง = ช่องในตารางว่าง (และกลับกัน)
  - แท็ก <...> ในคำแปลตรงกับแท็กใน JP ของไฟล์

วิธีใช้:
  python3 inject_trophy.py trophy.dat trophy_PUA.csv out.dat
"""
import csv
import re
import struct
import sys

LANGS = 7
TAG = re.compile(r"<[^>]+>")
FIELDS = [("ชื่อถ้วย_PUA", 9), ("คำอธิบาย_PUA", 25)]


def parse(data):
    cnt, rec_total, blob_size = struct.unpack_from("<3I", data, 0)
    base = len(data) - blob_size
    pos, recs = 12, []
    for _ in range(cnt):
        sz = struct.unpack_from("<I", data, pos)[0]
        recs.append((pos + 4, sz))
        pos += 4 + sz
    if pos != base:
        raise SystemExit(f"โครงสร้างไม่ตรง: จบเรคคอร์ดที่ {pos} แต่ BLOB_BASE={base}")
    return cnt, rec_total, blob_size, base, recs


def read_str(data, base, off, ln):
    e = base + off + ln
    if e >= len(data) or data[e] != 0:
        raise SystemExit(f"สตริง offset={off} len={ln} ไม่ลงท้ายด้วย \\0")
    return data[base + off:e].decode("utf-8")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "trophy.dat"
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "trophy_ตารางคำแปลไทย_PUA.csv"
    dst = sys.argv[3] if len(sys.argv) > 3 else "trophy_th.dat"

    orig = open(src, "rb").read()
    data = bytearray(orig)
    cnt, rec_total, blob_size, base, recs = parse(orig)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        table = {}
        for r in csv.DictReader(f):
            if r["key"] in table:
                raise SystemExit(f"key ซ้ำในตาราง: {r['key']}")
            table[r["key"]] = r

    new_blob = bytearray()
    done, untranslated, allowed = {}, [], set(range(8, 12))
    n_fields = 0

    for payload, size in recs:
        w = struct.unpack_from("<%dI" % (size // 4), orig, payload)
        key = read_str(orig, base, w[2], w[3])
        r = table.get(key)
        if r is None:
            untranslated.append(key)
            continue
        for col, wi in FIELDS:
            for q in range(LANGS):                      # ตรวจว่าพอยน์เตอร์ทั้ง 7 ภาษาเป็นสตริงจริง
                read_str(orig, base, w[wi + 2 * q], w[wi + 2 * q + 1])
            jp = read_str(orig, base, w[wi], w[wi + 1])
            th = r[col]
            if (jp == "") != (th == ""):
                raise SystemExit(f"{key} [{col}]: JP ในไฟล์={jp!r} แต่ตาราง={th!r}")
            if th == "":
                continue
            if TAG.findall(jp) != TAG.findall(th):
                raise SystemExit(f"แท็กไม่ตรง {key} [{col}]: JP={TAG.findall(jp)} TH={TAG.findall(th)}")
            raw = th.encode("utf-8")
            new_off = blob_size + len(new_blob)
            new_blob.extend(raw + b"\x00")
            at = payload + 4 * wi
            struct.pack_into("<II", data, at, new_off, len(raw))
            allowed.update(range(at, at + 8))
            done[(key, col)] = th
            n_fields += 1

    missing = [k for k in table if k not in {x for x, _ in done} and
               any(table[k][c] for c, _ in FIELDS)]
    if missing:
        raise SystemExit(f"key ในตารางที่ไม่พบในไฟล์: {missing[:5]}")

    data.extend(new_blob)
    struct.pack_into("<I", data, 8, blob_size + len(new_blob))
    open(dst, "wb").write(data)

    # ---------- ตรวจสอบไฟล์ผลลัพธ์ ----------
    out = bytes(data)
    cnt2, rt2, bs2, base2, recs2 = parse(out)
    assert base2 == base and cnt2 == cnt and rt2 == rec_total
    assert out[base:base + blob_size] == orig[base:], "blob เดิมต้องไม่เปลี่ยน"
    diff = [i for i in range(len(orig)) if orig[i] != out[i] and i not in allowed]
    assert not diff, f"พบไบต์เปลี่ยนนอกขอบเขต {len(diff)} ตำแหน่ง"
    for (p1, s1), (p2, s2) in zip(recs, recs2):
        w = struct.unpack_from("<%dI" % (s1 // 4), orig, p1)
        w2 = struct.unpack_from("<%dI" % (s2 // 4), out, p2)
        key = read_str(orig, base, w[2], w[3])
        for col, wi in FIELDS:
            for lang in range(LANGS):
                a = read_str(orig, base, w[wi + 2 * lang], w[wi + 2 * lang + 1])
                b = read_str(out, base2, w2[wi + 2 * lang], w2[wi + 2 * lang + 1])
                if lang == 0 and (key, col) in done:
                    assert b == done[(key, col)]
                else:
                    assert a == b
    print(f"ฉีดสำเร็จ {n_fields} ฟิลด์ จาก {len(table)} รายการในตาราง (ตรวจย้อนกลับผ่าน)")
    print(f"blob_size: {blob_size} -> {bs2} | ขนาดไฟล์: {len(orig)} -> {len(out)}")
    if untranslated:
        print(f"[เตือน] เรคคอร์ดที่ไม่มีในตาราง {len(untranslated)} รายการ (คง JP เดิมไว้):")
        for k in untranslated:
            print("   ", k)
    print("เขียนไฟล์:", dst)


if __name__ == "__main__":
    main()
