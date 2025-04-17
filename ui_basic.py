# ui_basic.py

import cv2

class AppUI:
    def __init__(self):
        self.quit = False
        self.last_label = None

    def update(self, original_frame, result_frame, label=None):
        if label:
            self.last_label = label
            cv2.putText(result_frame, f"Detected: {label}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # 組合畫面（左右顯示）
        combined = cv2.hconcat([original_frame, result_frame])
        cv2.imshow("ARMCtrl Demo", combined)

        # 偵測退出鍵
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.quit = True

    def should_quit(self):
        return self.quit
