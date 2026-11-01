from PIL import ImageGrab

img = ImageGrab.grab()
out_path = r'C:\Users\Administrator\.gemini\antigravity\scratch\current_game_screen.png'
img.save(out_path)
print(f'Saved screenshot to {out_path}')
