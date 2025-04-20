# ui_basic.py

import cv2

class AppUI:
    def __init__(self, window_name="ARMCtrl Demo"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def update(self, original_frame, annotated_frame, mask_frame, label=None):
        # Resize 所有畫面統一大小
        left = cv2.resize(annotated_frame, (640, 480))
        right_mask = cv2.resize(mask_frame, (640, 480))
        right = cv2.cvtColor(right_mask, cv2.COLOR_GRAY2BGR)  # 將 mask 灰階圖轉為彩色三通道

        # 顯示 label（若有）
        if label:
            cv2.putText(left, f"Detected: {label}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)

        # 顯示主畫面（左：原圖 + 框 右：遮罩結果）
        merged = cv2.hconcat([left, right])
        cv2.imshow(self.window_name, merged)

        # 額外顯示紅藍遮罩畫面
        if cv2.getWindowProperty("Red Mask", 0) >= 0:
            pass  # 已存在，不需再建立
        else:
            cv2.namedWindow("Red Mask")
            cv2.moveWindow("Red Mask", 0, 520)

        if cv2.getWindowProperty("Blue Mask", 0) >= 0:
            pass
        else:
            cv2.namedWindow("Blue Mask")
            cv2.moveWindow("Blue Mask", 650, 520)

        if label:
            if isinstance(label, list):
                text = f"Detected: {label}"  # 多個 label
            else:
                text = f"Detected: {label}"
            cv2.putText(left, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)

        # 合併畫面（左：原圖 + 框，右：過濾結果）
        merged = cv2.hconcat([left, right])
        cv2.imshow(self.window_name, merged)

    def should_quit(self):
        return cv2.waitKey(1) & 0xFF == ord('q')
