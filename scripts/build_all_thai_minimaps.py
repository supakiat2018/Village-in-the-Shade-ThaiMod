"""
Build All Thai Minimap Textures
Game: Village in the Shade (ほの暮しの庭)
Processes 4 minimap files:
  1. minimap_01_spr_en.png (Spring 01, 4096x4096x32, 32 labels)
  2. minimap_01_sum_en.png (Summer 01, 8192x8192x32, 32 labels, scale 2x)
  3. minimap_01_win_en.png (Winter 01, 8192x8192x32, 32 labels, scale 2x)
  4. minimap_11_spr_en.png (Spring 11, 4096x4096x32, 28 labels)
"""

import os
import shutil
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

MAP_11_EXCLUDED = {
    'Hot Spring',
    'My House',
}

def process_single_minimap(filename, base_dir, font_path):
    src_file = os.path.join(base_dir, "04ภาพen", filename)
    bak_file = src_file + ".bak"
    th_filename = filename.replace("_en.png", "_th.png")
    out_th_file1 = os.path.join(base_dir, "04ภาพen", th_filename)
    out_th_file2 = os.path.join(base_dir, "extracted_minimap_en", th_filename)

    if not os.path.exists(bak_file):
        print(f"[*] Creating backup: {bak_file}")
        shutil.copy2(src_file, bak_file)

    print(f"\n==================================================")
    print(f"[*] Processing: {filename}")
    print(f"    Source (backup): {bak_file}")

    t0 = time.time()
    img = Image.open(bak_file).convert("RGBA")
    w, h = img.size
    scale = w // 4096
    print(f"    Dimensions: {w}x{h}, Mode: {img.mode}, Scale: {scale}x")

    is_map_11 = "minimap_11" in filename

    alpha_arr = np.array(img.getchannel("A"))
    rgb_img = img.convert("RGB")
    arr = np.array(rgb_img)

    # 1. Process Parchment Labels
    p_labels = [l for l in PARCHMENT_LABELS if not (is_map_11 and l[0] in MAP_11_EXCLUDED)]
    print(f"    [*] Processing {len(p_labels)} parchment labels...")

    for name, th_text, cx, cy, hw, hh, fsize in p_labels:
        scx, scy = cx * scale, cy * scale
        shw, shh = hw * scale, hh * scale
        sfsize = fsize * scale
        x1, y1 = max(0, scx - shw), max(0, scy - shh)
        x2, y2 = min(w, scx + shw), min(h, scy + shh)

        patch = arr[y1:y2, x1:x2].copy()
        gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)

        halo = (gray > 185).astype(np.uint8)
        dark = (gray < 85).astype(np.uint8)
        kernel = np.ones((5 * scale, 5 * scale), np.uint8)
        halo_dil = cv2.dilate(halo, kernel, iterations=1)
        text_mask = ((dark & halo_dil) | (halo & cv2.dilate(dark, kernel, iterations=1))).astype(np.uint8) * 255
        text_mask = cv2.dilate(text_mask, np.ones((3 * scale, 3 * scale), np.uint8), iterations=1)

        inpaint_r = 3 * scale
        inpainted = cv2.inpaint(patch, text_mask, inpaintRadius=inpaint_r, flags=cv2.INPAINT_TELEA)

        res = Image.fromarray(inpainted)
        draw = ImageDraw.Draw(res)
        font = ImageFont.truetype(font_path, sfsize)
        bbox = font.getbbox(th_text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (res.width - tw) // 2
        ty = (res.height - th) // 2 - bbox[1]

        stroke_w = max(2, 2 * scale)
        draw.text((tx, ty), th_text, font=font, fill=(35, 30, 25), stroke_width=stroke_w, stroke_fill=(250, 246, 237))
        arr[y1:y2, x1:x2] = np.array(res)

    # 2. Process Box Labels
    result_rgba = Image.fromarray(np.dstack([arr, alpha_arr]), mode="RGBA")
    draw_box = ImageDraw.Draw(result_rgba)
    box_color = (46, 40, 36, 255)

    b_labels = [l for l in BOX_LABELS if not (is_map_11 and l[0] in MAP_11_EXCLUDED)]
    print(f"    [*] Processing {len(b_labels)} dark box labels...")

    for name, th_text, cx, cy, box_w, box_h, fsize in b_labels:
        scx, scy = cx * scale, cy * scale
        sbox_w, sbox_h = box_w * scale, box_h * scale
        sfsize = fsize * scale

        font = ImageFont.truetype(font_path, sfsize)
        bbox = font.getbbox(th_text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        bx1 = scx - sbox_w // 2
        by1 = scy - sbox_h // 2
        bx2 = scx + sbox_w // 2
        by2 = scy + sbox_h // 2

        draw_box.rounded_rectangle([bx1, by1, bx2, by2], radius=4 * scale, fill=box_color)

        tx = scx - tw // 2
        ty = scy - th // 2 - bbox[1]
        draw_box.text((tx, ty), th_text, font=font, fill=(250, 246, 237, 255))

    # 3. Save files
    print(f"    [*] Saving output files...")
    result_rgba.save(src_file)
    print(f"        [+] Overwritten primary: {src_file}")

    result_rgba.save(out_th_file1)
    print(f"        [+] Saved copy: {out_th_file1}")

    os.makedirs(os.path.dirname(out_th_file2), exist_ok=True)
    result_rgba.save(out_th_file2)
    print(f"        [+] Saved copy: {out_th_file2}")

    # Generate 1024 preview
    preview = result_rgba.resize((1024, 1024), Image.Resampling.LANCZOS)
    p_name = filename.replace("_en.png", "_preview_1024.png")
    preview_path = os.path.join(base_dir, p_name)
    preview.save(preview_path)
    print(f"        [+] Saved preview: {preview_path}")

    elapsed = time.time() - t0
    print(f"    [+] Finished {filename} in {elapsed:.1f}s")

def main():
    base_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    font_path = os.path.join(base_dir, "data", "lora-thai-jp-bold.ttf")

    target_files = [
        "minimap_01_spr_en.png",
        "minimap_01_sum_en.png",
        "minimap_01_win_en.png",
        "minimap_11_spr_en.png",
    ]

    total_t0 = time.time()
    for fn in target_files:
        process_single_minimap(fn, base_dir, font_path)

    total_elapsed = time.time() - total_t0
    print(f"\n==================================================")
    print(f"[+] ALL 4 MINIMAPS COMPLETED SUCCESSFULLY in {total_elapsed:.1f}s!")

if __name__ == "__main__":
    main()
