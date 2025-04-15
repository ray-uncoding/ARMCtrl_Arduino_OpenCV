import cv2
import numpy as np

def detect_shape(mask):
    """
    輸入 mask（單通道二值圖），回傳 (True, 'square') 或 (True, 'triangle') 或 (False, '')
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 1000:  # 忽略太小的雜訊
            continue

        approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
        vertices = len(approx)

        if vertices == 3:
            return True, "triangle"
        elif vertices == 4:
            return True, "square"

    return False, ""
