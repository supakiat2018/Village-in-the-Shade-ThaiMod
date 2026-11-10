#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_lostbook.py - ฉีดคำแปลภาษาไทย (PUA) ลงช่อง JP ของ lostbook.dat
Village in the Shade (Steam 1.30)  |  โหมด Safe Append & Re-point

โครงสร้างไฟล์ (Little-Endian) ที่ตรวจสอบจากไฟล์จริง:
  Header 12 ไบต์ : [0]=จำนวนเรคคอร์ด(55)  [1]=ผลรวมขนาด payload  [2]=blob_size
  Records        : uint32 size + payload ต่อเนื่องกัน (ขนาด 712/656/544 ไบต์)
  String Blob    : ท้ายไฟล์ ยาว blob_size (BLOB_BASE = filesize - blob_size)
                   สตริง UTF-8 ลงท้าย \\0, offset นับจาก BLOB_BASE, len ไม่รวม \\0

Payload ของเรคคอร์ด (นับเป็นคำ uint32 w[i]):
  w[2],w[3]       = Key (offset,len)
  w[4..17]        = Line 0 (ชื่อหนังสือ) 7 ภาษา คู่ละ (off,len) เรียง JP,EN,FR,ES,ZH-TW,KO,ZH-CN
  w[18]           = n จำนวนบรรทัดเนื้อความ
  w[19 + 14*j ..] = Line 1+j  7 ภาษา
  ส่วนท้ายเป็นตัวเลข (ไม่มีสตริง)
  ช่อง JP = คู่แรกของแต่ละกลุ่ม 7 ภาษา (แก้เฉพาะ 8 ไบต์นี้)

จับคู่กับตารางด้วย (Key, Line) และตรวจเทียบ ต้นฉบับ_JP ทุกบรรทัดก่อนฉีด

วิธีใช้:
  python3 inject_lostbook.py lostbook.dat lostbook_PUA.csv lostbook_out.dat
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
        recs.append((pos + 4, sz))  # (ตำแหน่ง payload, ขนาด)
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
    """คืน (key, {line_no: ตำแหน่งไบต์ของคู่ JP ในไฟล์}) ของเรคคอร์ดนี้"""
    nw = size // 4
    w = struct.unpack_from("<%dI" % nw, data, payload)
    key = read_str(data, base, w[2], w[3])
    n = w[18]
    slots = {0: 4}
    for j in range(n):
        slots[1 + j] = 19 + 14 * j
    tail = 19 + 14 * n
    return key, w, slots, tail


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "lostbook.dat"
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "lostbook_ตารางคำแปลไทย_PUA.csv"
    dst = sys.argv[3] if len(sys.argv) > 3 else "lostbook_th.dat"

    data = bytearray(open(src, "rb").read())
    orig = bytes(data)
    cnt, rec_total, blob_size, base, recs = parse(orig)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    table = {}
    for r in rows:
        k = (r["Key"], int(r["Line"]))
        if k in table:
            raise SystemExit(f"แถวซ้ำในตาราง: {k}")
        table[k] = r
    csv_lines = {}
    for (k, ln) in table:
        csv_lines[k] = max(csv_lines.get(k, -1), ln)

    new_blob = bytearray()
    done = {}                      # (key,line) -> Thai
    untranslated = []              # เรคคอร์ดที่ไม่มีในตาราง
    skipped_empty = 0

    def inject(payload_pos_words, w, widx, key, line):
        nonlocal skipped_empty
        t = table.get((key, line))
        off, ln = w[widx], w[widx + 1]
        jp = read_str(orig, base, off, ln)
        if t is None:
            if jp != "":
                raise SystemExit(f"{key} line {line}: ในไฟล์มี JP แต่ตารางไม่มีแถว")
            skipped_empty += 1
            return
        if t["ต้นฉบับ_JP"] != jp:
            raise SystemExit(f"JP ไม่ตรง {key} line {line}: ไฟล์={jp!r} ตาราง={t['ต้นฉบับ_JP']!r}")
        th = t["Thai_PUA"]
        if th == "":
            raise SystemExit(f"Thai_PUA ว่าง {key} line {line}")
        raw = th.encode("utf-8")
        new_off = blob_size + len(new_blob)
        new_blob.extend(raw + b"\x00")
        struct.pack_into("<II", data, payload_pos_words + 4 * widx, new_off, len(raw))
        done[(key, line)] = th

    for (payload, size) in recs:
        key, w, slots, tail = line_slots(orig, base, payload, size)
        if key not in csv_lines:
            untranslated.append(key)
            continue
        for line, widx in slots.items():
            inject(payload, w, widx, key, line)
        if csv_lines[key] > w[18]:
            raise SystemExit(f"{key}: ตารางมี Line สูงสุด {csv_lines[key]} แต่ไฟล์มี {w[18]} บรรทัดเนื้อความ")

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
    # ไบต์นอกพอยน์เตอร์ JP ที่ฉีดต้องเหมือนเดิมทุกไบต์ (ยกเว้น Header[2])
    allowed = set(range(8, 12))
    for (payload, size) in recs:
        key, w, slots, tail = line_slots(orig, base, payload, size)
        if key not in csv_lines:
            continue
        widxs = list(slots.values())
        for wi in widxs:
            allowed.update(range(payload + 4 * wi, payload + 4 * wi + 8))
    diff = [i for i in range(len(orig)) if orig[i] != out[i] and i not in allowed]
    assert not diff, f"พบไบต์เปลี่ยนนอกขอบเขต {len(diff)} ตำแหน่ง"
    # อ่านย้อนกลับ: ทุกบรรทัดที่ฉีดต้องได้ข้อความไทย และภาษาอื่นต้องเหมือนเดิม
    for (payload, size), (p2, s2) in zip(recs, recs2):
        key, w, slots, tail = line_slots(orig, base, payload, size)
        if key not in csv_lines:
            continue
        w2 = struct.unpack_from("<%dI" % (size // 4), out, p2)
        widxs = dict(slots)
        for line, wi in widxs.items():
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
    if untranslated:
        print(f"[เตือน] เรคคอร์ดที่ไม่มีในตาราง {len(untranslated)} รายการ (คง JP เดิมไว้):")
        for k in untranslated:
            print("   ", k)
    print("เขียนไฟล์:", dst)


if __name__ == "__main__":
    main()
