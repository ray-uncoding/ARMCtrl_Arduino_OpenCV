# utils/vision_processing/detector.py

import cv2
import numpy as np
from .config import action_map, load_color_ranges 
from .feature_validator import validate_shape 
from .confidence_scorer import compute_confidence
from utils.vision_processing.ui_basic import draw_chinese_text

shape_ch_map = {"Square": "方形", "Triangle": "三角形"}
color_ch_map = {"Red": "紅色", "Blue": "藍色", "Green": "綠色"}

def detect_target(frame, color_ranges_to_use, show_debug_windows=False):
    # Convert frame to HSV and apply Gaussian Blur
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = cv2.GaussianBlur(hsv, (3, 3), 0)  # 只對原圖輕微模糊，防雜訊

    result_frame = frame.copy()
    mask_dict = {}
    detected_labels = []

    for color_name, (lower, upper) in color_ranges_to_use.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv, lower_np, upper_np)

        # 只做一次小kernel膨脹/腐蝕，保持稜角
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        mask = cv2.erode(mask, kernel, iterations=1)

        # 連通元件分析，去除小雜點（保留大於min_area的區塊）
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        min_area = 300  # 根據實際情況調整
        cleaned_mask = np.zeros_like(mask)
        for i in range(1, num_labels):  # 0是背景
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                cleaned_mask[labels == i] = 255
        mask = cleaned_mask

        mask_dict[color_name] = mask

        if show_debug_windows:
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

                if score >= 0.7:
                    label = action_map.get((color_name, shape), None)
                    if label:
                        detected_labels.append(label)
                        cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        ch_color = color_ch_map.get(color_name, color_name)
                        ch_shape = shape_ch_map.get(shape, shape)
                        label_text = f"{ch_color}-{ch_shape} ({score:.2f})"
                        # 用 PIL 畫中文字
                        result_frame = draw_chinese_text(
                            result_frame,
                            label_text,
                            (x, y - 10),
                            font_size=28,
                            color=(255,255,255),
                            font_path="chinese.ttf"
                        )

    return result_frame, detected_labels, mask_dict  # 回傳 dict
