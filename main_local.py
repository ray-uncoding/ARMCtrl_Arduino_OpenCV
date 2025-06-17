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
# Global variable to store currently selected color for adjustment
current_color_to_adjust = "Red" # Default to Red

def on_trackbar_change(x):
    # This function is called when a trackbar value changes.
    # We don't need to do anything here as values are read directly in the loop.
    pass

def setup_trackbars(initial_hsv_values):
    cv2.namedWindow(TRACKBAR_WINDOW_NAME)
    cv2.resizeWindow(TRACKBAR_WINDOW_NAME, 400, 300) # Optional: resize for better layout

    # Create trackbars for HSV values
    # Initial values are set based on the loaded config for the current_color_to_adjust
    cv2.createTrackbar("H_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][0], 179, on_trackbar_change)
    cv2.createTrackbar("S_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][1], 255, on_trackbar_change)
    cv2.createTrackbar("V_min", TRACKBAR_WINDOW_NAME, initial_hsv_values[0][2], 255, on_trackbar_change)
    cv2.createTrackbar("H_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][0], 179, on_trackbar_change)
    cv2.createTrackbar("S_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][1], 255, on_trackbar_change)
    cv2.createTrackbar("V_max", TRACKBAR_WINDOW_NAME, initial_hsv_values[1][2], 255, on_trackbar_change)

def get_trackbar_hsv_values():
    h_min = cv2.getTrackbarPos("H_min", TRACKBAR_WINDOW_NAME)
    s_min = cv2.getTrackbarPos("S_min", TRACKBAR_WINDOW_NAME)
    v_min = cv2.getTrackbarPos("V_min", TRACKBAR_WINDOW_NAME)
    h_max = cv2.getTrackbarPos("H_max", TRACKBAR_WINDOW_NAME)
    s_max = cv2.getTrackbarPos("S_max", TRACKBAR_WINDOW_NAME)
    v_max = cv2.getTrackbarPos("V_max", TRACKBAR_WINDOW_NAME)
    return [[h_min, s_min, v_min], [h_max, s_max, v_max]]

def main():
    global current_color_to_adjust # Allow modification of global variable

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
    ui = AppUI() 

    # Load initial color ranges from config
    # Make a deep copy to allow live modification without altering the loaded config directly
    # until save is explicitly called.
    live_color_ranges = deepcopy(vision_config.color_ranges)

    if not live_color_ranges or current_color_to_adjust not in live_color_ranges:
        print(f"[MainLocal] Warning: Color '{current_color_to_adjust}' not found in config or config is empty. Using default HSV values for trackbars.")
        # Provide some default values if config is missing or color is not found
        initial_hsv_for_trackbar = [[0, 100, 100], [10, 255, 255]] 
    else:
        initial_hsv_for_trackbar = live_color_ranges[current_color_to_adjust]
    
    setup_trackbars(initial_hsv_for_trackbar)

    print(f"[MainLocal] System running in LOCAL display mode. Press 'q' in the OpenCV window to quit.")
    print(f"[MainLocal] HSV Adjustment: Press 'r' for Red, 'b' for Blue. Press 's' to save current color's HSV to config.")
    print(f"[MainLocal] Currently adjusting: {current_color_to_adjust}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[MainLocal] Error: Can't receive frame (stream end or camera error?). Exiting ...")
                break

            # Update live_color_ranges for the current_color_to_adjust from trackbars
            if current_color_to_adjust in live_color_ranges:
                live_color_ranges[current_color_to_adjust] = get_trackbar_hsv_values()
            else: # If the color was not in the initial config, add it
                live_color_ranges[current_color_to_adjust] = get_trackbar_hsv_values()


            # Process frame, detect targets, and control arm using live_color_ranges
            result_frame, labels, mask, stable_label = process_frame_and_control_arm(
                frame, state_manager, arm_controller, live_color_ranges, # Pass live ranges
                show_debug_windows=args.show_debug_masks
            )
            
            # Update UI
            # Display the name of the color being adjusted on the result_frame
            cv2.putText(result_frame, f"Adjusting: {current_color_to_adjust}", (10, frame_height - 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(result_frame, f"Press 's' to save {current_color_to_adjust}", (10, frame_height - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            ui.update(frame, result_frame, mask, labels) 
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("[MainLocal] Quit signal from UI.")
                break
            elif key == ord('s'):
                # Save the live_color_ranges (which contains the current trackbar values for the selected color)
                vision_config.save_color_ranges(live_color_ranges)
                print(f"[MainLocal] Saved current HSV values for {current_color_to_adjust} to config.")
                # Optionally, reload and re-setup trackbars if save_color_ranges modifies the structure
                # For now, assume live_color_ranges is the source of truth after saving.
            elif key == ord('r'):
                current_color_to_adjust = "Red"
                print(f"[MainLocal] Switched to adjusting: {current_color_to_adjust}")
                if current_color_to_adjust in live_color_ranges:
                    setup_trackbars(live_color_ranges[current_color_to_adjust])
                else: # If Red is not in config, use defaults
                    setup_trackbars([[0,100,100],[10,255,255]])
            elif key == ord('b'):
                current_color_to_adjust = "Blue"
                print(f"[MainLocal] Switched to adjusting: {current_color_to_adjust}")
                if current_color_to_adjust in live_color_ranges:
                    setup_trackbars(live_color_ranges[current_color_to_adjust])
                else: # If Blue is not in config, use defaults
                    setup_trackbars([[100,100,100],[120,255,255]])


    except KeyboardInterrupt:
        print("\\n[MainLocal] Program interrupted by user (Ctrl+C).")
    finally:
        print("[MainLocal] Cleaning up resources...")
        cleanup_resources(cap, arm_controller)
        cv2.destroyAllWindows()
        print("[MainLocal] OpenCV windows destroyed.")
        print("[MainLocal] Cleanup finished.")

if __name__ == "__main__":
    main()
