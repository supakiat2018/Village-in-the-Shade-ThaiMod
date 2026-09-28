import json
import os

mapping_path = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"
with open(mapping_path, "r", encoding="utf-8-sig") as f:
    mapping = json.load(f)

max_len = max(len(k) for k in mapping.keys())

def to_pua(text):
    if not text:
        return text
    result = []
    i = 0
    n = len(text)
    while i < n:
        matched = False
        for length in range(min(max_len, n - i), 0, -1):
            substr = text[i : i + length]
            if substr in mapping:
                result.append(mapping[substr])
                i += length
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)

# Translations dictionary: Japanese -> Thai
translations = {
    # System / Options
    "表示言語": "ภาษาที่แสดง",
    "主人公の向きにカメラを寄せる": "หมุนกล้องตามทิศทางตัวละคร",
    "振動": "การสั่น",
    "メッセージ設定": "ตั้งค่าข้อความ",
    "音楽の音量": "ระดับเสียงดนตรี",
    "効果音の音量": "ระดับเสียงเอฟเฟกต์",
    "設定画面へ": "ไปยังหน้าตั้งค่า",
    "キーコンフィグ": "ตั้งค่าคีย์บอร์ด",
    "パッドボタン設定": "ตั้งค่าคอนโทรลเลอร์",
    "ガイド表示": "แสดงคำแนะนำ",
    "マウス操作": "การควบคุมด้วยเมาส์",
    "ウィンドウタイプ": "รูปแบบหน้าต่าง",
    "ウィンドウ": "หน้าต่าง",
    "優先モニター": "จอภาพหลัก",
    "フルスクリーン解像度": "ความละเอียดเต็มจอ",
    "ウィンドウ時アスペクト比率固定": "ล็อกอัตราส่วนภาพหน้าต่าง",
    "垂直同期": "การซิงค์แนวตั้ง (V-Sync)",
    "フレームレート制限": "จำกัดเฟรมเรต",
    "バックグラウンドフレームレート制限": "จำกัดเฟรมเรตเบื้องหลัง",
    "ウィンドウモードサイズ": "ขนาดโหมดหน้าต่าง",
    "非アクティブ時ミュート": "ปิดเสียงเมื่ออยู่เบื้องหลัง",
    "IME使用": "เปิดใช้งาน IME",

    # Common states
    "通常": "ปกติ",
    "あり": "เปิด",
    "なし": "ปิด",
    "自動": "อัตโนมัติ",
    "日本語": "ภาษาไทย",

    # Auto-save notification
    "このゲームは1日の終了時にオートセーブされ、": "เกมนี้จะบันทึกอัตโนมัติเมื่อสิ้นสุดวัน และ",
    "最新のデータが上書きされます。": "จะเขียนทับข้อมูลล่าสุดเสมอ",
    "上のアイコンが表示されている間は、": "ในขณะที่ไอคอนด้านบนกำลังแสดงผล",
    "ゲームを終了したり、電源を切らないでください。": "กรุณาอย่าปิดเกมหรือปิดเครื่องเด็ดขาด",

    # Save screen
    "どのセーブデータで遊ぶ？": "เลือกข้อมูลเซฟที่จะเล่น",
    "1年目 春 1日": "ปีที่ 1 ฤดูใบไม้ผลิ วันที่ 1",
    "セーブデータ削除": "ลบข้อมูลเซฟ",
    "以前のセーブデータ": "ข้อมูลเซฟก่อนหน้า",

    # Common UI
    "決定": "ตกลง",
    "キャンセル": "ยกเลิก",
    "戻る": "ย้อนกลับ",
    "はい": "ใช่",
    "いいえ": "ไม่ใช่",
    "セーブ": "บันทึก",
    "ロード": "โหลด",
    "閉じる": "ปิด",
    "適用": "นำไปใช้",
    "デフォルトに戻す": "คืนค่าเริ่มต้น",
    "ゲーム終了": "ออกจากเกม",
    "タイトルへ": "กลับสู่หน้าจอหลัก",
    "はじめから": "เริ่มเกมใหม่",
    "つづきから": "เล่นต่อ"
}

out_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt"

lines = [
    "# ==================================================================",
    "# Village in the Shade - Thai Translation (PUA Encoded)",
    "# =================================================================="
]

for orig, thai in translations.items():
    pua = to_pua(thai)
    lines.append(f"{orig}={pua}")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Successfully written {len(translations)} PUA translations to {out_path}")
