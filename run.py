import time
from PIL import Image
import cv2
import io
import numpy as np
import tkinter as tk
import pyautogui
from ppadb.client import Client
from functools import lru_cache

ITEMS = {
    'burger': 1,
    'fries': 2,
    'milkshake': 3,
    'soda': 4,
}

tile_size =  134
gap_size = 19.5

grid_left = 86
grid_top = 878
grid_right = 990
grid_bottom = 1777

@lru_cache(maxsize=None)
def load_and_resize_image(base_path, image_name, size):
    path = f'A://code//McD-tasty-crush//{base_path}//{image_name}.jpg'
    return cv2.resize(cv2.imread(path, 0), size)

tile_size_x_y = (tile_size, tile_size)

TEMPLATES = {
    name: load_and_resize_image('assets', name, tile_size_x_y) for name in ['burger', 'fries', 'milkshake', 'soda']
}

TEMPLATES_ANIMATING = {
    name: load_and_resize_image('assets_animating', name, tile_size_x_y) for name in ['burger', 'fries', 'milkshake', 'soda']
}


adb = Client(host='127.0.0.1', port=5037)
devices = adb.devices()

if len(devices) == 0:
    print('no device attached')
    quit()

device = devices[0]
    

def get_screenshot(device):
    screenshot = device.screencap()
    with Image.open(io.BytesIO(screenshot)) as img:
        cropped_img = img.crop((grid_left, grid_top, grid_right, grid_bottom))
        screenshot_gray = cv2.cvtColor(np.array(cropped_img), cv2.COLOR_RGB2GRAY)
    return screenshot_gray

def get_grid(screenshot_gray):
    grid = [[0 for _ in range(6)] for _ in range(6)]
    for i in range(6):
        for j in range(6):
            start_x = int(j * (tile_size + gap_size))
            end_x = start_x + tile_size
            start_y = int(i * (tile_size + gap_size))
            end_y = start_y + tile_size
            tile = screenshot_gray[start_y:end_y, start_x:end_x]
            for item, template in TEMPLATES.items():
                res = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > 0.7:
                    grid[i][j] = ITEMS[item]
                    break
    return grid

def game_state_locked(screenshot_gray, grid):
    if any(0 in row for row in grid):
        # If any tile is empty, the game is locked
        return True
    
    for i in range(6):
        for j in range(6):
            start_x = int(j * (tile_size + gap_size))
            end_x = start_x + tile_size
            start_y = int(i * (tile_size + gap_size))
            end_y = start_y + tile_size
            tile = screenshot_gray[start_y:end_y, start_x:end_x]
            for item, template in TEMPLATES_ANIMATING.items():
                res = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > 0.9:
                    # locked                    
                    return True
    # If no animating template matches, the game is not locked
    return False

def find_best_move(grid):
    best_score = 0
    best_move = None

    for i in range(6):
        for j in range(6):
            for dx, dy in [(1, 0), (0, 1)]:
                if i + dx < 6 and j + dy < 6 and grid[i][j] != grid[i + dx][j + dy]:
                    grid[i][j], grid[i + dx][j + dy] = grid[i + dx][j + dy], grid[i][j]
                    score = calculate_score(grid)
                    if score > best_score:
                        best_score = score
                        best_move = ((i, j), (i + dx, j + dy))
                    grid[i][j], grid[i + dx][j + dy] = grid[i + dx][j + dy], grid[i][j]

    return best_move

def calculate_score(grid):
    score = 0
    for i in range(6):
        for j in range(6):
            # Horizontal
            for size in range(3, 6):
                if j <= 6 - size and all(grid[i][j+k] == grid[i][j] for k in range(size)):
                    score += size
            # Vertical
            for size in range(3, 6):
                if i <= 6 - size and all(grid[i+k][j] == grid[i][j] for k in range(size)):
                    score += size
    return score

def perform_move(move):
    start, end = move
    start_x = start[1] * (tile_size + gap_size) + tile_size // 2
    start_y = start[0] * (tile_size + gap_size) + tile_size // 2
    end_x = end[1] * (tile_size + gap_size) + tile_size // 2
    end_y = end[0] * (tile_size + gap_size) + tile_size // 2
    # Convert the coordinates to the original scale
    start_x += grid_left
    start_y += grid_top
    end_x += grid_left
    end_y += grid_top

    device.shell(f'input swipe {start_x} {start_y} {end_x} {end_y} 100')



def main():
    while True:
        screenshot_gray = get_screenshot(device)
        grid = get_grid(screenshot_gray)
        best_move = find_best_move(grid)
        if best_move is not None and not game_state_locked(screenshot_gray, grid):
            perform_move(best_move)
            time.sleep(2)  
        else:
            print('Game locked, waiting...')

        for row in grid:
            print(row)

main()

# root = tk.Tk()

# grid_frame = tk.Frame(root)
# grid_frame.pack()

# for i in range(6):
#     for j in range(6):
#         cell_value = grid[i][j]
#         cell_label = tk.Label(grid_frame, text=cell_value, relief="solid", borderwidth=1, padx=15, pady=10)
#         cell_label.grid(row=i, column=j)

# root.mainloop()
