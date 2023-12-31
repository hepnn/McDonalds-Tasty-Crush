import time
from PIL import Image
import cv2
import numpy as np
from functools import lru_cache
from multiprocessing import Pool
from culebratester_client.models import Point
import random
import pyautogui

ITEMS = {
    'burger': 1,
    'fries': 2,
    'milkshake': 3,
    'soda': 4,
}

tile_size =  52
gap_size = 4.45

grid_left = 64
grid_top = 356
grid_right = 396
grid_bottom = 688

@lru_cache(maxsize=None)
def load_and_resize_image(base_path, image_name, size):
    path = f'A://code//McD-tasty-crush//{base_path}//{image_name}.jpg'
    img = cv2.imread(path, 0)
    img = cv2.equalizeHist(img)
    return cv2.resize(img, size)

tile_size_x_y = (tile_size, tile_size)

TEMPLATES = {
    name: load_and_resize_image('assets', name, tile_size_x_y) for name in ['burger', 'fries', 'milkshake', 'soda']
}

TEMPLATES_ANIMATING = {
    name: load_and_resize_image('assets_animating', name, tile_size_x_y) for name in ['burger', 'fries', 'milkshake', 'soda']
}


def get_screenshot():
    screenshot = pyautogui.screenshot(region=(grid_left, grid_top, grid_right - grid_left, grid_bottom - grid_top))
    screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    screenshot_gray = cv2.equalizeHist(screenshot_gray)
    return screenshot_gray


def match_tile(args):
    i, j, tile, TEMPLATES = args
    for item, template in TEMPLATES.items():
        res = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > 0.8: # Increase the threshold
            return (i, j, ITEMS[item])
    return (i, j, 0)

def get_grid(screenshot_gray):
    grid = [[0 for _ in range(6)] for _ in range(6)]
    args = []
    for i in range(6):
        for j in range(6):
            start_x = int(j * (tile_size + gap_size))
            end_x = start_x + tile_size
            start_y = int(i * (tile_size + gap_size))
            end_y = start_y + tile_size
            tile = screenshot_gray[start_y:end_y, start_x:end_x]
            args.append((i, j, tile, TEMPLATES))

    with Pool() as p:
        results = p.map(match_tile, args)

    for i, j, item in results:
        grid[i][j] = item

    return grid

def game_state_locked(screenshot_gray, grid):
    # If any tile is empty, the game is locked
    if any(0 in row for row in grid):
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
                if max_val > 0.8:
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
    start_x += grid_left
    start_y += grid_top
    end_x += grid_left
    end_y += grid_top
    
    mid_points = []
    for fraction in [0.25, 0.5, 0.75]:
        mid_x = start_x + fraction * (end_x - start_x) + random.uniform(-5, 5)
        mid_y = start_y + fraction * (end_y - start_y) + random.uniform(-5, 5)
        mid_points.append((int(mid_x), int(mid_y)))
    
    pyautogui.mouseDown(start_x, start_y)
    for point in mid_points:
        pyautogui.moveTo(point)
        time.sleep(0.05)  # add a small delay between each movement
    pyautogui.mouseUp(end_x, end_y)



def main():
    while True:
        screenshot_gray = get_screenshot()
        grid = get_grid(screenshot_gray)
        best_move = find_best_move(grid)
        if best_move is not None and not game_state_locked(screenshot_gray, grid):
            perform_move(best_move)
        else:
            print('Game locked, waiting...')

        for row in grid:
            print(row)
        time.sleep(0.2)

if __name__ == '__main__':
    main()
    