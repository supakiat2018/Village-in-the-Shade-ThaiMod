#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_reminiscence.py - ฉีดคำแปลภาษาไทย (PUA) ลงช่อง JP ของ reminiscence.dat
Village in the Shade (Steam 1.30)  |  โหมด Safe Append & Re-point

โครงสร้างไฟล์ (Little-Endian) ที่ตรวจสอบจากไฟล์จริง:
  Header 12 ไบต์ : [0]=จำนวนเรคคอร์ด(5)  [1]=ผลรวมขนาด payload  [2]=blob_size
  Records        : uint32 size + payload ต่อเนื่องกัน (ขนาดไม่เท่ากัน)
  String Blob    : ท้ายไฟล์ ยาว blob_size (BLOB_BASE = filesize - blob_size)
                   สตริง UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, len ไม่รวม \\0

Payload ของเรคคอร์ด (คำ uint32 w[i]):
  w[2],w[3]  = Key (offset,len)
  w[4]       = G จำนวนกลุ่ม (group)
  จากนั้น G กลุ่ม เริ่มที่ w[5] แต่ละกลุ่ม =
       4 คำ header (kind, flag, id, c)  c = จำนวนบรรทัดในกลุ่ม
       c บรรทัด บรรทัดละ 21 คำ = 7 คู่ภาษา (off,len) x 7 (JP,EN,FR,ES,ZH-TW,KO,ZH-CN) + 7 คำ flag
  ท้ายเรคคอร์ด 4 คำเป็น 0
  เลข Line ในตารางนับต่อเนื่องข้ามกลุ่ม (0,1,2,...)
  ช่อง JP = คู่แรกของแต่ละบรรทัด (แก้เฉพาะ 8 ไบต์นี้)

จับคู่ตารางด้วย (Key, Line) และตรวจเทียบ ต้นฉบับ_JP ทุกบรรทัดก่อนฉีด

วิธีใช้:
  python3 inject_reminiscence.py reminiscence.dat reminiscence_PUA.csv out.dat
"""
import csv
import struct
import sys

LANGS = 7


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


def line_slots(data, base, payload, size):
    """คืน (key, w, [(line_no, word_index_ของคู่_JP)])"""
    nw = size // 4
    w = struct.unpack_from("<%dI" % nw, data, payload)
    key = read_str(data, base, w[2], w[3])
    k, line, slots = 5, 0, []
    for _ in range(w[4]):
        c = w[k + 3]
        k += 4
        for _ in range(c):
            slots.append((line, k))
            line += 1
            k += 21
    if k + 4 != nw or any(w[k:]):
        raise SystemExit(f"{key}: ท้ายเรคคอร์ดไม่ตรงโครงสร้างที่คาด (k={k}, nw={nw})")
    return key, w, slots


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "reminiscence.dat"
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "reminiscence_ตารางคำแปลไทย_PUA.csv"
    dst = sys.argv[3] if len(sys.argv) > 3 else "reminiscence_th.dat"

    orig = open(src, "rb").read()
    data = bytearray(orig)
    cnt, rec_total, blob_size, base, recs = parse(orig)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    table = {}
    for r in rows:
        k = (r["Key"], int(r["Line"]))
        if k in table:
            raise SystemExit(f"แถวซ้ำในตาราง: {k}")
        table[k] = r

    new_blob = bytearray()
    done, skipped_empty, allowed = {}, 0, set(range(8, 12))

    for payload, size in recs:
        key, w, slots = line_slots(orig, base, payload, size)
        for line, wi in slots:
            jp = read_str(orig, base, w[wi], w[wi + 1])
            t = table.get((key, line))
            if t is None:
                if jp != "":
                    raise SystemExit(f"{key} line {line}: ในไฟล์มี JP แต่ตารางไม่มีแถว")
                skipped_empty += 1
                continue
            if t["ต้นฉบับ_JP"] != jp:
                raise SystemExit(f"JP ไม่ตรง {key} line {line}: ไฟล์={jp!r} ตาราง={t['ต้นฉบับ_JP']!r}")
            if t["Thai_PUA"] == "":
                raise SystemExit(f"Thai_PUA ว่าง {key} line {line}")
            raw = t["Thai_PUA"].encode("utf-8")
            new_off = blob_size + len(new_blob)
            new_blob.extend(raw + b"\x00")
            at = payload + 4 * wi
            struct.pack_into("<II", data, at, new_off, len(raw))
            allowed.update(range(at, at + 8))
            done[(key, line)] = t["Thai_PUA"]

    missing = [k for k in table if k not in done]
    if missing:
        raise SystemExit(f"แถวในตารางที่ไม่ได้ถูกฉีด {len(missing)} แถว เช่น {missing[:5]}")

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
        key, w, slots = line_slots(orig, base, p1, s1)
        w2 = struct.unpack_from("<%dI" % (s2 // 4), out, p2)
        for line, wi in slots:
            for lang in range(LANGS):
                a = read_str(orig, base, w[wi + 2 * lang], w[wi + 2 * lang + 1])
                b = read_str(out, base2, w2[wi + 2 * lang], w2[wi + 2 * lang + 1])
                if lang == 0 and (key, line) in done:
                    assert b == done[(key, line)]
                else:
                    assert a == b
    print(f"ฉีดสำเร็จ {len(done)} บรรทัด จาก {len(table)} แถวในตาราง (ตรวจย้อนกลับผ่าน)")
    print(f"blob_size: {blob_size} -> {bs2} | ขนาดไฟล์: {len(orig)} -> {len(out)}")
    print(f"บรรทัดว่างในไฟล์ที่ไม่มีในตาราง (ข้ามปกติ): {skipped_empty}")
    print("เขียนไฟล์:", dst)


if __name__ == "__main__":
    main()
