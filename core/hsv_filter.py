import cv2
import numpy as np


def apply_hsv_filter(frame_bgr, hsv_ranges):
    """
    將 BGR 影像轉為 HSV，根據範圍做 inRange 篩選，回傳二值化 mask。
    hsv_ranges 應為 dict：{"H": [low, high], "S": [...], "V": [...]}。
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    lower_bound = np.array([
        hsv_ranges["H"][0],
        hsv_ranges["S"][0],
        hsv_ranges["V"][0]
    ])
    upper_bound = np.array([
        hsv_ranges["H"][1],
        hsv_ranges["S"][1],
        hsv_ranges["V"][1]
    ])

    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    return mask
