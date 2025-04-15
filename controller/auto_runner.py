import time
import cv2
import numpy as np
from core.hsv_filter import apply_hsv_filter
from core.object_detector import detect_valid_contours
from core.json_storage import load_all_colors
from core.serial_sender import SerialSender


class AutoRunner:
    def __init__(self, serial_port="COM3"):
        self.sender = SerialSender(serial_port)
        self.last_sent_time = 0
        self.send_interval = 2  # 秒
        self.enabled = False

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def process_frame(self, frame_bgr):
        if not self.enabled:
            return frame_bgr

        color_db = load_all_colors("color_db.json")
        display = frame_bgr.copy()

        for name, hsv in color_db.items():
            mask = apply_hsv_filter(frame_bgr, hsv)
            contours = detect_valid_contours(mask)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)

                if time.time() - self.last_sent_time > self.send_interval:
                    code = name[0].lower()
                    self.sender.send_code(code)
                    self.last_sent_time = time.time()
                    break  # 傳送一筆就跳出

        return display

    def close(self):
        self.sender.close()
