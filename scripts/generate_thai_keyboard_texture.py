import os
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Paths
base_dir = os.path.dirname(os.path.abspath(__file__))
dev_dir = os.path.abspath(os.path.join(base_dir, ".."))
font_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\Fonts\Lora-Bold.ttf"
backup_img_path = os.path.join(dev_dir, "คียบอด", "tex_113_1024x2048_backup.png")
output_img_path = os.path.join(dev_dir, "คียบอด", "tex_113_1024x2048.png")
preview_img_path = os.path.join(dev_dir, "คียบอด", "tex_113_1024x2048_thai_preview.png")

# Page 1: Consonants (ก-ฮ) + Digits (91 chars)
p1_chars = [
    # Row 1 (Cols 1-5 Left, Cols 6,8,10 Mid, Cols 11-15 Right)
    'ก', 'ข', 'ฃ', 'ค', 'ฅ',      'ล', 'ว', 'ศ',      '๐', '๑', '๒', '๓', '๔',
    # Row 2
    'ฆ', 'ง', 'จ', 'ฉ', 'ช',      'ษ', 'ส', 'ห', 'ฬ', 'อ',      '๕', '๖', '๗', '๘', '๙',
    # Row 3
    'ซ', 'ฌ', 'ญ', 'ฎ', 'ฏ',      'ฮ', ' ', '.',      '(', ')', '[', ']', '{',
    # Row 4
    'ฐ', 'ฑ', 'ฒ', 'ณ', 'ด',      '0', '1', '2', '3', '4',      '}', '+', '=', '*', ':',
    # Row 5
    'ต', 'ถ', 'ท', 'ธ', 'น',      '5', '6', '7', '8', '9',      ';', '"', "'", '<', '>',
    # Row 6
    'บ', 'ป', 'ผ', 'ฝ', 'พ',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    # Row 7
    'ฟ', 'ภ', 'ม', 'ย', 'ร'
]

# Page 2: Vowels, Tone marks, Digits, Math symbols (91 chars)
p2_chars = [
    # Row 1
    'ะ', 'า', 'ำ', 'ิ', 'ี',      '0', '1', '2',      '๐', '๑', '๒', '๓', '๔',
    # Row 2
    'ึ', 'ื', 'ุ', 'ู', 'เ',      '3', '4', '5', '6', '7',      '๕', '๖', '๗', '๘', '๙',
    # Row 3
    'แ', 'โ', 'ใ', 'ไ', '็',      '8', '9', ' ',      '[', ']', '{', '}', '<',
    # Row 4
    'ั', '่', '้', '๊', '๋',      '+', '-', '*', '/', '=',      '>', '"', "'", ':', ';',
    # Row 5
    '์', 'ๆ', 'ฯ', 'ฺ', 'ํ',      '%', '^', '&', '(', ')',      '~', '\\', '|', '_', '฿',
    # Row 6
    '๎', '๏', '๚', '๛', '฿',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    # Row 7
    'ฤ', 'ฦ', '.', ',', '-'
]

print("1. Loading backup image...")
orig_img = Image.open(backup_img_path).convert("RGBA")
arr = np.array(orig_img)
alpha = arr[:, :, 3]

print("2. Setting up font...")
font = ImageFont.truetype(font_path, 32)
COLOR_RGB = (210, 210, 210)

def render_centered_char(ch, tile_w=48, tile_h=48):
    if ch == ' ' or ch == '':
        return Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((64, 64), ch, font=font, fill=(*COLOR_RGB, 255))
    bbox = canvas.getbbox()
    if not bbox:
        return Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    ink = canvas.crop(bbox)
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    x_off = (tile_w - ink.width) // 2
    y_off = (tile_h - ink.height) // 2
    tile.paste(ink, (x_off, y_off), ink)
    return tile

def get_glyph_center(arr_alpha, approx_x, approx_y, radius=24):
    y1 = max(0, approx_y - radius)
    y2 = min(arr_alpha.shape[0], approx_y + radius)
    x1 = max(0, approx_x - radius)
    x2 = min(arr_alpha.shape[1], approx_x + radius)
    box = arr_alpha[y1:y2, x1:x2]
    ys, xs = np.where(box > 10)
    if len(xs) == 0:
        return approx_x, approx_y
    cx = x1 + int(np.mean(xs))
    cy = y1 + int(np.mean(ys))
    return cx, cy

