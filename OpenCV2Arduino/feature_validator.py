# feature_validator.py

import cv2

def validate_shape(cnt, approx, shape_name):
    area = cv2.contourArea(cnt)
    if area < 1000:
        return False

    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = w / h

    if shape_name == "Square":
        if aspect_ratio < 0.8 or aspect_ratio > 1.2:
            return False

    if shape_name == "Triangle":
        if len(approx) != 3:
            return False
        if area < 1500:  # 更嚴格過濾小三角形
            return False

    return True
