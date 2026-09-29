"""
Build Thai Minimap Texture
Game: Village in the Shade (ほの暮しの庭)
Applies 32 accurate Thai translations to the 4096x4096x32 minimap texture.
"""

import os
import shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def main():
    base_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    src_file = os.path.join(base_dir, "04ภาพen", "minimap_01_aut_en.png")
    bak_file = os.path.join(base_dir, "04ภาพen", "minimap_01_aut_en.png.bak")
    out_en_file = src_file
    out_th_file1 = os.path.join(base_dir, "04ภาพen", "minimap_01_aut_th.png")
    out_th_file2 = os.path.join(base_dir, "extracted_minimap_en", "minimap_01_aut_th.png")
    font_path = os.path.join(base_dir, "data", "lora-thai-jp-bold.ttf")

    if not os.path.exists(bak_file):
        print(f"[*] Creating backup of original: {bak_file}")
        shutil.copy2(src_file, bak_file)

    print(f"[*] Loading pristine image from: {bak_file}")
    img = Image.open(bak_file).convert("RGBA")
    w, h = img.size
    print(f"    Dimensions: {w}x{h}, Mode: {img.mode}")

    alpha_arr = np.array(img.getchannel("A"))
    rgb_img = img.convert("RGB")
    arr = np.array(rgb_img)

    # 18 Parchment labels (inpaint English text, then draw Thai text with halo)
    PARCHMENT_LABELS = [
        ('Altar', 'แท่นบูชา', 2390, 1975, 55, 22, 26),
        ('Cemetery', 'สุสาน', 1160, 1540, 80, 22, 27),
        ('Clock Tower', 'หอนาฬิกา', 2570, 2165, 90, 22, 26),
        ('Crossroads bulletin board', 'ป้ายประกาศทางแยก', 2160, 2515, 150, 28, 25),
        ('Crossroads fishing spot', 'จุดตกปลาทางแยก', 2440, 2535, 140, 28, 25),
        ('Hot Spring', 'บ่อน้ำพุร้อน', 1570, 1390, 90, 22, 26),
        ('Mountain foot fishing spot', 'จุดตกปลาเชิงเขา', 2140, 1490, 140, 28, 25),
        ('Mountain peak', 'ยอดเขา', 1578, 648, 80, 22, 27),
        ('Mountain pond fishing spot', 'จุดตกปลาบึงบนเขา', 1538, 868, 150, 22, 25),
        ('Muko Crossing', 'ทางข้ามมุโกะ', 2095, 2439, 120, 25, 26),
        ('Nodobotoke Mountain Trail', 'ทางเดินเขาโนโดโบโตเกะ', 1840, 1910, 160, 22, 24),
        ('Okami Pond', 'บึงโอกามิ', 3040, 1775, 90, 22, 26),
        ('Plaza', 'ลานกว้าง', 2485, 2125, 65, 22, 26),
        ('Quarry fishing spot', 'จุดตกปลาเหมืองหิน', 1551, 2169, 140, 25, 25),
        ('Village bulletin board', 'ป้ายประกาศหมู่บ้าน', 2635, 2012, 140, 22, 25),
        ('Village creek fishing spot', 'จุดตกปลาลำธารหมู่บ้าน', 2740, 2455, 150, 28, 24),
        ('Waterfall fishing spot', 'จุดตกปลา', 3200, 1835, 100, 22, 26),
        ('Watermill', 'กังหันน้ำ', 2330, 1800, 70, 22, 26),
    ]

    print("[*] Processing 18 parchment labels...")
    for idx, (name, th_text, cx, cy, hw, hh, fsize) in enumerate(PARCHMENT_LABELS):
        x1, y1 = max(0, cx - hw), max(0, cy - hh)
        x2, y2 = min(w, cx + hw), min(h, cy + hh)
        patch = arr[y1:y2, x1:x2].copy()
        gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)

        halo = (gray > 185).astype(np.uint8)
        dark = (gray < 85).astype(np.uint8)
        kernel = np.ones((5, 5), np.uint8)
        halo_dil = cv2.dilate(halo, kernel, iterations=1)
        text_mask = ((dark & halo_dil) | (halo & cv2.dilate(dark, kernel, iterations=1))).astype(np.uint8) * 255
        text_mask = cv2.dilate(text_mask, np.ones((3, 3), np.uint8), iterations=1)

        inpainted = cv2.inpaint(patch, text_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        res = Image.fromarray(inpainted)
        draw = ImageDraw.Draw(res)
        font = ImageFont.truetype(font_path, fsize)
        bbox = font.getbbox(th_text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (res.width - tw) // 2
        ty = (res.height - th) // 2 - bbox[1]

        draw.text((tx, ty), th_text, font=font, fill=(35, 30, 25), stroke_width=2, stroke_fill=(250, 246, 237))
        arr[y1:y2, x1:x2] = np.array(res)
        print(f"    [{idx+1}/18] Parchment: {name} -> {th_text}")

    # Reassemble RGBA image
    result_rgba = Image.fromarray(np.dstack([arr, alpha_arr]), mode="RGBA")
    draw_box = ImageDraw.Draw(result_rgba)
    box_color = (46, 40, 36, 255)

    # 14 Box labels (draw clean rounded dark boxes + white Thai text)
    BOX_LABELS = [
        ('Chasm', 'หุบเหว', 1210, 2835, 150, 56, 27),
        ('Chawantei', 'ร้านชาชาวันเต', 2340, 2200, 210, 56, 27),
        ('Forest', 'ป่า', 2310, 885, 150, 56, 28),
        ('Hunting Lodge', 'กระท่อมนายพราน', 1925, 1695, 240, 56, 26),
        ('Kiki Construction', 'ร้านช่างกิกิ', 2200, 1950, 240, 56, 26),
        ('Kiki Manor', 'คฤหาสน์กิกิ', 2460, 1480, 220, 56, 27),
        ('Kusunoki Clinic', 'คลินิกคุสุโนะกิ', 2665, 2100, 240, 56, 26),
        ('Library', 'ห้องสมุด', 2490, 1925, 160, 56, 27),
        ('Mountain pass', 'ช่องเขา', 2811, 3197, 180, 56, 27),
        ('My House', 'บ้านของฉัน', 1860, 2340, 190, 56, 27),
        ('Quarry', 'เหมืองหิน', 1340, 2042, 160, 56, 27),
        ('Street Vendor', 'ร้านแผงลอย', 2560, 2360, 200, 56, 27),
        ('Tagami General Store', 'ร้านค้าทากามิ', 2535, 2245, 345, 56, 26),
        ('Thicket', 'พงหญ้า', 940, 1885, 160, 56, 27),
    ]

    print("[*] Processing 14 dark box labels...")
    for idx, (name, th_text, cx, cy, box_w, box_h, fsize) in enumerate(BOX_LABELS):
        font = ImageFont.truetype(font_path, fsize)
        bbox = font.getbbox(th_text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        bx1 = cx - box_w // 2
        by1 = cy - box_h // 2
        bx2 = cx + box_w // 2
        by2 = cy + box_h // 2

        draw_box.rounded_rectangle([bx1, by1, bx2, by2], radius=4, fill=box_color)

        tx = cx - tw // 2
        ty = cy - th // 2 - bbox[1]
        draw_box.text((tx, ty), th_text, font=font, fill=(250, 246, 237, 255))
        print(f"    [{idx+1}/14] Box: {name} -> {th_text}")

    print(f"\n[*] Saving final Thai minimap to destinations (4096x4096x32 RGBA):")
    
    os.makedirs(os.path.dirname(out_en_file), exist_ok=True)
    result_rgba.save(out_en_file)
    print(f"    [+] Saved: {out_en_file}")

    result_rgba.save(out_th_file1)
    print(f"    [+] Saved: {out_th_file1}")

    os.makedirs(os.path.dirname(out_th_file2), exist_ok=True)
    result_rgba.save(out_th_file2)
    print(f"    [+] Saved: {out_th_file2}")

    # Generate a preview image of the whole map (1024x1024)
    preview = result_rgba.resize((1024, 1024), Image.Resampling.LANCZOS)
    preview_path = os.path.join(base_dir, "thai_minimap_preview_1024.png")
    preview.save(preview_path)
    print(f"    [+] Saved preview: {preview_path}")

    print("\n[+] ALL DONE! Thai minimap created successfully.")

if __name__ == "__main__":
    main()
