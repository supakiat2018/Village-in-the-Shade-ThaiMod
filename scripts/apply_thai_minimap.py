"""
Script to apply Thai translation labels to minimap textures (aut, spr, sum, win).
Game: Village in the Shade (ほの暮しの庭)
"""

import os
import sys
import argparse
from collections import deque
from PIL import Image
import numpy as np

# Coordinates (cx, cy) and min coverage width (min_w) for all 32 labels
# Calibrated for 4096 x 4096 resolution
LABEL_CONFIG = {
    'Altar': (2390, 1975, 140),
    'Cemetery': (1160, 1540, 200),
    'Chasm': (1210, 2835, 170),
    'Chawantei': (2340, 2200, 220),
    'Clock Tower': (2570, 2165, 210),
    'Crossroads bulletin board': (2160, 2515, 280),
    'Crossroads fishing spot': (2440, 2535, 270),
    'Forest': (2310, 885, 240),
    'Hot Spring': (1570, 1390, 200),
    'Hunting Lodge': (1925, 1695, 260),
    'Kiki Construction': (2200, 1950, 310),
    'Kiki Manor': (2460, 1480, 220),
    'Kusunoki Clinic': (2665, 2100, 280),
    'Library': (2500, 1925, 190),
    'Mountain foot fishing spot': (2140, 1490, 360),
    'Mountain pass': (2840, 3175, 270),
    'Mountain peak': (1578, 648, 200),
    'Mountain pond fishing spot': (1538, 868, 300),
    'Muko Crossing': (2020, 2440, 230),
    'My House': (1850, 2350, 210),
    'Nodobotoke Mountain Trail': (1840, 1910, 340),
    'Okami Pond': (3040, 1775, 220),
    'Plaza': (2485, 2125, 205),
    'Quarry': (1330, 2045, 180),
    'Quarry fishing spot': (1465, 2170, 270),
    'Street Vendor': (2570, 2360, 270),
    'Tagami General Store': (2555, 2245, 370),
    'Thicket': (945, 1885, 210),
    'Village bulletin board': (2628, 2012, 280),
    'Village creek fishing spot': (2750, 2455, 310),
    'Waterfall fishing spot': (3210, 1835, 290),
    'Watermill': (2330, 1800, 190)
}

