import json
from pathlib import Path
import cv2
import numpy as np
import os

# 建立空函式給 TrackBar 用
def empty(v):
    pass

# 可編輯的顏色名稱
editable_colors = ['Red', 'Blue']
current_color = 'Red'

# 建立 HSV 調整介面
cv2.namedWindow("HSV Adjust", cv2.WINDOW_NORMAL)
cv2.resizeWindow("HSV Adjust", 400, 300)

# 加入顏色切換 TrackBar
cv2.createTrackbar("Color (0=Red, 1=Blue)", "HSV Adjust", 0, len(editable_colors)-1, empty)

# 建立 HSV 上下限 TrackBars
for name in ['Hue Min', 'Hue Max', 'Sat Min', 'Sat Max', 'Val Min', 'Val Max']:
    cv2.createTrackbar(name, "HSV Adjust", 0, 255, empty)

# 初始化預設值（可依照實測調整）
initial_values = {
    'Red': ([3, 105, 100], [17, 196, 157]),
    'Blue': ([108, 117, 133], [125, 173, 195])
}

# 設定初始拉條位置
for i, name in enumerate(['Hue Min', 'Sat Min', 'Val Min']):
    cv2.setTrackbarPos(name, "HSV Adjust", initial_values[current_color][0][i])
for i, name in enumerate(['Hue Max', 'Sat Max', 'Val Max']):
    cv2.setTrackbarPos(name, "HSV Adjust", initial_values[current_color][1][i])

# 開啟攝影機畫面預覽
cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 更新目前編輯的顏色
    current_color = editable_colors[cv2.getTrackbarPos("Color (0=Red, 1=Blue)", "HSV Adjust")]

    # 取得 HSV 範圍
    h_min = cv2.getTrackbarPos('Hue Min', "HSV Adjust")
    h_max = cv2.getTrackbarPos('Hue Max', "HSV Adjust")
    s_min = cv2.getTrackbarPos('Sat Min', "HSV Adjust")
    s_max = cv2.getTrackbarPos('Sat Max', "HSV Adjust")
    v_min = cv2.getTrackbarPos('Val Min', "HSV Adjust")
    v_max = cv2.getTrackbarPos('Val Max', "HSV Adjust")

    # 顯示即時濾色效果
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    combined = np.hstack((frame, result))
    cv2.imshow("Preview", combined)

    key = cv2.waitKey(1)
    # 儲存邏輯（trigger：按下 s 鍵）
    if key == ord('s'):
        color_config_path = Path(__file__).parent / "OpenCV2Arduino" / "color_config.json"

        new_data = {}
        for color in editable_colors:
            if color == current_color:
                lower = [h_min, s_min, v_min]
                upper = [h_max, s_max, v_max]
                new_data[color] = [lower, upper]
            else:
                new_data[color] = initial_values[color]

        with open(color_config_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4)

        print(f"[Saved] HSV value for '{current_color}' updated in color_config.json.")

    elif key == ord('q'):  # 離開
        break

cap.release()
cv2.destroyAllWindows()