# Grid definitions
cols_13 = [110, 163, 216, 270, 323,   406, 512, 618,   701, 754, 808, 861, 914]
cols_15 = [110, 163, 216, 270, 323,   406, 459, 512, 565, 618,   701, 754, 808, 861, 914]
cols_5  = [110, 163, 216, 270, 323]

hira_rows = [
    (16, cols_13),
    (70, cols_15),
    (124, cols_13),
    (178, cols_15),
    (232, cols_15),
    (287, cols_15),
    (341, cols_5)
]

kata_rows = [
    (400, cols_13),
    (454, cols_15),
    (508, cols_13),
    (562, cols_15),
    (616, cols_15),
    (671, cols_15),
    (725, cols_5)
]

# Create output image starting from copy of original
out_arr = arr.copy()

# Preserve special decorative symbols from original: 'ー', '～', '＝', '♥', '★'
PRESERVE_SYMBOLS = {'ー', '～', '＝', '♥', '★'}

print("3. Replacing Hiragana section with Thai Page 1...")
hira_idx = 0
for r_idx, (y_approx, cols) in enumerate(hira_rows):
    for c_idx, x_approx in enumerate(cols):
        cx, cy = get_glyph_center(alpha, x_approx, y_approx)
        thai_ch = p1_chars[hira_idx]
        hira_idx += 1
        
        if thai_ch in PRESERVE_SYMBOLS:
            continue
        
        # Clear original Japanese character bounding box (50x48)
        y1 = max(0, cy - 24)
        y2 = min(2048, cy + 24)
        x1 = max(0, cx - 25)
        x2 = min(1024, cx + 25)
        out_arr[y1:y2, x1:x2] = 0

print("4. Replacing Katakana section with Thai Page 2...")
kata_idx = 0
for r_idx, (y_approx, cols) in enumerate(kata_rows):
    for c_idx, x_approx in enumerate(cols):
        cx, cy = get_glyph_center(alpha, x_approx, y_approx)
        thai_ch = p2_chars[kata_idx]
        kata_idx += 1
        
        if thai_ch in PRESERVE_SYMBOLS:
            continue
        
        # Clear original Japanese character bounding box (50x48)
        y1 = max(0, cy - 24)
        y2 = min(2048, cy + 24)
        x1 = max(0, cx - 25)
        x2 = min(1024, cx + 25)
        out_arr[y1:y2, x1:x2] = 0

# Convert cleared array to Image
result_img = Image.fromarray(out_arr, "RGBA")

print("5. Drawing centered Thai characters...")
# Draw Page 1
hira_idx = 0
for r_idx, (y_approx, cols) in enumerate(hira_rows):
    for c_idx, x_approx in enumerate(cols):
        cx, cy = get_glyph_center(alpha, x_approx, y_approx)
        thai_ch = p1_chars[hira_idx]
        hira_idx += 1
        if thai_ch in PRESERVE_SYMBOLS or thai_ch == ' ':
            continue
        tile = render_centered_char(thai_ch, 48, 48)
        result_img.paste(tile, (cx - 24, cy - 24), tile)

# Draw Page 2
kata_idx = 0
for r_idx, (y_approx, cols) in enumerate(kata_rows):
    for c_idx, x_approx in enumerate(cols):
        cx, cy = get_glyph_center(alpha, x_approx, y_approx)
        thai_ch = p2_chars[kata_idx]
        kata_idx += 1
        if thai_ch in PRESERVE_SYMBOLS or thai_ch == ' ':
            continue
        tile = render_centered_char(thai_ch, 48, 48)
        result_img.paste(tile, (cx - 24, cy - 24), tile)

print(f"6. Saving outputs...")
result_img.save(output_img_path)
result_img.save(preview_img_path)

# Also save a 50% preview for quick viewing
preview_half = result_img.crop((0, 0, 1024, 760)).resize((512, 380), Image.Resampling.LANCZOS)
preview_half_path = os.path.join(dev_dir, "คียบอด", "tex_113_thai_keyboard_cropped_preview.png")
preview_half.save(preview_half_path)

print(f"SUCCESS: Saved {output_img_path}")
print(f"SUCCESS: Saved {preview_half_path}")
