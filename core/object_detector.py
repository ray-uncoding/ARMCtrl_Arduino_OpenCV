import cv2


def detect_valid_contours(mask, area_threshold=3000):
    """
    在二值化影像中尋找輪廓，
    回傳符合面積與形狀條件的輪廓清單（近似方形）。
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < area_threshold:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            valid_contours.append(cnt)

    return valid_contours