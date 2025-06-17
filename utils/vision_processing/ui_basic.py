# utils/vision_processing/ui_basic.py

import cv2

class AppUI:
    def __init__(self, window_name="ARMCtrl Demo"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def update(self, original_frame, annotated_frame, mask_frame, label=None):
        # Resize all frames to a uniform size
        left = cv2.resize(annotated_frame, (640, 480))
        right_mask = cv2.resize(mask_frame, (640, 480))
        # Convert mask grayscale image to three-channel color
        right = cv2.cvtColor(right_mask, cv2.COLOR_GRAY2BGR)  

        # Display label (if any)
        display_text = ""
        if label:
            if isinstance(label, list):
                display_text = f"Detected: {', '.join(label)}"
            else:
                display_text = f"Detected: {label}"
            cv2.putText(left, display_text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

        # Display main window (left: annotated_frame, right: mask result)
        merged = cv2.hconcat([left, right])
        cv2.imshow(self.window_name, merged)

    def destroy_windows(self):
        # Destroy only the window managed by this UI class
        if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow(self.window_name)
            print(f"[AppUI] Window '{self.window_name}' destroyed.")
