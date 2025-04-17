# detector.py

import cv2
import numpy as np
from config import color_ranges, action_map

def detect_target(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    result_frame = frame.copy()
    label = None

    for color_name, (lower, upper) in color_ranges.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv, lower_np, upper_np)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:
                continue

            approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            shape = None

            if len(approx) == 3:
                shape = "Triangle"
            elif len(approx) == 4:
                shape = "Square"

            if shape:
                action_key = (color_name, shape)
                if action_key in action_map:
                    label = action_map[action_key]
                    cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(result_frame, f"{color_name}-{shape}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    return result_frame, label  # 找到一個就回傳

    return result_frame, None
