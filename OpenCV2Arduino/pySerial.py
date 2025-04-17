import cv2
import numpy as np
import serial
import time

# 串列埠設定
COM_PORT = 'COM4'
BAUD_RATES = 9600
ser = serial.Serial(COM_PORT, BAUD_RATES, timeout=1)

# 影像來源
cap = cv2.VideoCapture(1)

# 面積閾值
threshold_area = 1000

# 紀錄上一個動作
last_action = None 

# 自訂 HSV 顏色範圍
color_ranges = {
    'Red': ([0, 82, 192], [27, 203, 255]),
    'Green': ([84, 64, 146], [135, 247, 200])
}

# 對應動作字元（形狀 + 顏色）
action_map = {
    ('Red', 'Triangle'): 'A',
    ('Red', 'Square'): 'B',
    ('Green', 'Triangle'): 'C',
    ('Green', 'Square'): 'D'
}
time.sleep(3)
# 傳送測試信號
print("發送測試訊號...")
ser.write(b't')
time.sleep(4)
print("開始影像辨識...")

# 主函式：尋找目標
def find_shapes(frame, hsv_frame):
    result_action = None

    for label, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv_frame, np.array(lower), np.array(upper))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > threshold_area:
                
                epsilon = 0.02 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                x, y, w, h = cv2.boundingRect(approx)

                shape = None
                if len(approx) == 3:
                    shape = 'Triangle'
                elif len(approx) == 4:
                    shape = 'Square'
                else:
                    continue

                action = action_map.get((label, shape))
                if action and not result_action:
                    result_action = action  # 優先只傳第一個偵測到的

                # 繪製框與標籤
                color_bgr = (0, 0, 255) if label == 'Red' else (0, 255, 0)
                cv2.drawContours(frame, [approx], -1, color_bgr, 2)
                cv2.putText(frame, f"{label} {shape} ({action})", (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)
    return result_action

# 主程式迴圈
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 前處理
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # 偵測形狀並產生動作
        action = find_shapes(frame, hsv)

        # 若有新動作，且與上一個動作不同，才傳送
        if action and action != last_action:
            print(f'傳送指令: {action}')
            ser.write(action.encode())
            last_action = action
            time.sleep(5)

        # 若沒有任何物體被偵測，重置 last_action
        #elif not action:
            #print(f'進行中: {action}')
            #last_action = None

        cv2.imshow("Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("中斷程式")

finally:
    cap.release()
    cv2.destroyAllWindows()
    ser.close()
