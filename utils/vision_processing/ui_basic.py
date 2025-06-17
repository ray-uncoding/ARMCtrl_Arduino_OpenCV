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
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)

        # Display main window (left: original + box, right: mask result)
        merged = cv2.hconcat([left, right])
        cv2.imshow(self.window_name, merged)

        # Optionally display individual color masks if windows are open
        # This part seems to attempt to create windows if they don't exist,
        # but doesn't actually display the specific masks (e.g., red_mask_frame, blue_mask_frame)
        # For simplicity, I'm commenting out the dynamic window creation here.
        # If needed, specific mask display logic should be tied to detect_target or main loop.
        # if cv2.getWindowProperty("Red Mask", cv2.WND_PROP_VISIBLE) >= 1:
        #     pass 
        # if cv2.getWindowProperty("Blue Mask", cv2.WND_PROP_VISIBLE) >= 1:
        #     pass

    def should_quit(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return True
        # Potentially add other key handlers here if needed
        return False

    def destroy_windows(self):
        cv2.destroyAllWindows()
        print("[AppUI] All OpenCV windows destroyed.")
