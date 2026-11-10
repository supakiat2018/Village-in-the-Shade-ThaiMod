#!/usr/bin/env python3
"""Inject Thai (PUA-compressed) text into the 'ja' slot of the NEW
Village in the Shade talknameplate.dat (PC Steam v1.30+).

This file uses a 9-pointer-per-record layout (one more field than the
older talknameplate.dat this project worked with before — a 9th,
likely-Chinese-variant field follows 'ko'). Layout, derived empirically
from the uploaded binary and verified by an exact self round-trip:

  header (12 B): num_records, sum(record body sizes), blob_size
  record (120 B): u32 body_size(=116), u32 index, u32 0,
                   9 x (u32 offset, u32 length)  -> 9 string pointers
                   36 B opaque tail (talker-specific flags/ids, kept verbatim)
  blob: UTF-8 strings, each NUL-terminated, sequential, no gaps.

Columns (confirmed from decoded content):
  0 key (TALK_NAME_ID_...)   1 talker_id (TALKER_...)   2 ja   3 en
  4 fr   5 es   6 zh (Traditional, as found)   7 ko   8 zh2 (second CJK variant)

Only column 2 (ja) is modified -- the game's font-compressed Thai_PUA
text from talknameplate_translated.csv, matched to each record by its
TALK_NAME_ID key.
"""
import csv, struct, sys, json

HDR, PAIRS_AT = 12, 12

def parse(d, npairs):
    n, f2, blob_size, body = struct.unpack_from("<4I", d, 0)
    rec_sz = body + 4
    blob_start = HDR + n * rec_sz
    blob = d[blob_start:]
    assert len(blob) == blob_size, (len(blob), blob_size)
    recs, rows = [], []
    for r in range(n):
        base = HDR + r * rec_sz
        rec = bytearray(d[base:base + rec_sz])
        row = []
        for k in range(npairs):
            off, ln = struct.unpack_from("<2I", rec, PAIRS_AT + 8 * k)
            assert blob[off + ln] == 0, f"rec {r} col {k}: no NUL terminator"
            row.append(blob[off:off + ln].decode("utf-8"))
        recs.append(rec); rows.append(row)
    return (n, f2, body), recs, rows

def build(hdr, recs, rows, npairs):
    n, f2, body = hdr
    blob = bytearray(); out_recs = []
    for rec, row in zip(recs, rows):
        rec = bytearray(rec)
        for k, s in enumerate(row):
            b = s.encode("utf-8")
            struct.pack_into("<2I", rec, PAIRS_AT + 8 * k, len(blob), len(b))
            blob += b + b"\x00"
        out_recs.append(bytes(rec))
    return struct.pack("<3I", n, f2, len(blob)) + b"".join(out_recs) + bytes(blob)

if __name__ == "__main__":
    src, csv_path, dst = sys.argv[1:4]
    NPAIRS = 9
    JA = 2

    d = open(src, "rb").read()
    hdr, recs, rows = parse(d, NPAIRS)
    # self-test: rebuilding the untouched data must reproduce the original byte-for-byte
    rebuilt = build(hdr, recs, rows, NPAIRS)
    assert rebuilt == d, f"round-trip mismatch: {len(rebuilt)} vs {len(d)} bytes"

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f); head = next(rd)
        trows = [r for r in rd if r]
    # translated.csv columns: ID, TALK_NAME_ID, Talker_Code, Japanese, English, Thai_Normal, Thai_PUA
    assert head[1] == "TALK_NAME_ID" and head[-1] == "Thai_PUA", head
    thai = {r[1]: r[-1] for r in trows}
    assert set(thai) == {r[0] for r in rows}, "TALK_NAME_ID sets differ between dat and csv"

    new_rows = [list(r) for r in rows]
    for row in new_rows:
        row[JA] = thai[row[0]]

    out = build(hdr, recs, new_rows, NPAIRS)
    open(dst, "wb").write(out)
    print("wrote", dst, len(out), "bytes")
