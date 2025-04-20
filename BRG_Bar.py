import cv2
import numpy as np
import json
import os

# 設定統一路徑（位於 OpenCV2Arduino 資料夾內）
CONFIG_PATH = os.path.join("OpenCV2Arduino", "color_config.json")

class HSVAdjuster:
    def __init__(self):
        self.color_options = ["Red", "Blue"]
        self.current_color_index = 0
        self.color_name = self.color_options[self.current_color_index]
        self.window_name = "HSV Adjust"

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")

        # 建立 Trackbars
        cv2.namedWindow(self.window_name)
        self._create_trackbars()

        self.hsv_ranges = self._load_config()

    def _create_trackbars(self):
        cv2.createTrackbar("Hue Min", self.window_name, 0, 179, lambda x: None)
        cv2.createTrackbar("Hue Max", self.window_name, 10, 179, lambda x: None)
        cv2.createTrackbar("Sat Min", self.window_name, 100, 255, lambda x: None)
        cv2.createTrackbar("Sat Max", self.window_name, 255, 255, lambda x: None)
        cv2.createTrackbar("Val Min", self.window_name, 100, 255, lambda x: None)
        cv2.createTrackbar("Val Max", self.window_name, 255, 255, lambda x: None)

    def _get_trackbar_values(self):
        h_min = cv2.getTrackbarPos("Hue Min", self.window_name)
        h_max = cv2.getTrackbarPos("Hue Max", self.window_name)
        s_min = cv2.getTrackbarPos("Sat Min", self.window_name)
        s_max = cv2.getTrackbarPos("Sat Max", self.window_name)
        v_min = cv2.getTrackbarPos("Val Min", self.window_name)
        v_max = cv2.getTrackbarPos("Val Max", self.window_name)
        return [h_min, s_min, v_min], [h_max, s_max, v_max]

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        return {}

    def _save_config(self):
        lower, upper = self._get_trackbar_values()
        # 覆蓋原本的設定，清除舊的上下限
        self.hsv_ranges[self.color_name] = [lower, upper]
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.hsv_ranges, f, indent=4)
        print(f"[{self.color_name}] HSV Range saved.")

    def _switch_color(self):
        self.current_color_index = (self.current_color_index + 1) % len(self.color_options)
        self.color_name = self.color_options[self.current_color_index]
        print(f"Switched to color: {self.color_name}")

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower, upper = self._get_trackbar_values()
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            result = cv2.bitwise_and(frame, frame, mask=mask)

            # Resize output for visibility
            vis = np.hstack((frame, result))
            cv2.imshow("Preview", vis)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                self._save_config()
            elif key == ord('q'):
                break
            elif key == ord('r'):
                self.color_name = "Red"
                print("Switched to Red")
            elif key == ord('b'):
                self.color_name = "Blue"
                print("Switched to Blue")

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    adjuster = HSVAdjuster()
    adjuster.run()
