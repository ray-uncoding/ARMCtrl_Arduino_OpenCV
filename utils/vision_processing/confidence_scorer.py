# utils/vision_processing/confidence_scorer.py

import cv2

def compute_confidence(cnt, approx, hsv_mask, shape):
    area = cv2.contourArea(cnt)
    if area < 1000:
        return 0.0

    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = w / h if h != 0 else 0

    # Shape score
    if shape == "Square":
        shape_score = max(0.0, 1 - abs(1 - aspect_ratio))  # Closer to 1 is higher
    elif shape == "Triangle":
        shape_score = 1.0 if len(approx) == 3 else 0.5
    else:
        shape_score = 0.3

    # Mask density score
    mask_crop = hsv_mask[y:y+h, x:x+w]
    mask_area = cv2.countNonZero(mask_crop)
    density_score = mask_area / (w * h + 1)

    # Total score (you can adjust weights)
    total_score = 0.6 * shape_score + 0.4 * density_score
    return total_score
