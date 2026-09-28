"""
================================================================================
 Village in the Shade - Title Screen & Logo Thai Text Generator
 สคริปต์พิมพ์ข้อความและโลโก้ลงบน Texture ไตเติลอัตโนมัติ (Option 1)
 
 ปรับแต่งได้ทั้ง:
 1. ui_1000_title01.png -> โลโก้ชื่อเกม, ปุ่ม 'กดปุ่มใดก็ได้', เมนูเริ่มเกม/ตั้งค่า/ออก
 2. title_white.png     -> แผ่นมาสก์สีขาวสำหรับเอฟเฟกต์เรืองแสง/เฟดหน้าไตเติล
================================================================================
"""

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# -----------------------------------------------------------------------------
# กำหนดข้อความที่ต้องการเปลี่ยน (แก้ไขข้อความตรงนี้ได้เลย)
# -----------------------------------------------------------------------------
CONFIG = {
    "title_logo":   "Village in the Shade", # โลโก้ชื่อเกม (แทนที่ ほの暮しの庭)
    "press_button": "กดปุ่มใดก็ได้",          # แทนที่ 'Press any button'
    "start_game":   "เริ่มเกม",                # แทนที่ 'はじめる'
    "settings":     "ตั้งค่า",                 # แทนที่ '設定'
    "exit_game":    "ออกจากเกม",              # แทนที่ 'ゲームを終了する'
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "lora-thai-jp-bold.ttf"),
    r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ฟอนต์และตัวจัดการฟอนต์\lora-thai-jp-bold.ttf",
    r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ฟอนต์และตัวจัดการฟอนต์\lora-bold.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)

MAPPING_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "Mapping.json"),
    os.path.join(SCRIPT_DIR, "..", "scripts", "Mapping.json"),
    r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scripts\Mapping.json",
    r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json",
]
MAPPING_PATH = next((p for p in MAPPING_CANDIDATES if os.path.exists(p)), None)


def load_pua_mapping(mapping_file):
    if not mapping_file or not os.path.exists(mapping_file):
        return {}, 1
    with open(mapping_file, "r", encoding="utf-8-sig") as f:
        mapping = json.load(f)
    mapping = {str(k): str(v) for k, v in mapping.items() if k and v}
    max_len = max((len(k) for k in mapping.keys()), default=1)
    return mapping, max_len


def to_pua(text, mapping, max_len):
    if not mapping:
        return text
    result = []
    i = 0
    n = len(text)
    while i < n:
        matched = False
        for l in range(min(max_len, n - i), 0, -1):
            sub = text[i : i + l]
            if sub in mapping:
                result.append(mapping[sub])
                i += l
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)


