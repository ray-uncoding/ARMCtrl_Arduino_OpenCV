# utils/app_core.py

import cv2
import argparse
import socket
import os
# Ensure relative import is correct
from .arm_controller.pi_gpio_controller import PiGPIOController, RPI_GPIO_AVAILABLE 
# Updated import path for vision_processing
from .vision_processing import detect_target, StateManager, config as vision_config # Import config

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
        inverse_logic=args.arm_inverse_logic
    )
    print(f"[Core] Arm controller initialized with GPIO pins: Relays {args.relay_pins}, LED {args.led_pin}. Inverse Logic: {args.arm_inverse_logic}")
    return arm_controller

def process_frame_and_control_arm(frame, state_manager, arm_controller, current_color_ranges, show_debug_windows=False):
    """Processes a single frame for target detection and controls the arm."""
    # Pass current_color_ranges to detect_target
    result_frame, labels, mask = detect_target(frame.copy(), current_color_ranges, show_debug_windows=show_debug_windows)

    # Example: Control arm based on the first detected label's state
    # This logic needs to be refined based on actual requirements
    if labels:
        # This is a placeholder. You'll need to decide how to map labels to arm actions.
        # For example, if a "red" object is detected, move arm to position 1.
        # The current `labels` list contains color names.
        # The `state_manager` can be used to avoid rapid/repeated actions.
        
        # Example: if arm_controller is not None and RPI_GPIO_AVAILABLE:
        # first_label = labels[0] # Get the first detected color
        # if first_label == "red":
        # if state_manager.can_perform_action("move_to_red_pos", cooldown_seconds=2):
        # print(f"[Core] Detected {first_label}, triggering action.")
        # arm_controller.move_to_position_by_name("pickup") # Example action
        # pass
        pass # Implement arm control logic here

    return result_frame, labels, mask # Return mask as well for potential future use

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
