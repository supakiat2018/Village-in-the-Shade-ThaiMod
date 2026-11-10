#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_logtext.py - ฉีดคำแปลภาษาไทย (PUA) ลงช่อง JP ของ logtext.dat
Village in the Shade (Steam 1.30)  |  โหมด Safe Append & Re-point

โครงสร้างไฟล์ (Little-Endian) ที่ตรวจสอบจากไฟล์จริง:
  Header 12 ไบต์ : [0]=จำนวนเรคคอร์ด(101)  [1]=ผลรวมขนาด payload  [2]=blob_size
  Records        : uint32 size(=108) + payload 27 คำ (uint32) ต่อเนื่องกัน
  String Blob    : ท้ายไฟล์ ยาว blob_size (BLOB_BASE = filesize - blob_size)
                   สตริง UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, len ไม่รวม \\0

Payload (คำ w[i]):
  w[0]      = id (1000 + id ในตาราง)
  w[2],w[3] = Key (offset,len)  เช่น LOG_STAMINA_HALF
  w[4..17]  = 7 คู่ภาษา (off,len) เรียง JP,EN,FR,ES,ZH-TW,KO,ZH-CN
  w[18..26] = ตัวเลข (ไม่แตะ)
  ช่อง JP = w[4],w[5]  (แก้เฉพาะ 8 ไบต์นี้)

ตารางไม่มีคอลัมน์ JP จึงจับคู่ด้วย key, ตรวจ id (w[0]-1000 == id) และตรวจว่า
แท็ก <...> ในคำแปลตรงกับแท็กในข้อความ JP ของไฟล์ทุกตัว ก่อนฉีด

วิธีใช้:
  python3 inject_logtext.py logtext.dat logtext_PUA.csv out.dat
"""
import csv
import re
import struct
import sys

LANGS = 7
JP_WORD = 4
TAG = re.compile(r"<[^>]+>")


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
    src = sys.argv[1] if len(sys.argv) > 1 else "logtext.dat"
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "logtext_ตารางคำแปลไทย_PUA.csv"
    dst = sys.argv[3] if len(sys.argv) > 3 else "logtext_th.dat"

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

    for payload, size in recs:
        w = struct.unpack_from("<%dI" % (size // 4), orig, payload)
        key = read_str(orig, base, w[2], w[3])
        r = table.get(key)
        if r is None:
            untranslated.append(key)
            continue
        if int(r["id"]) != w[0] - 1000:
            raise SystemExit(f"id ไม่ตรง {key}: ไฟล์={w[0]} ตาราง={r['id']}")
        jp = read_str(orig, base, w[JP_WORD], w[JP_WORD + 1])
        th = r["ข้อความ_PUA"]
        if th == "":
            raise SystemExit(f"ข้อความ_PUA ว่าง: {key}")
        if TAG.findall(jp) != TAG.findall(th):
            raise SystemExit(f"แท็กไม่ตรง {key}: JP={TAG.findall(jp)} TH={TAG.findall(th)}")
        raw = th.encode("utf-8")
        new_off = blob_size + len(new_blob)
        new_blob.extend(raw + b"\x00")
        at = payload + 4 * JP_WORD
        struct.pack_into("<II", data, at, new_off, len(raw))
        allowed.update(range(at, at + 8))
        done[key] = th

    missing = [k for k in table if k not in done]
    if missing:
        raise SystemExit(f"key ในตารางที่ไม่พบในไฟล์ {len(missing)} รายการ เช่น {missing[:5]}")

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
        for lang in range(LANGS):
            a = read_str(orig, base, w[4 + 2 * lang], w[5 + 2 * lang])
            b = read_str(out, base2, w2[4 + 2 * lang], w2[5 + 2 * lang])
            if lang == 0 and key in done:
                assert b == done[key]
            else:
                assert a == b
    print(f"ฉีดสำเร็จ {len(done)} รายการ จาก {len(table)} แถวในตาราง (ตรวจย้อนกลับผ่าน)")
    print(f"blob_size: {blob_size} -> {bs2} | ขนาดไฟล์: {len(orig)} -> {len(out)}")
    if untranslated:
        print(f"[เตือน] เรคคอร์ดที่ไม่มีในตาราง {len(untranslated)} รายการ (คง JP เดิมไว้):")
        for k in untranslated:
            print("   ", k)
    print("เขียนไฟล์:", dst)


if __name__ == "__main__":
    main()
