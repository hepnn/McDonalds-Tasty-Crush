import cv2
import numpy as np
from functools import lru_cache
from multiprocessing import Pool
from culebratester_client.models import Point
import pyautogui
import keyboard
import culebratester_client
from culebratester_client.models import Point
from ppadb.client import Client

ITEMS = {
    'burger': 1,
    'fries': 2,
    'milkshake': 3,
    'soda': 4,
}

CONFIGURATION = None

api_instance = culebratester_client.DefaultApi(culebratester_client.ApiClient(CONFIGURATION))


adb = Client(host='127.0.0.1', port=5037)
devices = adb.devices()

if len(devices) == 0:
    print('no device attached')
    quit()

device = devices[0]

tile_size =  50
gap_size = 12

grid_left = 776
grid_top = 421
grid_right = 1141
grid_bottom = 787

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


def match_tile_multi_scale(args):
    i, j, tile, TEMPLATES, scales = args
    best_match = (0, None) 
    
    for scale in scales:
        for item, template in TEMPLATES.items():
            resized_template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
            res = cv2.matchTemplate(tile, resized_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_match[0]:  
                best_match = (max_val, item)
    
    if best_match[0] > 0.8:
        return (i, j, ITEMS[best_match[1]])
    return (i, j, 0)

def get_grid(screenshot_gray, pool ,scales=[0.9, 1.0, 1.1]):
    grid = [[0 for _ in range(6)] for _ in range(6)]
    args = []
    
    tile_positions = [(i, j, int(j * (tile_size + gap_size)), int(i * (tile_size + gap_size))) for i in range(6) for j in range(6)]
    
    for i, j, start_x, start_y in tile_positions:
        end_x = start_x + tile_size
        end_y = start_y + tile_size
        tile = screenshot_gray[start_y:end_y, start_x:end_x]
        args.append((i, j, tile, TEMPLATES, scales))

    results = pool.map(match_tile_multi_scale, args)

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
            item = grid[i][j]
            if item == 0:
                continue  # Skip empty tiles
            # Horizontal
            count = 1
            for k in range(j + 1, 6):
                if grid[i][k] == item:
                    count += 1
                else:
                    break
            if count >= 3:
                score += count
                j += count - 1  # Skip checked tiles
            # Vertical
            count = 1
            for k in range(i + 1, 6):
                if grid[k][j] == item:
                    count += 1
                else:
                    break
            if count >= 3:
                score += count
                i += count - 1  # Skip checked tiles
    return score

def perform_move(move):
    #Android screen specific values for input
    tile_s =  134
    gap_s = 19.5
    grid_l = 86
    grid_t = 878

    start, end = move
    start_x = start[1] * (tile_s + gap_s) + tile_s // 2
    start_y = start[0] * (tile_s + gap_s) + tile_s // 2
    end_x = end[1] * (tile_s + gap_s) + tile_s // 2
    end_y = end[0] * (tile_s + gap_s) + tile_s // 2
    start_x += grid_l
    start_y += grid_t
    end_x += grid_l
    end_y += grid_t
    
    start_point = Point(x=int(start_x), y=int(start_y))
    end_point = Point(x=int(end_x), y=int(end_y))

    segments = [start_point, end_point]
    
    body =  culebratester_client.SwipeBody(segments=segments, segment_steps=3)

    api_instance.ui_device_swipe_post(body=body)

def main(pool):
    while True:
        if(keyboard.is_pressed('q')):
            break

        screenshot_gray = get_screenshot()
        grid = get_grid(screenshot_gray, pool=pool)
        best_move = find_best_move(grid)
        if best_move is not None and not game_state_locked(screenshot_gray, grid):
            perform_move(best_move)
        else:
            print('Game locked, waiting...')

        for row in grid:
            print(row)


if __name__ == '__main__':
    with Pool() as pool:
        main(pool)