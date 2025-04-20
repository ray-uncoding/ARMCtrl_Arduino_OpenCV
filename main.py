# main.py
import cv2
from OpenCV2Arduino import detect_target, SignalSender, AppUI, StateManager

COM_PORT = 'COM5'
BAUD_RATE = 9600


def main():
    cap = cv2.VideoCapture(1)
    sender = SignalSender(port=COM_PORT, baudrate=BAUD_RATE)
    ui = AppUI()

    last_action = None

    if not cap.isOpened():
        print("[Main] Camera not accessible.")
        return

    print("[Main] System running. Press 'q' to quit.")
    
    state_manager = StateManager()
        
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result_frame, labels, mask = detect_target(frame)
        ui.update(frame, result_frame, mask, labels)

        for label in labels:
            state_manager.update(label)

        # 詢問：現在有穩定結果嗎？
        stable_label = state_manager.get_stable_label()
        if stable_label:
            print(f"[Main] 穩定觸發：{stable_label}")
            sender.send_async(stable_label)

        if ui.should_quit():
            break

    cap.release()
    cv2.destroyAllWindows()
    sender.close()
    print("[Main] System exited.")

if __name__ == '__main__':
    main()
