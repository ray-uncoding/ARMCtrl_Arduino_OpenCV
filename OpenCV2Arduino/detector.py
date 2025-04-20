# detector.py

import cv2
import numpy as np
from .config import color_ranges, action_map
from .feature_validator import validate_shape 
from .confidence_scorer import compute_confidence

def detect_target(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    result_frame = frame.copy()
    mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
    detected_labels = []

    for color_name, (lower, upper) in color_ranges.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv, lower_np, upper_np)
        mask_total = cv2.bitwise_or(mask_total, mask)

        # 🧪 可視化各個遮罩
        cv2.imshow(f"{color_name} Mask", mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
            x, y, w, h = cv2.boundingRect(approx)

            shape = None
            if len(approx) == 3:
                shape = "Triangle"
            elif len(approx) == 4:
                shape = "Square"

            if shape and validate_shape(cnt, approx, shape):
                score = compute_confidence(cnt, approx, mask, shape)
                #print(f"[Debug] {color_name}-{shape} score: {score:.2f}")

                if score >= 0.7:  # 🟡 門檻可調
                    label = action_map.get((color_name, shape), None)
                    if label:
                        detected_labels.append(label)
                        # ✅ 顯示偵測框
                        cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(result_frame,
                            f"{color_name}-{shape} ({score:.2f})",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (255, 255, 255), 2)

    return result_frame, detected_labels, mask_total