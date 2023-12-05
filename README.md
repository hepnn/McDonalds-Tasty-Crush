# McDonalds-Tasty-Crush


1. Capture device screen, crop game board
2. Use image matching to detect tile classes
3. calculate the best move



https://github.com/hepnn/McDonalds-Tasty-Crush/assets/47219299/48232cd2-2834-4910-babe-ce4b62a3bd19



### Setup

There are 2 version: run.py & run_pyautogui.py 
Second one is using pyautogui, it is much faster and more efficient, because no delay from ADB

I switched to culebra from ADB shell, because adb shell has a huge (1s +) delay
You can follow CulebraTester2 setup guide here https://github.com/dtmilano/CulebraTester2-public

You'll have to find your own grid size and tile size as these are hardcoded

You can do so by enabling `Pointer location` in android developer settings and then getting x, y values from each grid corner and from tile corners. 

### How it works:

1. Capture full device screen 
2. Crop it to the grid's size
3. Convert the RGB images to greyscale and apply histogram equalization
4. Use OpenCV to match given template assets with the game board items
5. Use brute force to find the best move (this should be improved)


TODO:
Improve screenshot taking time, currently it averages at 1.7 seconds
Somehow avoid hardcoded sizes and coordinates
