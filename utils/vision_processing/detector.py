# utils/vision_processing/detector.py

import cv2
import numpy as np
from .config import action_map, load_color_ranges 
from .feature_validator import validate_shape 
from .confidence_scorer import compute_confidence

def detect_target(frame, color_ranges_to_use, show_debug_windows=False):
    # Directly convert frame to HSV without Gaussian Blur
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Initialize kernel for morphological operations
    kernel = np.ones((2, 2), np.uint8)  # Reduced kernel size

    result_frame = frame.copy()
    mask_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
    detected_labels = []

    for color_name, (lower, upper) in color_ranges_to_use.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv, lower_np, upper_np)

        # Apply morphological operations with reduced intensity
        mask = cv2.dilate(mask, kernel, iterations=1)  # Reduced iterations
        mask = cv2.erode(mask, kernel, iterations=1)  # Reduced iterations

        mask_total = cv2.bitwise_or(mask_total, mask)

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
                        cv2.putText(result_frame,
                            f"{color_name}-{shape} ({score:.2f})",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (255, 255, 255), 2)

    return result_frame, detected_labels, mask_total
