# confidence_scorer.py

import cv2

def compute_confidence(cnt, approx, hsv_mask, shape):
    area = cv2.contourArea(cnt)
    if area < 1000:
        return 0.0

    x, y, w, h = cv2.boundingRect(approx)
    aspect_ratio = w / h if h != 0 else 0

    # 形狀得分
    if shape == "Square":
        shape_score = max(0.0, 1 - abs(1 - aspect_ratio))  # 越接近 1 越高
    elif shape == "Triangle":
        shape_score = 1.0 if len(approx) == 3 else 0.5
    else:
        shape_score = 0.3

    # 遮罩密度得分
    mask_crop = hsv_mask[y:y+h, x:x+w]
    mask_area = cv2.countNonZero(mask_crop)
    density_score = mask_area / (w * h + 1)

    # 總分數（你可以調整權重）
    total_score = 0.6 * shape_score + 0.4 * density_score
    return total_score
