import os

header_path = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\keyboard_v120_patch.h"
with open(header_path, encoding="utf-8") as f:
    lines = f.readlines()

hira_map = {}
kata_map = {}

for line in lines:
    if "{" in line and "}" in line and "0x" in line:
        parts = [p.strip().strip('"') for p in line.split('"')]
        if len(parts) >= 7:
            thai = parts[1]
            orig = parts[3]
            desc = parts[5]
            if "Hira" in desc:
                hira_map[orig] = thai
            elif "Kata" in desc:
                kata_map[orig] = thai

# Layout rows in tex_113
hira_grid = [
    # Row 1 (Cols 1-5 Left, Cols 6,7,8 Mid, Cols 9-13 Right)
    ['あ', 'い', 'う', 'え', 'お',    'や', 'ゆ', 'よ',    'が', 'ぎ', 'ぐ', 'げ', 'ご'],
    # Row 2
    ['か', 'き', 'く', 'け', 'こ',    'ら', 'り', 'る', 'れ', 'ろ',    'ざ', 'じ', 'ず', 'ぜ', 'ぞ'],
    # Row 3
    ['さ', 'し', 'す', 'せ', 'そ',    'わ', 'を', 'ん',    'だ', 'ぢ', 'づ', 'で', 'ど'],
    # Row 4
    ['た', 'ち', 'つ', 'て', 'と',    'ぁ', 'ぃ', 'ぅ', 'ぇ', 'ぉ',    'ば', 'び', 'ぶ', 'べ', 'ぼ'],
    # Row 5
    ['な', 'に', 'ぬ', 'ね', 'の',    'ゃ', 'ゅ', 'ょ', 'っ', 'ゎ',    'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ'],
    # Row 6
    ['は', 'ひ', 'ふ', 'へ', 'ほ',    '・', '。', '、', '！', '？',    'ー', '～', '＝', '♥', '★'],
    # Row 7
    ['ま', 'み', 'む', 'め', 'も']
]

kata_grid = [
    # Row 1
    ['ア', 'イ', 'ウ', 'エ', 'オ',    'ヤ', 'ユ', 'ヨ',    'ガ', 'ギ', 'グ', 'ゲ', 'ゴ'],
    # Row 2
    ['カ', 'キ', 'ク', 'ケ', 'コ',    'ラ', 'リ', 'ル', 'レ', 'ロ',    'ザ', 'ジ', 'ズ', 'ゼ', 'ゾ'],
    # Row 3
    ['サ', 'シ', 'ス', 'セ', 'ソ',    'ワ', 'ヲ', 'ン',    'ダ', 'ヂ', 'ヅ', 'デ', 'ド'],
    # Row 4
    ['タ', 'チ', 'ツ', 'テ', 'ト',    'ァ', 'ィ', 'ゥ', 'ェ', 'ォ',    'バ', 'ビ', 'ブ', 'ベ', 'ボ'],
    # Row 5
    ['ナ', 'ニ', 'ヌ', 'ネ', 'ノ',    'ャ', 'ュ', 'ョ', 'ッ', 'ヮ',    'パ', 'ピ', 'プ', 'ペ', 'ポ'],
    # Row 6
    ['ハ', 'ヒ', 'フ', 'ヘ', 'ホ',    '・', '。', '、', '！', '？',    'ー', '～', '＝', '♥', '★'],
    # Row 7
    ['マ', 'ミ', 'ム', 'メ', 'モ']
]

print("================================================================================")
print("=== ผังการแปลงปุ่มคีย์บอร์ด: หน้า 1 ฮิระงะนะ (HIRAGANA -> พยัญชนะไทย + ตัวเลข) ===")
print("================================================================================")
for r_idx, row in enumerate(hira_grid):
    jp_str = " | ".join(f"{ch:^2s}" for ch in row)
    th_str = " | ".join(f"{hira_map.get(ch, '?'):^2s}" for ch in row)
    print(f"\n[แถวที่ {r_idx+1}]")
    print(f"  รูปเดิมใน tex_113: | {jp_str} |")
    print(f"  ปุ่มไทยที่พิมพ์ออก: | {th_str} |")

print("\n================================================================================")
print("=== ผังการแปลงปุ่มคีย์บอร์ด: หน้า 2 คะตะกะนะ (KATAKANA -> สระ / วรรณยุกต์ / สัญลักษณ์) ===")
print("================================================================================")
for r_idx, row in enumerate(kata_grid):
    jp_str = " | ".join(f"{ch:^2s}" for ch in row)
    th_str = " | ".join(f"{kata_map.get(ch, '?'):^2s}" for ch in row)
    print(f"\n[แถวที่ {r_idx+1}]")
    print(f"  รูปเดิมใน tex_113: | {jp_str} |")
    print(f"  ปุ่มไทยที่พิมพ์ออก: | {th_str} |")
