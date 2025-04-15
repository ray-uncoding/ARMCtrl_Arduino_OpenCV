import cv2
from controller.signal_mapper import get_all_slots, get_signal_code
from core.hsv_filter import apply_hsv_filter
from core.object_detector import detect_shape
from core.serial_sender import send_signal

class AutoRunner:
    def __init__(self):
        self.enabled = False
        self.last_sent = None

    def set_enabled(self, flag):
        self.enabled = flag
        self.last_sent = None  # 切換模式時重設

    def process_frame(self, bgr_img):
        if not self.enabled:
            return bgr_img

        slots = get_all_slots()
        for code in sorted(slots.keys()):
            conf = slots[code]
            hsv_range = conf.get("hsv", {})
            label = conf.get("label", "")
            shape = conf.get("shape", "")

            # 基本檢查
            if not label or not shape or not hsv_range:
                continue

            mask = apply_hsv_filter(bgr_img, hsv_range)
            found, detected_shape = detect_shape(mask)

            if found and detected_shape == shape:
                if self.last_sent != code:
                    send_signal(code)
                    print(f"🔁 傳送訊號：{code} (對應 {label} + {shape})")
                    self.last_sent = code
                break

        return bgr_img  # 若要顯示處理畫面，也可改為 return mask 或加框畫面

    def close(self):
        pass  # 若日後要釋放 serial 可放在此