def generate_title_assets():
    print("=" * 70)
    print(" กำลังสร้าง Texture หน้าไตเติล (Title Elements Generator)")
    print("=" * 70)
    print(f"[*] ฟอนต์ที่ใช้       : {FONT_PATH}")
    print(f"[*] ตาราง Mapping PUA : {MAPPING_PATH}")
    print(f"[*] ชื่อเกมที่ใช้      : {CONFIG['title_logo']}\n")

    mapping, max_len = load_pua_mapping(MAPPING_PATH)

    # -------------------------------------------------------------------------
    # 1. จัดการ ui_1000_title01.png
    # -------------------------------------------------------------------------
    title01_in = os.path.join(SCRIPT_DIR, "ui_1000_title01.png")
    if not os.path.exists(title01_in):
        title01_in = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_textures\title_elements\ui_1000_title01.png"

    base_img = Image.open(title01_in).convert("RGBA")
    draw_base = ImageDraw.Draw(base_img)

    # ลบพื้นที่เก่าออก
    draw_base.rectangle([ 90,   5,  930, 255], fill=(0, 0, 0, 0)) # โลโก้เดิม
    draw_base.rectangle([1010, 275, 1425, 365], fill=(0, 0, 0, 0)) # Press any button
    draw_base.rectangle([1840, 160, 1995, 215], fill=(0, 0, 0, 0)) # はじめる
    draw_base.rectangle([1610, 160, 1715, 215], fill=(0, 0, 0, 0)) # 設定
    draw_base.rectangle([ 950, 195, 1195, 255], fill=(0, 0, 0, 0)) # ゲームを終了する

    items_title01 = [
        {
            "name": "Title Logo",
            "text": CONFIG["title_logo"],
            "cx": 512,
            "cy": 140,
            "size": 82,
            "fill": (247, 241, 223, 255),
            "stroke_fill": (32, 30, 26, 230),
            "stroke_width": 2,
            "shadow": True,
            "shadow_alpha": 160,
            "shadow_radius": 6,
        },
        {
            "name": "Press Any Button",
            "text": CONFIG["press_button"],
            "cx": 1216,
            "cy": 320,
            "size": 50,
            "fill": (218, 213, 208, 255),
            "stroke_fill": (55, 52, 48, 190),
            "stroke_width": 1,
            "shadow": True,
            "shadow_alpha": 140,
            "shadow_radius": 4,
        },
        {
            "name": "Start Game",
            "text": CONFIG["start_game"],
            "cx": 1918,
            "cy": 188,
            "size": 28,
            "fill": (205, 199, 195, 255),
            "stroke_fill": None,
            "stroke_width": 0,
            "shadow": False,
        },
        {
            "name": "Settings",
            "text": CONFIG["settings"],
            "cx": 1663,
            "cy": 188,
            "size": 28,
            "fill": (205, 199, 195, 255),
            "stroke_fill": None,
            "stroke_width": 0,
            "shadow": False,
        },
        {
            "name": "Exit Game",
            "text": CONFIG["exit_game"],
            "cx": 1072,
            "cy": 225,
            "size": 30,
            "fill": (218, 213, 208, 255),
            "stroke_fill": (55, 52, 48, 190),
            "stroke_width": 1,
            "shadow": True,
            "shadow_alpha": 140,
            "shadow_radius": 3,
        },
    ]

    text_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    shadow_draw = ImageDraw.Draw(shadow_layer)

    for it in items_title01:
        pua_str = to_pua(it["text"], mapping, max_len)
        f = ImageFont.truetype(FONT_PATH, it["size"])
        sw = it["stroke_width"]
        bbox = text_draw.textbbox((0, 0), pua_str, font=f, stroke_width=sw)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = int(it["cx"] - tw / 2)
        ty = int(it["cy"] - th / 2) - 2

        if it.get("shadow"):
            s_alpha = it.get("shadow_alpha", 140)
            s_rad = it.get("shadow_radius", 4)
            shadow_draw.text(
                (tx, ty),
                pua_str,
                font=f,
                fill=(0, 0, 0, s_alpha),
                stroke_fill=(0, 0, 0, s_alpha),
                stroke_width=sw + s_rad * 2,
            )

        if it["stroke_fill"]:
            text_draw.text((tx, ty), pua_str, font=f, fill=it["fill"], stroke_fill=it["stroke_fill"], stroke_width=sw)
        else:
            text_draw.text((tx, ty), pua_str, font=f, fill=it["fill"])

        print(f"[+] เรนเดอร์ '{it['text']}' -> พิกัด ({tx}, {ty})")

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=4))
    final_title01 = Image.alpha_composite(base_img, shadow_layer)
    final_title01 = Image.alpha_composite(final_title01, text_layer)

    out_title01 = os.path.join(SCRIPT_DIR, "ui_1000_title01_thai.png")
    final_title01.save(out_title01)
    print(f"[SUCCESS] บันทึก: {out_title01}\n")

    # -------------------------------------------------------------------------
    # 2. จัดการ title_white.png
    # -------------------------------------------------------------------------
    white_in = os.path.join(SCRIPT_DIR, "title_white.png")
    if not os.path.exists(white_in):
        white_in = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_textures\title_elements\title_white.png"

    white_img = Image.open(white_in).convert("RGBA")
    white_draw = ImageDraw.Draw(white_img)

    # ลบพื้นที่โลโก้ขาวเดิมออก
    white_draw.rectangle([450, 380, 1550, 730], fill=(0, 0, 0, 0))

    logo_text = CONFIG["title_logo"]
    f_logo = ImageFont.truetype(FONT_PATH, 82)
    sw_logo = 2
    bbox_w = white_draw.textbbox((0, 0), logo_text, font=f_logo, stroke_width=sw_logo)
    tw_w = bbox_w[2] - bbox_w[0]
    th_w = bbox_w[3] - bbox_w[1]
    tx_w = int(998 - tw_w / 2)
    ty_w = int(564 - th_w / 2) - 2

    # วาดตัวหนังสือสีขาวทึบล้วนพร้อมขอบ
    white_draw.text(
        (tx_w, ty_w),
        logo_text,
        font=f_logo,
        fill=(255, 255, 255, 255),
        stroke_fill=(255, 255, 255, 255),
        stroke_width=sw_logo,
    )

    out_white = os.path.join(SCRIPT_DIR, "title_white_thai.png")
    white_img.save(out_white)
    print(f"[SUCCESS] บันทึก: {out_white}\n")

    print("=" * 70)
    print("[+] อัปเดตโลโก้และข้อความไตเติลครบทั้ง 2 ภาพเรียบร้อยแล้ว!")
    print("=" * 70)


if __name__ == "__main__":
    generate_title_assets()