def extract_connected_boxes(img_path):
    """Detect non-transparent bounding boxes from RGBA image."""
    img = Image.open(img_path).convert('RGBA')
    arr = np.array(img)
    alpha = arr[:, :, 3] > 20
    h, w = alpha.shape
    visited = np.zeros((h, w), dtype=bool)
    boxes = []
    
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if alpha[y, x] and not visited[y, x]:
                q = deque([(y, x)])
                visited[y, x] = True
                min_y, max_y = y, y
                min_x, max_x = x, x
                while q:
                    cy, cx = q.popleft()
                    if cy < min_y: min_y = cy
                    if cy > max_y: max_y = cy
                    if cx < min_x: min_x = cx
                    if cx > max_x: max_x = cx
                    for dy, dx in [(-2,0), (2,0), (0,-2), (0,2)]:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            if alpha[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                q.append((ny, nx))
                if (max_y - min_y) > 30 and (max_x - min_x) > 50:
                    min_x = max(0, min_x - 2)
                    min_y = max(0, min_y - 2)
                    max_x = min(w, max_x + 3)
                    max_y = min(h, max_y + 3)
                    boxes.append((min_x, min_y, max_x, max_y))
    return img, boxes

def prepare_thai_labels(base_dir, cache_dir):
    """Extract and cache all 32 Thai labels from ChatGPT images."""
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if already cached
    all_cached = True
    for name in LABEL_CONFIG:
        safe_name = name.replace(' ', '_').lower()
        if not os.path.exists(os.path.join(cache_dir, f'{safe_name}.png')):
            all_cached = False
            break
            
    if all_cached:
        print("[+] All 32 Thai labels are already cached.")
        return

    print("[*] Extracting Thai labels from ChatGPT images...")
    img1_path = os.path.join(base_dir, "ChatGPT Image 22 ก.ย. 2569 20_50_23.png")
    img2_path = os.path.join(base_dir, "ChatGPT Image 22 ก.ย. 2569 21_17_08.png")

    img1, b1 = extract_connected_boxes(img1_path)
    b1.sort(key=lambda b: (b[1] // 80, b[0]))

    names1 = [
        'Mountain peak', 'Mountain pond fishing spot', 'Forest',
        'Hot Spring', 'Nodobotoke Mountain Trail', 'Kiki Manor',
        'Hunting Lodge', 'Library', 'Okami Pond',
        'Thicket', 'Quarry', 'Kiki Construction', 'Altar',
        'Kusunoki Clinic', 'Chawantei', 'Clock Tower',
        'My House', 'Tagami General Store', 'Street Vendor',
        'Chasm', 'Muko Crossing', 'Village bulletin board',
        'Crossroads bulletin board', 'Quarry fishing spot',
        'Waterfall fishing spot', 'Village creek fishing spot',
        'Mountain pass', 'Crossroads fishing spot', 'Mountain foot fishing spot'
    ]

    for name, box in zip(names1, b1):
        crop = img1.crop(box)
        safe_name = name.replace(' ', '_').lower()
        crop.save(os.path.join(cache_dir, f'{safe_name}.png'))

    img2, b2 = extract_connected_boxes(img2_path)
    b2.sort(key=lambda b: (b[1] // 200, b[0]))
    names2 = ['Cemetery', 'Watermill', 'Plaza']

    for name, box in zip(names2, b2):
        crop = img2.crop(box)
        safe_name = name.replace(' ', '_').lower()
        crop.save(os.path.join(cache_dir, f'{safe_name}.png'))

    print("[+] Extracted and cached all 32 Thai labels successfully.")

def make_box_fit(lbl, min_w, target_h=55):
    """
    Scale box to target_h while widening padding to min_w cleanly 
    without stretching text or borders.
    """
    scale = target_h / lbl.height
    curr_w = int(lbl.width * scale)
    scaled = lbl.resize((curr_w, target_h), Image.Resampling.LANCZOS)
    if curr_w >= min_w:
        return scaled

    pad_total = min_w - curr_w
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left

    arr = np.array(scaled)
    # Brightness of text characters
    is_text = (arr[:, :, :3].mean(axis=2) > 150) & (arr[:, :, 3] > 100)
    tx = np.where(is_text.any(axis=0))[0]
    if len(tx) == 0:
        return scaled
        
    left_margin = tx[0]
    right_margin = tx[-1]

    split_l = max(6, left_margin // 2)
    split_r = min(curr_w - 6, right_margin + (curr_w - right_margin) // 2)

    p1 = scaled.crop((0, 0, split_l, target_h))
    s_l = scaled.crop((split_l, 0, split_l + 1, target_h)).resize((pad_left, target_h), Image.Resampling.NEAREST)
    p2 = scaled.crop((split_l, 0, split_r, target_h))
    s_r = scaled.crop((split_r, 0, split_r + 1, target_h)).resize((pad_right, target_h), Image.Resampling.NEAREST)
    p3 = scaled.crop((split_r, 0, curr_w, target_h))

    out = Image.new('RGBA', (min_w, target_h), (0, 0, 0, 0))
    x = 0
    for part in [p1, s_l, p2, s_r, p3]:
        out.paste(part, (x, 0))
        x += part.width
    return out

def process_minimap(input_path, output_path, cache_dir, target_h=55):
    """Apply all 32 Thai labels onto the minimap."""
    if not os.path.exists(input_path):
        print(f"[-] Input file not found: {input_path}")
        return False

    print(f"[*] Processing: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    minimap = Image.open(input_path).convert('RGBA')
    w, h = minimap.size
    print(f"    Dimensions: {w}x{h}, Mode: {minimap.mode}")

    out_map = minimap.copy()

    for idx, (name, (cx, cy, min_w)) in enumerate(LABEL_CONFIG.items()):
        safe_name = name.replace(' ', '_').lower()
        lbl_file = os.path.join(cache_dir, f'{safe_name}.png')
        if not os.path.exists(lbl_file):
            print(f"[-] Missing label file: {lbl_file}")
            continue

        lbl = Image.open(lbl_file).convert('RGBA')
        fitted_box = make_box_fit(lbl, min_w, target_h)
        pos = (cx - fitted_box.width // 2, cy - fitted_box.height // 2)
        out_map.alpha_composite(fitted_box, pos)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    out_map.save(output_path)
    file_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[+] Successfully saved Thai minimap: {output_path} ({file_mb:.2f} MB)\n")
    return True

def main():
    parser = argparse.ArgumentParser(description="Apply Thai translation labels to game minimaps.")
    parser.add_argument('--season', choices=['aut', 'spr', 'sum', 'win', 'all'], default='aut',
                        help="Season to process: aut (autumn), spr (spring), sum (summer), win (winter), or all (default: aut)")
    parser.add_argument('--input', type=str, default=None, help="Custom input image path")
    parser.add_argument('--output', type=str, default=None, help="Custom output image path")
    args = parser.parse_args()

    base_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_minimap_en"
    cache_dir = os.path.join(base_dir, "thai_labels_cache")

    # 1. Prepare Thai labels
    prepare_thai_labels(base_dir, cache_dir)

    # 2. Process specified files
    if args.input and args.output:
        process_minimap(args.input, args.output, cache_dir)
        return

    season_map = {
        'aut': ('minimap_01_aut_en.png', 'minimap_01_aut_th.png'),
        'spr': ('minimap_01_spr_en.png', 'minimap_01_spr_th.png'),
        'sum': ('minimap_01_sum_en.png', 'minimap_01_sum_th.png'),
        'win': ('minimap_01_win_en.png', 'minimap_01_win_th.png'),
    }

    if args.season == 'all':
        targets = list(season_map.keys())
    else:
        targets = [args.season]

    for s in targets:
        in_name, out_name = season_map[s]
        in_p = os.path.join(base_dir, in_name)
        out_p = os.path.join(base_dir, out_name)
        process_minimap(in_p, out_p, cache_dir)

if __name__ == '__main__':
    main()
