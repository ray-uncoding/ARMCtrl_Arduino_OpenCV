# main_local.py
import cv2
import argparse
import numpy as np # Added for numpy array creation
from copy import deepcopy # Added for deep copying color ranges

# Updated import path for AppUI
from utils.vision_processing.ui_basic import AppUI 
# Ensure other imports from app_core are correct and StateManager is available if needed directly
from utils.app_core import (
    add_common_arguments, 
    initialize_camera, 
    initialize_arm_controller, 
    process_frame_and_control_arm,
    cleanup_resources,
    StateManager 
)
# Import config from vision_processing
from utils.vision_processing import config as vision_config

# Global variable for trackbar window
TRACKBAR_WINDOW_NAME = "HSV Adjustments"
# Global variable for our new controls window
CONTROLS_WINDOW_NAME = "Controls"
# Global variable to store currently selected color for adjustment
current_color_to_adjust = "Red" # Default to Red
# Global variable to store action from button clicks
current_action_from_buttons = None

# Button definitions (coordinates are relative to the CONTROLS_WINDOW_NAME)
BUTTON_HEIGHT = 30
BUTTON_WIDTH = 180
TEXT_COLOR = (255, 255, 255) # White
BUTTON_COLOR = (100, 100, 100) # Grey
QUIT_BUTTON_COLOR = (50, 50, 150) # Darker red for quit
CONTROLS_WINDOW_WIDTH = 220 
CONTROLS_WINDOW_HEIGHT = 250 # Increased height for title and buttons

buttons_config = [
    {"rect": (20, 50, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "Save Settings", "action": "save", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 50 + BUTTON_HEIGHT + 10, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "Tune Red", "action": "set_red", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 50 + 2 * (BUTTON_HEIGHT + 10), BUTTON_WIDTH, BUTTON_HEIGHT), "text": "Tune Blue", "action": "set_blue", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 50 + 3 * (BUTTON_HEIGHT + 10), BUTTON_WIDTH, BUTTON_HEIGHT), "text": "Quit", "action": "quit", "color": QUIT_BUTTON_COLOR, "text_color": TEXT_COLOR},
]

def on_trackbar_change(x):
    # This function is called when a trackbar value changes.
    # We don\'t need to do anything here as values are read directly in the loop.
    pass

