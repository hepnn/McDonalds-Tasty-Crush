def get_grid(screenshot_gray):
    grid = [[0 for _ in range(6)] for _ in range(6)]
    for i in range(6):
        for j in range(6):
            start_x = int(j * (tile_size + gap_size))
            end_x = start_x + tile_size
            start_y = int(i * (tile_size + gap_size))
            end_y = start_y + tile_size
            tile = screenshot_gray[start_y:end_y, start_x:end_x]
            # cv2.imshow('tile', tile)
            # cv2.waitKey(0)
            for item, template in TEMPLATES.items():
                res = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val > 0.7:
                    grid[i][j] = ITEMS[item]
                    break
    return grid