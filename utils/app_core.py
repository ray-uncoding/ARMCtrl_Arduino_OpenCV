# utils/app_core.py

import cv2
import argparse
import socket
import os
# Ensure relative import is correct
from .arm_controller.pi_gpio_controller import PiGPIOController, RPI_GPIO_AVAILABLE 
# Updated import path for vision_processing
from .vision_processing import detect_target, config as vision_config # Import config
from .vision_processing.state_manager import StateManager

# --- Default GPIO Pin configurations (BCM Mode) ---
DEFAULT_RELAY_PINS = [17, 27, 22, 23]
DEFAULT_LED_PIN = 18
DEFAULT_INVERSE_LOGIC = True
# ---

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"

def add_common_arguments(parser):
    """Adds common command-line arguments to the parser."""
    parser.add_argument(
        '--camera_index',
        type=str, 
        default='0',
        help="Camera index (e.g., 0, 1) or URL for IP camera."
    )
    parser.add_argument(
        '--relay_pins',
        type=int,
        nargs=4,
        default=DEFAULT_RELAY_PINS,
        help=f"BCM GPIO pins for the 4 relays (default: {DEFAULT_RELAY_PINS})"
    )
    parser.add_argument(
        '--led_pin',
        type=int,
        default=DEFAULT_LED_PIN,
        help=f"BCM GPIO pin for the test LED (default: {DEFAULT_LED_PIN})"
    )
    parser.add_argument(
        '--arm_inverse_logic',
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_INVERSE_LOGIC,
        help="Set if arm relays are inverse logic (LOW active)"
    )
    parser.add_argument(
        '--ready_pin',
        type=int,
        default=26,
        help="GPIO pin for ready signal (default: 26)"
    )
    return parser

def initialize_camera(cap_source_str):
    """Initializes the camera and returns the capture object and properties."""
    if isinstance(cap_source_str, str) and (cap_source_str.startswith("http://") or cap_source_str.startswith("rtsp://")):
        print(f"[Core] Using IP camera: {cap_source_str}")
        cap_source = cap_source_str
    else:
        try:
            cap_source = int(cap_source_str)
            print(f"[Core] Using camera index: {cap_source}")
        except ValueError:
            print(f"[Core] Error: Invalid camera_index format: {cap_source_str}. Please use an integer or a valid URL.")
            return None, None, None, None
            
    cap = cv2.VideoCapture(cap_source)
    
    if not cap.isOpened():
        print(f"[Core] Camera not accessible at source: {cap_source_str}.")
        return None, None, None, None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    raw_fps = cap.get(cv2.CAP_PROP_FPS)
    fps = int(raw_fps if raw_fps and 5 <= raw_fps <= 120 else 30)  # Default to 30 FPS if invalid

    print(f"[Core] Camera initialized: {frame_width}x{frame_height} at {fps} FPS.")
    return cap, frame_width, frame_height, fps

def initialize_arm_controller(args):
    """Initializes and returns the arm controller based on parsed arguments."""
    if not RPI_GPIO_AVAILABLE:
        print("[Core] WARNING: RPi.GPIO library not found or not running on a Raspberry Pi. Arm control will be simulated.")
        # Optionally, return a mock/dummy controller if you have one for testing
        # For now, we'll let PiGPIOController handle its internal simulation mode if GPIO is not available
    
    # relay_pins and led_pin are already lists/int from argparse
    arm_controller = PiGPIOController(
        relay_pins=args.relay_pins, 
        led_pin=args.led_pin, 
        inverse_logic=args.arm_inverse_logic,
        ready_pin=getattr(args, "ready_pin", 26)  # 預設 26
    )
    print(f"[Core] Arm controller initialized with GPIO pins: Relays {args.relay_pins}, LED {args.led_pin}. Inverse Logic: {args.arm_inverse_logic}")
    return arm_controller

def process_frame_and_control_arm(frame, state_manager, arm_controller, current_color_ranges, show_debug_windows=False):
    """Processes a single frame for target detection and controls the arm."""
    # detect_target now returns labels like ['A', 'B'] based on color+shape and action_map
    result_frame, detected_actions, mask = detect_target(frame.copy(), current_color_ranges, show_debug_windows=show_debug_windows)

    if detected_actions and arm_controller: # Ensure arm_controller is not None and actions were detected
        # Process the first detected action
        # In a real scenario, you might need a more sophisticated way to prioritize if multiple actions are detected
        first_action_label = detected_actions[0] # e.g., 'A', 'B', 'C', or 'D'

        action_to_perform_method = None
        action_name_for_state_manager = None

        if first_action_label == 'A':
            action_to_perform_method = arm_controller.trigger_action_A
            action_name_for_state_manager = "action_A"
        elif first_action_label == 'B':
            action_to_perform_method = arm_controller.trigger_action_B
            action_name_for_state_manager = "action_B"
        elif first_action_label == 'C':
            action_to_perform_method = arm_controller.trigger_action_C
            action_name_for_state_manager = "action_C"
        elif first_action_label == 'D':
            action_to_perform_method = arm_controller.trigger_action_D
            action_name_for_state_manager = "action_D"
        elif first_action_label == 'E':
            action_to_perform_method = arm_controller.trigger_action_E
            action_name_for_state_manager = "action_E"
        elif first_action_label == 'F':
            action_to_perform_method = arm_controller.trigger_action_F
            action_name_for_state_manager = "action_F"

        if action_to_perform_method and action_name_for_state_manager:
            if state_manager.can_perform_action(action_name_for_state_manager, cooldown_seconds=7):
                print(f"[Core] Detected action '{first_action_label}', triggering {action_name_for_state_manager}.")
                action_to_perform_method() # Execute the arm action method
                state_manager.reset_action_cooldown(action_name_for_state_manager)  # Ensure cooldown is reset after action
            else:
                print(f"[Core] Detected action '{first_action_label}', but {action_name_for_state_manager} is on cooldown.")
                action_to_perform_method = None  # Ensure no action is performed during cooldown
        elif detected_actions: # An action label was detected but not mapped to a method
            print(f"[Core] Detected action label '{first_action_label}' has no defined arm trigger method.")

    return result_frame, detected_actions, mask # Return detected_actions (e.g. ['A', 'B']) instead of raw color labels

def cleanup_resources(cap, arm_controller):
    """Releases camera and cleans up GPIO resources."""
    if cap:
        print("[Core] Releasing camera...")
        cap.release()
        print("[Core] Camera released.")
    if arm_controller:
        print("[Core] Cleaning up arm controller (GPIO)...")
        arm_controller.cleanup()
        print("[Core] Arm controller GPIO cleaned up.")
    cv2.destroyAllWindows() # Ensure all OpenCV windows are closed
    print("[Core] All OpenCV windows destroyed.")
    print("[Core] Resources cleaned up.")

# --- StateManager (already defined in vision_processing, re-exporting or using from there) ---
# Using StateManager from vision_processing to avoid duplication
# from .vision_processing import StateManager 
# No, StateManager is imported at the top from .vision_processing
