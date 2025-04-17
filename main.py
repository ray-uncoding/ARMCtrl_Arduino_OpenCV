# main.py
import cv2
from detector import detect_target
from signal_sender import SignalSender
from ui_basic import AppUI

COM_PORT = 'COM5'
BAUD_RATE = 9600

def main():
    cap = cv2.VideoCapture(0)
    sender = SignalSender(port=COM_PORT, baudrate=BAUD_RATE)
    ui = AppUI()

    last_action = None

    if not cap.isOpened():
        print("[Main] Camera not accessible.")
        return

    print("[Main] System running. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result_frame, label = detect_target(frame)
        ui.update(frame, result_frame, label)

        # --- 阻回與傳送 ---
        if label and label != last_action:
            print(f"[Main] 傳送指令: {label}")
            sender.send_async(label)
            last_action = label
        # 如果沒有偵測到任何東西，也可考慮清除 last_action
        elif not label:
            last_action = None

        if ui.should_quit():
            break

    cap.release()
    cv2.destroyAllWindows()
    sender.close()
    print("[Main] System exited.")

if __name__ == '__main__':
    main()
