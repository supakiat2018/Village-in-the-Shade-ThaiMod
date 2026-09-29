#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 scripts/generate_ui_textures.py
 ระบบเรนเดอร์และสร้างภาพ UI ภาษาไทยอัตโนมัติ 28 ภาพ
 พร้อมแปลงเป็น BC7 DDS และแพ็กเข้าไฟล์ .nltx สำหรับ Village in the Shade (PC Steam)
================================================================================
"""

import os
import sys
import json
import struct
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DEV_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(DEV_DIR, "01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ")
OUT_PNG_DIR = os.path.join(DEV_DIR, "extracted_textures", "thai_generated")
OUT_NLTX_DIR = os.path.join(DEV_DIR, "extracted_textures", "thai_generated_nltx")
MOD_TEXTURES_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
FONT_PATH = os.path.join(DEV_DIR, "data", "lora-thai-jp-bold.ttf")
MAPPING_PATH = os.path.join(DEV_DIR, "scripts", "Mapping.json")
TEXCONV_PATH = os.path.join(DEV_DIR, "texconv.exe")

os.makedirs(OUT_PNG_DIR, exist_ok=True)
os.makedirs(OUT_NLTX_DIR, exist_ok=True)
os.makedirs(MOD_TEXTURES_DIR, exist_ok=True)

# Load PUA Mapping
with open(MAPPING_PATH, "r", encoding="utf-8-sig") as f:
    MAPPING = json.load(f)

MAX_LEN = max(len(k) for k in MAPPING.keys())

def to_pua(text):
    if not text:
        return text
    res, i, n = [], 0, len(text)
    while i < n:
        matched = False
        for l in range(min(MAX_LEN, n - i), 0, -1):
            sub = text[i:i+l]
            if sub in MAPPING:
                res.append(MAPPING[sub])
                i += l
                matched = True
                break
        if not matched:
            res.append(text[i])
            i += 1
    return "".join(res)

def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def render_text_with_shadow(draw_shadow, draw_text, font, text, cx, cy, 
                            color=(255, 255, 255, 255), 
                            shadow_color=(0, 0, 0, 220), 
                            stroke_width=1, stroke_color=(25, 25, 25, 255),
                            shadow_width=3, align="center"):
    pua = to_pua(text)
    bbox = font.getbbox(pua)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    if align == "center":
        tx = cx - tw // 2 - bbox[0]
    elif align == "left":
        tx = cx - bbox[0]
    elif align == "right":
        tx = cx - tw - bbox[0]
    else:
        tx = cx
    ty = cy - th // 2 - bbox[1]

    if draw_shadow:
        draw_shadow.text((tx, ty), pua, font=font, fill=shadow_color,
                         stroke_width=shadow_width, stroke_fill=shadow_color)
    if draw_text:
        draw_text.text((tx, ty), pua, font=font, fill=color,
                       stroke_width=stroke_width, stroke_fill=stroke_color)
    return (tx, ty, tw, th)

# ==============================================================================
# 1. ui_0060_Charaname24pxB.png (1024x512)
# ==============================================================================
def gen_ui_0060():
    filename = "ui_0060_Charaname24pxB.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    blank_btn = im.crop((558, 73, 722, 117))

    col0 = ['ริน', 'โทบาริ', 'โคมะโกะ', 'ซาซังกะ', 'โย', 'ฮาสุมิ', 'ชินานะ', 'โคดามะ']
    col1 = ['คิสุเกะ', 'ชิโรจิ', 'สุมิเระ', 'ยูตะ', 'ร็อกคาคุ', 'นาโงะ', 'คอนโนะ', '???']
    col2 = ['โอวาน']

    rows_y = [9, 73, 137, 201, 265, 329, 393, 457]
    cols_x = [46, 302, 558]
    font = get_font(22)

    for r_idx, name in enumerate(col0):
        x, y = cols_x[0], rows_y[r_idx]
        im.paste(blank_btn, (x, y))
        pua = to_pua(name)
        bbox = font.getbbox(pua)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (164 - tw) // 2 - bbox[0]
        ty = y + (44 - th) // 2 - bbox[1] - 1
        d = ImageDraw.Draw(im)
        d.text((tx, ty+1), pua, font=font, fill=(20, 20, 20, 220))
        d.text((tx, ty), pua, font=font, fill=(240, 240, 240, 255))

    for r_idx, name in enumerate(col1):
        x, y = cols_x[1], rows_y[r_idx]
        im.paste(blank_btn, (x, y))
        pua = to_pua(name)
        bbox = font.getbbox(pua)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (164 - tw) // 2 - bbox[0]
        ty = y + (44 - th) // 2 - bbox[1] - 1
        d = ImageDraw.Draw(im)
        d.text((tx, ty+1), pua, font=font, fill=(20, 20, 20, 220))
        d.text((tx, ty), pua, font=font, fill=(240, 240, 240, 255))

    for r_idx, name in enumerate(col2):
        x, y = cols_x[2], rows_y[r_idx]
        im.paste(blank_btn, (x, y))
        pua = to_pua(name)
        bbox = font.getbbox(pua)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (164 - tw) // 2 - bbox[0]
        ty = y + (44 - th) // 2 - bbox[1] - 1
        d = ImageDraw.Draw(im)
        d.text((tx, ty+1), pua, font=font, fill=(20, 20, 20, 220))
        d.text((tx, ty), pua, font=font, fill=(240, 240, 240, 255))

    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 2. ui_0070_buttonicon_text.png (512x256)
# ==============================================================================
def gen_ui_0070():
    filename = "ui_0070_buttonicon_text.png"
    im = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    items = [
        ("ยืนยัน", 64, 36),
        ("รายละเอียด", 192, 36),
        ("กดค้าง", 64, 96),
        ("เก็บกู้", 192, 96),
        ("สลับ", 64, 156),
        ("หมุน", 64, 216)
    ]
    font = get_font(22)
    shadow = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    for text, cx, cy in items:
        render_text_with_shadow(sdraw, tdraw, font, text, cx, cy,
                                color=(245, 245, 245, 255),
                                shadow_color=(0, 0, 0, 230),
                                stroke_width=1, stroke_color=(35, 35, 35, 255),
                                shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    res = Image.alpha_composite(shadow, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    res.save(out_p)
    return filename

# ==============================================================================
# 3. ui_0010_nameplate.png (512x512)
# ==============================================================================
def gen_ui_0010_nameplate():
    filename = "ui_0010_nameplate.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    boxes_to_clear = [
        (20, 10, 220, 50),   # 持ち物
        (280, 10, 480, 50),  # (大工さん)
        (20, 75, 220, 115),  # 出荷
        (280, 75, 480, 115), # (木こり)
        (20, 140, 220, 180), # 保管箱
        (20, 205, 220, 245), # (骨ネキ)
    ]
    draw_clear = ImageDraw.Draw(im)
    for b in boxes_to_clear:
        draw_clear.rectangle(b, fill=(0, 0, 0, 0))

    items = [
        ('สัมภาระ', 120, 30),
        ('(ช่างไม้)', 375, 30),
        ('จัดส่ง', 120, 95),
        ('(คนตัดไม้)', 375, 95),
        ('หีบเก็บของ', 120, 160),
        ('(เจ๊กระดูก)', 120, 225),
    ]
    font = get_font(22)
    shadow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    for text, cx, cy in items:
        render_text_with_shadow(sdraw, tdraw, font, text, cx, cy,
                                color=(255, 255, 255, 255),
                                shadow_color=(0, 0, 0, 240),
                                stroke_width=1, stroke_color=(20, 20, 20, 255),
                                shadow_width=4)

    shadow = shadow.filter(ImageFilter.GaussianBlur(2.0))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 4. ui_0120_汎用テキスト01.png (512x256)
# ==============================================================================
def gen_ui_0120():
    filename = "ui_0120_汎用テキスト01.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear text areas
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((0, 0, 256, 170), fill=(0, 0, 0, 0))

    font = get_font(24)
    shadow = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 256), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    items = [
        ("ได้รับ", 64, 45),
        ("ปลดล็อค", 192, 45),
        ("สำเร็จ", 64, 120),
    ]

    for text, cx, cy in items:
        render_text_with_shadow(sdraw, tdraw, font, text, cx, cy,
                                color=(255, 255, 255, 255),
                                shadow_color=(0, 0, 0, 240),
                                stroke_width=1, stroke_color=(20, 20, 20, 255),
                                shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 5. ui_1070_メッセージポップアップtext0.png (512x128)
# ==============================================================================
def gen_ui_1070():
    filename = "ui_1070_メッセージポップアップtext0.png"
    im = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    font = get_font(26)
    shadow = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "อืมๆๆๆๆ", 128, 32,
                            color=(245, 245, 245, 255), shadow_color=(0, 0, 0, 200),
                            stroke_width=1, shadow_width=3)
    render_text_with_shadow(sdraw, tdraw, font, "ไม่เอาๆๆๆๆ", 384, 32,
                            color=(245, 245, 245, 255), shadow_color=(0, 0, 0, 200),
                            stroke_width=1, shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    res = Image.alpha_composite(shadow, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    res.save(out_p)
    return filename

# ==============================================================================
# 6. ui_1153_ウィンドウ.png (1024x1024)
# ==============================================================================
def gen_ui_1153():
    filename = "ui_1153_ウィンドウ.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    arr = np.array(im)

    # 1. Fill [572:608, 864:928] inside orange button with matching texture noise
    h_box = 608 - 572
    w_box = 928 - 864
    np.random.seed(42)
    noise_r = np.random.normal(170, 5.5, (h_box, w_box)).clip(0, 255)
    noise_g = np.random.normal(93, 3.1, (h_box, w_box)).clip(0, 255)
    noise_b = np.random.normal(53, 7.4, (h_box, w_box)).clip(0, 255)
    noise_a = np.full((h_box, w_box), 255)
    noise_patch = np.stack([noise_r, noise_g, noise_b, noise_a], axis=-1).astype(np.uint8)
    arr[572:608, 864:928] = noise_patch
    im = Image.fromarray(arr)

    # 2. Clear old '売値' / 'Sell Price' at (775, 785, 885, 825)
    draw = ImageDraw.Draw(im)
    draw.rectangle((775, 785, 885, 825), fill=(0, 0, 0, 0))

    # 3. Draw 'ราคาขาย' at (782, 792)
    font_sell = get_font(18)
    pua_sell = to_pua("ราคาขาย")
    draw.text((782, 792), pua_sell, font=font_sell, fill=(35, 35, 35, 255))

    # 4. Draw 'สร้างได้' on the orange button
    font_craft = get_font(15)
    pua_craft = to_pua("สร้างได้")
    bbox_craft = font_craft.getbbox(pua_craft)
    cw = bbox_craft[2] - bbox_craft[0]
    cx = 896 - cw // 2 - bbox_craft[0]
    cy = 581

    draw.text((cx + 1, cy + 1), pua_craft, font=font_craft, fill=(80, 40, 15, 240))
    draw.text((cx, cy), pua_craft, font=font_craft, fill=(255, 255, 255, 255))

    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 7. ui_1170_投げ銭_text.png (256x128)
# ==============================================================================
def gen_ui_1170():
    filename = "ui_1170_投げ銭_text.png"
    im = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    font = get_font(22)
    shadow = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (256, 128), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    # 拾(10) 百(100) 千(1000) 萬(10000)
    # 十萬(100000)
    items = [
        ("10", 30, 30),
        ("100", 90, 30),
        ("1,000", 155, 30),
        ("10,000", 225, 30),
        ("100,000", 55, 90),
    ]

    for text, cx, cy in items:
        render_text_with_shadow(sdraw, tdraw, font, text, cx, cy,
                                color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 200),
                                stroke_width=1, shadow_width=2)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.0))
    res = Image.alpha_composite(shadow, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    res.save(out_p)
    return filename

# ==============================================================================
# 8. ui_2030_詳細ポップアップ.png (512x512)
# ==============================================================================
def gen_ui_2030():
    filename = "ui_2030_詳細ポップアップ.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear text areas
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((0, 100, 250, 400), fill=(0, 0, 0, 0))
    draw_clear.rectangle((440, 50, 510, 110), fill=(0, 0, 0, 0))

    font_l = get_font(20)
    font_s = get_font(18)
    shadow = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    # Right side units
    render_text_with_shadow(sdraw, tdraw, font_s, "ชม.", 475, 75, align="center")
    render_text_with_shadow(sdraw, tdraw, font_s, "วัน", 475, 100, align="center")

    # Left side status descriptions
    items = [
        ("จนกว่าจะเก็บเกี่ยว", 15, 150),
        ("เหลือเวลาเก็บเกี่ยวอีก", 15, 180),
        ("ออกผลแล้ว", 15, 210),
        ("จนกว่าจะเสร็จ", 15, 245),
        ("เหลือเวลาเสร็จอีก", 15, 275),
        ("จนกว่าจะโต", 15, 335),
        ("เหลือเวลาโตอีก", 15, 365),
    ]

    for text, x, y in items:
        render_text_with_shadow(sdraw, tdraw, font_l, text, x, y, align="left",
                                color=(250, 250, 250, 255), shadow_color=(0, 0, 0, 220),
                                stroke_width=1, shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 9. ui_2100_00.png (256x256)
# ==============================================================================
def gen_ui_2100():
    filename = "ui_2100_00.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear text lines below bars
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((0, 120, 256, 256), fill=(0, 0, 0, 0))

    font = get_font(18)
    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "ปลดล็อคสกิลเงื่อนไขแล้ว", 128, 155,
                            color=(245, 245, 245, 255), shadow_color=(0, 0, 0, 220),
                            stroke_width=1, shadow_width=2)
    render_text_with_shadow(sdraw, tdraw, font, "ยังไม่ปลดล็อคสกิลเงื่อนไข", 128, 215,
                            color=(200, 200, 200, 255), shadow_color=(0, 0, 0, 220),
                            stroke_width=1, shadow_width=2)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.2))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 10. ui_2210_日リザルト02.png (1024x256)
# ==============================================================================
def gen_ui_2210():
    filename = "ui_2210_日リザルト02.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear ★ セーブが完了しました at X=10..300, Y=80..130
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((0, 60, 400, 150), fill=(0, 0, 0, 0))

    font = get_font(24)
    shadow = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (1024, 256), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "★ บันทึกข้อมูลเสร็จสิ้น", 30, 105, align="left",
                            color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 230),
                            stroke_width=1, shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 11. ui_2220_post03.png (512x1024)
# ==============================================================================
def gen_ui_2220_post03():
    filename = "ui_2220_post03.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear 手紙がありません at X=80..420, Y=500..600
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((50, 500, 460, 600), fill=(0, 0, 0, 0))

    font = get_font(26)
    shadow = Image.new("RGBA", (512, 1024), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 1024), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "ไม่มีจดหมาย", 256, 550, align="center",
                            color=(240, 240, 240, 255), shadow_color=(0, 0, 0, 230),
                            stroke_width=1, shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.8))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 12. ui_3030_家具配置01.png (2048x512)
# ==============================================================================
def gen_ui_3030():
    filename = "ui_3030_家具配置01.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear 家具配置 at bottom-left: X=0..120, Y=450..512
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((0, 450, 150, 512), fill=(0, 0, 0, 0))

    font = get_font(18)
    shadow = Image.new("RGBA", (2048, 512), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (2048, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "จัดวางเฟอร์นิเจอร์", 10, 480, align="left",
                            color=(230, 230, 230, 255), shadow_color=(0, 0, 0, 220),
                            stroke_width=1, shadow_width=2)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.2))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 13. ui_5010_項目02.png (256x1024)
# ==============================================================================
def gen_ui_5010_item02():
    filename = "ui_5010_項目02.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # 1. 完売 at Y ~ 100..150
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((50, 90, 206, 160), fill=(0, 0, 0, 0))

    # Clear text inside pill buttons:
    # 春 (pink): [20, 490, 105, 545]
    # 残 日 (brown): [145, 490, 235, 545]
    # 夏 (green): [20, 605, 105, 660]
    # 週替 (brown): [145, 605, 235, 660]
    # 秋 (red): [20, 720, 105, 775]
    # 残 個 (yellow): [145, 720, 235, 775]
    # 冬 (blue): [20, 835, 105, 890]

    # For buttons, we redraw the text centered in each pill
    font_btn = get_font(18)
    font_main = get_font(28)

    shadow = Image.new("RGBA", (256, 1024), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (256, 1024), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font_main, "ขายหมด", 128, 125, align="center",
                            color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 240),
                            stroke_width=1, shadow_width=3)

    pills = [
        ((20, 490, 105, 545), (195, 75, 85), "ใบไม้ผลิ"),
        ((145, 490, 235, 545), (190, 85, 45), "เหลือ...วัน"),
        ((20, 605, 105, 660), (75, 135, 65), "ฤดูร้อน"),
        ((145, 605, 235, 660), (190, 85, 45), "สลับสัปดาห์"),
        ((20, 720, 105, 775), (175, 65, 50), "ใบไม้ร่วง"),
        ((145, 720, 235, 775), (200, 130, 25), "เหลือ...ชิ้น"),
        ((20, 835, 105, 890), (55, 115, 155), "ฤดูหนาว"),
    ]

    for box, bg_col, text in pills:
        draw_clear.rectangle(box, fill=bg_col + (255,))
        cx = (box[0] + box[2]) // 2
        cy = (box[1] + box[3]) // 2
        render_text_with_shadow(sdraw, tdraw, font_btn, text, cx, cy, align="center",
                                color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 180),
                                stroke_width=1, shadow_width=2)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.2))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 14. ui_5100_bandolPU01.png (256x256)
# ==============================================================================
def gen_ui_5100():
    filename = "ui_5100_bandolPU01.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear 春のバインダー at X=30..200, Y=80..130
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((20, 80, 220, 130), fill=(0, 0, 0, 0))

    font = get_font(18)
    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "แฟ้มสะสมฤดูใบไม้ผลิ", 115, 105, align="center",
                            color=(245, 245, 245, 255), shadow_color=(0, 0, 0, 220),
                            stroke_width=1, shadow_width=2)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.2))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 15. ui_0020_カレンダー.png (1024x1024)
# ==============================================================================
def gen_ui_0020_calendar():
    filename = "ui_0020_カレンダー.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear calendar text on right side: X=700..1024, Y=150..600
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((740, 150, 1000, 580), fill=(0, 0, 0, 0))

    font_season = get_font(26)
    font_day = get_font(22)
    font_year = get_font(20)

    shadow = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    # Seasons:
    render_text_with_shadow(sdraw, tdraw, font_season, "ใบไม้ผลิ", 800, 210, align="center")
    render_text_with_shadow(sdraw, tdraw, font_season, "ฤดูร้อน", 880, 210, align="center")
    render_text_with_shadow(sdraw, tdraw, font_season, "ใบไม้ร่วง", 800, 270, align="center")
    render_text_with_shadow(sdraw, tdraw, font_season, "ฤดูหนาว", 880, 270, align="center")

    # Days of week: จ. อ. พ. พฤ. ศ. ส. อา.
    days = [
        ("จ.", 760, 370, (200, 200, 200, 255)),
        ("อ.", 810, 370, (200, 200, 200, 255)),
        ("พ.", 860, 370, (200, 200, 200, 255)),
        ("พฤ.", 910, 370, (200, 200, 200, 255)),
        ("ศ.", 780, 420, (200, 200, 200, 255)),
        ("ส.", 840, 420, (65, 140, 220, 255)),   # Saturday blue
        ("อา.", 900, 420, (220, 65, 65, 255)),   # Sunday red
    ]

    for d_text, dx, dy, d_col in days:
        render_text_with_shadow(sdraw, tdraw, font_day, d_text, dx, dy, align="center",
                                color=d_col, stroke_color=(20, 20, 20, 255))

    # Year
    render_text_with_shadow(sdraw, tdraw, font_year, "• ปี •", 840, 480, align="center")

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 16. ui_0010_itemcategory.png (512x1024)
# ==============================================================================
def gen_ui_0010_itemcategory():
    filename = "ui_0010_itemcategory.png"
    im = Image.new("RGBA", (512, 1024), (0, 0, 0, 0))

    col1 = [
        "เมล็ดพันธุ์", "อุปกรณ์เกษตร", "ของใช้สัตว์", "อุปกรณ์ล่า", "ยา", "อาหาร",
        "พืชผล", "ดอกไม้", "ผลไม้", "ผลผลิตปศุสัตว์", "ของป่า", "สัตว์ที่ล่าได้",
        "ปลา", "ผลผลิตแปรรูป", "วัตถุดิบ", "แร่ธาตุ"
    ]
    col2 = [
        "เครื่องปรุง", "น้ำหล่อเลี้ยง", "เครื่องจักร", "ที่เก็บของ", "โคมไฟ", "โต๊ะ",
        "เก้าอี้", "ของชิ้นเล็ก", "เครื่องนอน", "ของแขวนผนัง", "พรมปูพื้น", "ไม้ประดับสวน",
        "เสื้อผ้า", "ผ้าพันคอ", "เครื่องประดับ", "กระเป๋า"
    ]
    col3 = [
        "เศษซากวัสดุ", "เฟอร์นิเจอร์กลางคืน", "หนังสือ", "ภาชนะ", "ของต้องสาป", "ของมีค่า",
        "ช่างไม้", "นายพราน", "ร้านของชำ", "พ่อค้าเร่", "พ่อครัว", "นักบำบัด",
        "ผู้ใหญ่บ้าน", "วอลเปเปอร์", "สูตรผสม", "สิ่งปลูกสร้าง"
    ]

    font = get_font(19)
    shadow = Image.new("RGBA", (512, 1024), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (512, 1024), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    col_x = [90, 270, 440]
    row_start_y = 35
    row_step_y = 62

    for r_idx in range(16):
        cy = row_start_y + r_idx * row_step_y
        render_text_with_shadow(sdraw, tdraw, font, col1[r_idx], col_x[0], cy, align="center")
        render_text_with_shadow(sdraw, tdraw, font, col2[r_idx], col_x[1], cy, align="center")
        render_text_with_shadow(sdraw, tdraw, font, col3[r_idx], col_x[2], cy, align="center")

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.4))
    res = Image.alpha_composite(shadow, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    res.save(out_p)
    return filename

# ==============================================================================
# 17. ui_0010_itemcategory03.png (256x512)
# ==============================================================================
def gen_ui_0010_itemcategory03():
    filename = "ui_0010_itemcategory03.png"
    im = Image.new("RGBA", (256, 512), (0, 0, 0, 0))
    items = [
        "พืชผลต้องสาป",
        "ปลาต้องสาป",
        "สินค้าที่ซื้อ",
        "ใบรับรองการล่า",
        "ปศุสัตว์",
        "ชั้นวาง",
        "ของสำคัญ"
    ]
    font = get_font(20)
    shadow = Image.new("RGBA", (256, 512), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (256, 512), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    row_start_y = 40
    row_step_y = 64
    for r_idx, text in enumerate(items):
        cy = row_start_y + r_idx * row_step_y
        render_text_with_shadow(sdraw, tdraw, font, text, 128, cy, align="center")

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.4))
    res = Image.alpha_composite(shadow, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    res.save(out_p)
    return filename

# ==============================================================================
# 18. ui_0010_itemcategory2.png (1024x256)
# ==============================================================================
def gen_ui_0010_itemcategory2():
    filename = "ui_0010_itemcategory2.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    # For horizontal spritesheet, copy base
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 19. ui_0030_汎用アイコン_はんこ.png (1024x512)
# ==============================================================================
def gen_ui_0030():
    filename = "ui_0030_汎用アイコン_はんこ.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear red stamp text
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((20, 20, 105, 180), fill=(100, 15, 15, 255))
    draw_clear.rectangle((140, 20, 225, 180), fill=(100, 15, 15, 255))
    draw_clear.rectangle((260, 20, 345, 180), fill=(100, 15, 15, 255))
    draw_clear.rectangle((380, 20, 560, 95), fill=(100, 15, 15, 255))
    draw_clear.rectangle((380, 130, 560, 205), fill=(100, 15, 15, 255))

    font_v = get_font(20)
    font_h = get_font(24)
    text_layer = Image.new("RGBA", (1024, 512), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(text_layer)

    # Vertical stamps: ทั่งตีเหล็ก, โต๊ะย้อมสี, ก่อสร้าง
    # Horizontal stamps: งานช่าง, ทำอาหาร
    render_text_with_shadow(None, tdraw, font_v, "ตีเหล็ก", 62, 90, color=(180, 30, 30, 255), stroke_width=0)
    render_text_with_shadow(None, tdraw, font_v, "ย้อมสี", 182, 90, color=(180, 30, 30, 255), stroke_width=0)
    render_text_with_shadow(None, tdraw, font_v, "ก่อสร้าง", 302, 90, color=(180, 30, 30, 255), stroke_width=0)
    render_text_with_shadow(None, tdraw, font_h, "งานช่าง", 470, 55, color=(180, 30, 30, 255), stroke_width=0)
    render_text_with_shadow(None, tdraw, font_h, "ทำอาหาร", 470, 165, color=(180, 30, 30, 255), stroke_width=0)

    im = Image.alpha_composite(im, text_layer)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 20. ui_9000_01.png (1024x2048) - สัญญาเช่าที่ดิน
# ==============================================================================
def gen_ui_9000_01():
    filename = "ui_9000_01.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear 賃貸借契約書 at X=240..560, Y=450..550
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((220, 440, 600, 560), fill=(215, 210, 195, 255))

    font = get_font(32)
    shadow = Image.new("RGBA", (1024, 2048), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (1024, 2048), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "สัญญาเช่าที่ดินและสิ่งปลูกสร้าง", 410, 500, align="center",
                            color=(45, 40, 35, 255), shadow_color=(0, 0, 0, 100),
                            stroke_width=0, shadow_width=1)

    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 21. ui_9000_02.png (1024x2048)
# ==============================================================================
def gen_ui_9000_02():
    filename = "ui_9000_02.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 22. 名前_steam版_04.png (1024x2048)
# ==============================================================================
def gen_name_steam_04():
    filename = "名前_steam版_04.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")

    # Clear ローカライズ at top
    draw_clear = ImageDraw.Draw(im)
    draw_clear.rectangle((340, 35, 680, 105), fill=(0, 0, 0, 0))

    font = get_font(32)
    shadow = Image.new("RGBA", (1024, 2048), (0, 0, 0, 0))
    text_layer = Image.new("RGBA", (1024, 2048), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    tdraw = ImageDraw.Draw(text_layer)

    render_text_with_shadow(sdraw, tdraw, font, "การแปลภาษา", 512, 70, align="center",
                            color=(255, 255, 255, 255), shadow_color=(0, 0, 0, 220),
                            stroke_width=1, shadow_width=3)

    shadow = shadow.filter(ImageFilter.GaussianBlur(1.5))
    combined = Image.alpha_composite(shadow, text_layer)
    im = Image.alpha_composite(im, combined)
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 23. ui_0990_localize_00.png (1024x512)
# ==============================================================================
def gen_ui_0990():
    filename = "ui_0990_localize_00.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 24. ui_1000_02.png (2048x256)
# ==============================================================================
def gen_ui_1000_02():
    filename = "ui_1000_02.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 25. bg_8080_00_tex.png (512x256)
# ==============================================================================
def gen_bg_8080_00():
    filename = "bg_8080_00_tex.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 26. bg_8080_01_tex.png (2048x256)
# ==============================================================================
def gen_bg_8080_01():
    filename = "bg_8080_01_tex.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 27. bg_8080_04_tex.png (1024x2048)
# ==============================================================================
def gen_bg_8080_04():
    filename = "bg_8080_04_tex.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# 28. ene_3020_1_02.png (512x256)
# ==============================================================================
def gen_ene_3020():
    filename = "ene_3020_1_02.png"
    src_path = os.path.join(SRC_DIR, filename)
    im = Image.open(src_path).convert("RGBA")
    out_p = os.path.join(OUT_PNG_DIR, filename)
    im.save(out_p)
    return filename

# ==============================================================================
# NLTX Packing & Deployment Engine
# ==============================================================================
def pack_and_deploy_nltx(png_filename):
    import lz4.block
    png_path = os.path.join(OUT_PNG_DIR, png_filename)
    base_no_ext = os.path.splitext(png_filename)[0]
    dds_path = os.path.join(OUT_PNG_DIR, f"{base_no_ext}.dds")
    out_nltx_path = os.path.join(OUT_NLTX_DIR, f"{base_no_ext}.nltx")
    game_nltx_path = os.path.join(MOD_TEXTURES_DIR, f"{base_no_ext}.nltx")

    im = Image.open(png_path)
    width, height = im.size

    # Convert to BC7 DDS
    cmd = [
        TEXCONV_PATH,
        "-f", "BC7_UNORM",
        "-m", "1",
        "-nologo",
        "-y",
        "-o", OUT_PNG_DIR,
        png_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] texconv error on {png_filename}:\n{res.stderr}")
        return False

    with open(dds_path, "rb") as f:
        f.seek(148)
        raw_bc7 = f.read()

    expected_size = width * height
    if len(raw_bc7) != expected_size:
        print(f"[!] Warning on {png_filename}: raw_bc7 ({len(raw_bc7)}) != expected ({expected_size})")

    # LZ4 compress
    comp_data = lz4.block.compress(raw_bc7, mode='high_compression', store_size=False)
    comp_sz = len(comp_data) + 20
    uncomp_sz = len(raw_bc7)

    ykcmp_hdr = struct.pack('<8sIII', b'YKCMP_V1', 9, comp_sz, uncomp_sz)
    payload = ykcmp_hdr + comp_data

    # 128-byte NMPLTEX1 header
    hdr = bytearray(128)
    hdr[0:8] = b'NMPLTEX1'
    struct.pack_into('<I', hdr, 0x10, 0x66)
    struct.pack_into('<I', hdr, 0x14, 0x00800006)
    struct.pack_into('<II', hdr, 0x18, width, height)
    hdr[0x20:0x28] = bytes.fromhex('04 00 FF FF 00 01 01 00')
    struct.pack_into('<I', hdr, 0x2C, uncomp_sz)
    struct.pack_into('<II', hdr, 0x30, len(payload), 128)

    nltx_data = bytes(hdr) + payload

    with open(out_nltx_path, "wb") as f:
        f.write(nltx_data)
    with open(game_nltx_path, "wb") as f:
        f.write(nltx_data)

    print(f"  [OK] Packed & Installed: {base_no_ext}.nltx ({len(nltx_data):,} B)")
    return True

def main():
    print("=" * 70)
    print(" Generating & Packing All 28 UI Textures into Thai Mod")
    print("=" * 70)

    generators = [
        gen_ui_0060,
        gen_ui_0070,
        gen_ui_0010_nameplate,
        gen_ui_0120,
        gen_ui_1070,
        gen_ui_1153,
        gen_ui_1170,
        gen_ui_2030,
        gen_ui_2100,
        gen_ui_2210,
        gen_ui_2220_post03,
        gen_ui_3030,
        gen_ui_5010_item02,
        gen_ui_5100,
        gen_ui_0020_calendar,
        gen_ui_0010_itemcategory,
        gen_ui_0010_itemcategory03,
        gen_ui_0010_itemcategory2,
        gen_ui_0030,
        gen_ui_9000_01,
        gen_ui_9000_02,
        gen_name_steam_04,
        gen_ui_0990,
        gen_ui_1000_02,
        gen_bg_8080_00,
        gen_bg_8080_01,
        gen_bg_8080_04,
        gen_ene_3020,
    ]

    success_count = 0
    for gen in generators:
        png_name = gen()
        if pack_and_deploy_nltx(png_name):
            success_count += 1

    print("=" * 70)
    print(f" COMPLETED: {success_count}/{len(generators)} textures successfully processed and deployed!")
    print("=" * 70)

if __name__ == "__main__":
    main()
