# utils/vision_processing/config.py

import json
from pathlib import Path

# Path to the configuration file
# RENAME CONFIG_FILE_PATH to COLOR_CONFIG_PATH for consistency with main_stream.py import
COLOR_CONFIG_PATH = Path(__file__).parent / "color_config.json"

# Global variable to hold color ranges, initialized by load_color_ranges
color_ranges = {}

# color + shape -> corresponding control command
action_map = {
    ('Red', 'Triangle'): 'A',
    ('Red', 'Square'): 'B',
    ('Blue', 'Triangle'): 'C',
    ('Blue', 'Square'): 'D',
}

def load_color_ranges():
    """Loads color ranges from the JSON configuration file."""
    global color_ranges
    if COLOR_CONFIG_PATH.exists(): # Use the renamed variable
        try:
            with open(COLOR_CONFIG_PATH, "r", encoding="utf-8") as f: # Use the renamed variable
                color_ranges = json.load(f)
            print(f"[Config] Color ranges loaded from {COLOR_CONFIG_PATH}") # Use the renamed variable
        except json.JSONDecodeError as e:
            print(f"[Config] Error decoding JSON from {COLOR_CONFIG_PATH}: {e}") # Use the renamed variable
            # Initialize with empty or default if file is corrupt
            color_ranges = {}
        except Exception as e:
            print(f"[Config] Error loading {COLOR_CONFIG_PATH}: {e}") # Use the renamed variable
            color_ranges = {}
    else:
        print(f"[Config] Warning: Configuration file {COLOR_CONFIG_PATH} not found. Initializing empty color ranges.") # Use the renamed variable
        color_ranges = {}
    return color_ranges

def save_color_ranges(new_ranges):
    """Saves the given color ranges to the JSON configuration file."""
    global color_ranges
    try:
        with open(COLOR_CONFIG_PATH, "w", encoding="utf-8") as f: # Use the renamed variable
            json.dump(new_ranges, f, indent=4)
        color_ranges = new_ranges # Update the global variable as well
        print(f"[Config] Color ranges saved to {COLOR_CONFIG_PATH}") # Use the renamed variable
    except Exception as e:
        print(f"[Config] Error saving color ranges to {COLOR_CONFIG_PATH}: {e}") # Use the renamed variable
# Initialize color_ranges when the module is imported
load_color_ranges()