def setup_trackbars(initial_hsv_values):
    cv2.namedWindow(TRACKBAR_WINDOW_NAME)
    cv2.resizeWindow(TRACKBAR_WINDOW_NAME, 400, 300) # Keep original size for trackbars

    cv2.createTrackbar("H_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][0], 179, on_trackbar_change)
    cv2.createTrackbar("H_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][0], 179, on_trackbar_change)
    cv2.createTrackbar("S_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][1], 255, on_trackbar_change)
    cv2.createTrackbar("S_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][1], 255, on_trackbar_change)
    cv2.createTrackbar("V_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][2], 255, on_trackbar_change)
    cv2.createTrackbar("V_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][2], 255, on_trackbar_change)

def get_trackbar_hsv_values():
    h_min = cv2.getTrackbarPos("H_min", TRACKBAR_WINDOW_NAME)
    s_min = cv2.getTrackbarPos("S_min", TRACKBAR_WINDOW_NAME)
    v_min = cv2.getTrackbarPos("V_min", TRACKBAR_WINDOW_NAME)
    h_max = cv2.getTrackbarPos("H_max", TRACKBAR_WINDOW_NAME)
    s_max = cv2.getTrackbarPos("S_max", TRACKBAR_WINDOW_NAME)
    v_max = cv2.getTrackbarPos("V_max", TRACKBAR_WINDOW_NAME)
    return [[h_min, s_min, v_min], [h_max, s_max, v_max]]

def draw_buttons_panel():
    global current_color_to_adjust 
    panel_image = np.full((CONTROLS_WINDOW_HEIGHT, CONTROLS_WINDOW_WIDTH, 3), (50, 50, 50), dtype=np.uint8) # Dark gray background

    adjust_text = f"Tuning: {current_color_to_adjust}"
    (w, h), _ = cv2.getTextSize(adjust_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.putText(panel_image, adjust_text, ((CONTROLS_WINDOW_WIDTH - w) // 2, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 100), 2, cv2.LINE_AA) # Light green text, centered

    for button in buttons_config:
        x, y, w, h = button["rect"]
        cv2.rectangle(panel_image, (x, y), (x + w, y + h), button["color"], -1)
        text_size = cv2.getTextSize(button["text"], cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2
        cv2.putText(panel_image, button["text"], (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, button["text_color"], 1, cv2.LINE_AA)
    
    cv2.imshow(CONTROLS_WINDOW_NAME, panel_image)

def on_buttons_panel_mouse_click(event, x, y, flags, param):
    global current_action_from_buttons
    if event == cv2.EVENT_LBUTTONDOWN:
        for button in buttons_config:
            bx, by, bw, bh = button["rect"]
            if bx <= x < bx + bw and by <= y < by + bh:
                current_action_from_buttons = button["action"]
                # print(f"Button clicked: {button['action']}") # For debugging
                break

def main():
    global current_color_to_adjust
    global current_action_from_buttons

    parser = argparse.ArgumentParser(description="ARMCtrl OpenCV Application - Local Display Mode with HSV Adjustment")
    parser = add_common_arguments(parser)
    parser.add_argument(
        '--show_debug_masks',
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show individual color mask windows for debugging."
    )
    args = parser.parse_args()

    cap, frame_width, frame_height, fps = initialize_camera(args.camera_index)
    if not cap:
        return

    arm_controller = initialize_arm_controller(args)
    state_manager = StateManager()
    ui = AppUI() # AppUI is now simplified, only for video display

    live_color_ranges = deepcopy(vision_config.color_ranges)

    if not live_color_ranges or current_color_to_adjust not in live_color_ranges:
        print(f"[MainLocal] Warning: Color '{current_color_to_adjust}' not found in config or config is empty. Using default HSV values.")
        initial_hsv_for_trackbar = vision_config.DEFAULT_COLOR_RANGES.get(current_color_to_adjust, [[0,0,0],[179,255,255]])
    else:
        initial_hsv_for_trackbar = live_color_ranges[current_color_to_adjust]
    
    setup_trackbars(initial_hsv_for_trackbar)

    # Setup controls window
    cv2.namedWindow(CONTROLS_WINDOW_NAME)
    cv2.setMouseCallback(CONTROLS_WINDOW_NAME, on_buttons_panel_mouse_click)
    draw_buttons_panel() # Initial draw of the buttons panel

    print(f"[MainLocal] System running. Use UI buttons or press 'q' in the OpenCV window to quit.")
    print(f"[MainLocal] Currently adjusting: {current_color_to_adjust}")

    print("[MainLocal] Starting main loop...")
    print("[MainLocal] Initializing camera and arm controller...")
    print("[MainLocal] Current color ranges:", live_color_ranges)
    print("[MainLocal] Current color to adjust:", current_color_to_adjust)
    print("[MainLocal] Entering frame processing loop...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[MainLocal] Error: Can't receive frame (stream end or camera error?). Exiting ...")
                break

            # Check if trackbar window is open and update HSV values
            # cv2.getWindowProperty returns -1 if window does not exist or has been destroyed.
            # It returns 0.0 if window exists but is not visible (e.g. minimized, or just created but not shown yet)
            # It returns >= 1.0 if window exists and is visible.
            trackbar_window_exists_and_visible = False
            try:
                if cv2.getWindowProperty(TRACKBAR_WINDOW_NAME, cv2.WND_PROP_VISIBLE) >= 1.0:
                    trackbar_window_exists_and_visible = True
            except cv2.error: # Window does not exist
                pass # trackbar_window_exists_and_visible remains False

            if trackbar_window_exists_and_visible:
                if current_color_to_adjust in live_color_ranges:
                    live_color_ranges[current_color_to_adjust] = get_trackbar_hsv_values()
                else: 
                    live_color_ranges[current_color_to_adjust] = get_trackbar_hsv_values()
            else:
                # Attempt to re-create if it was closed
                print(f"[MainLocal] Trackbar window ('{TRACKBAR_WINDOW_NAME}') is not visible. Attempting to re-create.")
                if current_color_to_adjust in live_color_ranges:
                    setup_trackbars(live_color_ranges[current_color_to_adjust])
                else: 
                     default_hsv = vision_config.DEFAULT_COLOR_RANGES.get(current_color_to_adjust, [[0,100,100],[10,255,255]])
                     setup_trackbars(default_hsv)

            result_frame, labels, mask = process_frame_and_control_arm(
                frame, state_manager, arm_controller, live_color_ranges,
                show_debug_windows=args.show_debug_masks
            )
            
            # Update AppUI (main video display)
            ui.update(frame, result_frame, mask, labels) 
            
            # Handle actions from our new buttons panel
            action = None
            if current_action_from_buttons:
                action = current_action_from_buttons
                current_action_from_buttons = None # Reset action once processed

            # Also check for keyboard 'q' in the main video window as a fallback
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or action == "quit": # Corrected string literal for "quit"
                print("[MainLocal] Quit signal received.")
                break
            elif action == "save":
                vision_config.save_color_ranges(live_color_ranges)
                print(f"[MainLocal] Saved current HSV values for ALL colors to config.")
            elif action == "set_red":
                if current_color_to_adjust != "Red":
                    current_color_to_adjust = "Red"
                    print(f"[MainLocal] Switched to adjusting: {current_color_to_adjust}")
                    try:
                        if cv2.getWindowProperty(TRACKBAR_WINDOW_NAME, cv2.WND_PROP_VISIBLE) >=1:
                            cv2.destroyWindow(TRACKBAR_WINDOW_NAME) 
                    except cv2.error: pass # Window might already be destroyed
                    
                    if current_color_to_adjust in live_color_ranges:
                        setup_trackbars(live_color_ranges[current_color_to_adjust])
                    else: 
                        default_hsv = vision_config.DEFAULT_COLOR_RANGES.get("Red", [[0,100,100],[10,255,255]])
                        setup_trackbars(default_hsv)
                    draw_buttons_panel() # Update "Tuning: Red" text
            elif action == "set_blue":
                if current_color_to_adjust != "Blue":
                    current_color_to_adjust = "Blue"
                    print(f"[MainLocal] Switched to adjusting: {current_color_to_adjust}")
                    try:
                        if cv2.getWindowProperty(TRACKBAR_WINDOW_NAME, cv2.WND_PROP_VISIBLE) >=1:
                            cv2.destroyWindow(TRACKBAR_WINDOW_NAME)
                    except cv2.error: pass # Window might already be destroyed
                    
                    if current_color_to_adjust in live_color_ranges:
                        setup_trackbars(live_color_ranges[current_color_to_adjust])
                    else: 
                        default_hsv = vision_config.DEFAULT_COLOR_RANGES.get("Blue", [[100,100,100],[120,255,255]])
                        setup_trackbars(default_hsv)
                    draw_buttons_panel() # Update "Tuning: Blue" text
            
            # Ensure controls panel is redrawn if closed by user
            controls_window_exists_and_visible = False
            try:
                if cv2.getWindowProperty(CONTROLS_WINDOW_NAME, cv2.WND_PROP_VISIBLE) >= 1.0:
                    controls_window_exists_and_visible = True
            except cv2.error:
                pass
            
            if not controls_window_exists_and_visible:
                print(f"[MainLocal] Controls window ('{CONTROLS_WINDOW_NAME}') is not visible. Attempting to re-create.")
                cv2.namedWindow(CONTROLS_WINDOW_NAME) # Ensure window is created if it was fully destroyed
                draw_buttons_panel()
                cv2.setMouseCallback(CONTROLS_WINDOW_NAME, on_buttons_panel_mouse_click) # Re-apply callback

    except KeyboardInterrupt:
        print("\n[MainLocal] Program interrupted by user (Ctrl+C).")
    finally:
        print("[MainLocal] Cleaning up resources...")
        cleanup_resources(cap, arm_controller) # For camera and arm
        ui.destroy_windows() # For the main ARMCtrl Demo window
        
        # Explicitly destroy trackbar and controls windows if they exist
        # Using a helper function to avoid code duplication
        def safe_destroy_window(window_name):
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 0: # Check if window exists (visible or not)
                    cv2.destroyWindow(window_name)
                    print(f"[MainLocal] Window '{window_name}' destroyed.")
            except cv2.error: # Catch error if window doesn't exist at all
                print(f"[MainLocal] Window '{window_name}' was already closed or never created.")

        safe_destroy_window(TRACKBAR_WINDOW_NAME)
        safe_destroy_window(CONTROLS_WINDOW_NAME)
        
        print("[MainLocal] Cleanup finished.")

if __name__ == "__main__":
    main()
