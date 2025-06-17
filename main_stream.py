# main_stream.py
import argparse
import time
import subprocess
import os

from utils.stream_pusher.rtsp_pusher import RTSPPusher
from utils.app_core import (
    add_common_arguments,
    initialize_camera,
    initialize_arm_controller,
    process_frame_and_control_arm,
    cleanup_resources as app_core_cleanup, # Renamed to avoid conflict
    get_local_ip,
    StateManager
)
from utils.vision_processing.config import load_color_ranges, COLOR_CONFIG_PATH # Added import

# --- Path to mediamtx and its config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIAMTX_BIN_DEFAULT = os.path.join(BASE_DIR, "utils", "bin", "mediamtx")
MEDIAMTX_CONFIG_DEFAULT = os.path.join(BASE_DIR, "utils", "stream_pusher", "mediamtx.yml")

class StreamApplication:
    def __init__(self, args):
        self.args = args
        self.cap = None
        self.frame_width = None
        self.frame_height = None
        self.fps = None
        self.arm_controller = None
        self.state_manager = None
        self.pusher = None
        self.mediamtx_process = None
        
        self.mediamtx_bin = MEDIAMTX_BIN_DEFAULT
        self.mediamtx_config = MEDIAMTX_CONFIG_DEFAULT

        self.current_color_ranges = {}
        self.last_config_mod_time = 0
        self._load_initial_color_config()

        self._initialize_components()

    def _load_initial_color_config(self):
        """Loads the initial color configuration."""
        print(f"[StreamApp] Loading initial color configuration from {COLOR_CONFIG_PATH}...")
        self.current_color_ranges = load_color_ranges()
        if not self.current_color_ranges:
            print("[StreamApp] Warning: No color ranges loaded. Detection might not work as expected.")
        else:
            print(f"[StreamApp] Initial color ranges loaded: {list(self.current_color_ranges.keys())}")
        
        try:
            if os.path.exists(COLOR_CONFIG_PATH):
                self.last_config_mod_time = os.path.getmtime(COLOR_CONFIG_PATH)
            else:
                print(f"[StreamApp] Color config file {COLOR_CONFIG_PATH} not found during initial load for mod time.")
                self.last_config_mod_time = 0
        except OSError as e:
            print(f"[StreamApp] Error getting modification time for {COLOR_CONFIG_PATH}: {e}")
            self.last_config_mod_time = 0


    def _check_and_reload_color_config(self):
        """Checks if the color config file has been modified and reloads it if necessary."""
        try:
            if not os.path.exists(COLOR_CONFIG_PATH):
                # If file was deleted after initial load
                if self.current_color_ranges: # Only clear if it previously had content
                    print(f"[StreamApp] Color config file {COLOR_CONFIG_PATH} deleted. Clearing current ranges.")
                    self.current_color_ranges = {}
                    self.last_config_mod_time = 0
                return

            current_mod_time = os.path.getmtime(COLOR_CONFIG_PATH)
            if current_mod_time != self.last_config_mod_time:
                print(f"[StreamApp] Change detected in {COLOR_CONFIG_PATH}. Reloading color configuration...")
                reloaded_ranges = load_color_ranges()
                if reloaded_ranges is not None: # load_color_ranges returns {} on error/not found, not None
                    self.current_color_ranges = reloaded_ranges
                    self.last_config_mod_time = current_mod_time
                    print(f"[StreamApp] Color configuration reloaded. Active colors: {list(self.current_color_ranges.keys())}")
                else:
                    # This case should not be hit if load_color_ranges always returns a dict
                    print(f"[StreamApp] Failed to reload color configuration from {COLOR_CONFIG_PATH}. Keeping previous settings.")
        except FileNotFoundError:
            # This can happen if the file is deleted between os.path.exists and os.path.getmtime
            # Or if it was created after initial check and then deleted.
            if self.current_color_ranges: # Only clear if it previously had content
                print(f"[StreamApp] Color config file {COLOR_CONFIG_PATH} not found during check. Clearing current ranges.")
                self.current_color_ranges = {}
            self.last_config_mod_time = 0 # Reset mod time as file is gone
        except OSError as e:
            print(f"[StreamApp] Error checking/reloading color config: {e}")

    def _initialize_components(self):
        print("[StreamApp] Initializing components...")
        self.cap, self.frame_width, self.frame_height, self.fps = initialize_camera(self.args.camera_index)
        if not self.cap:
            raise RuntimeError("Failed to initialize camera.")

        self.arm_controller = initialize_arm_controller(self.args)
        self.state_manager = StateManager()
        print("[StreamApp] Components initialized.")

    def _start_mediamtx_server(self):
        if not os.path.exists(self.mediamtx_bin):
            print(f"[StreamApp] Error: mediamtx executable not found at {self.mediamtx_bin}")
            return False
        if not os.path.exists(self.mediamtx_config):
            print(f"[StreamApp] Error: mediamtx config not found at {self.mediamtx_config}")
            return False
        
        if not os.access(self.mediamtx_bin, os.X_OK):
            print(f"[StreamApp] Warning: mediamtx at {self.mediamtx_bin} is not executable. Attempting to set permission.")
            try:
                os.chmod(self.mediamtx_bin, 0o755)
                print(f"[StreamApp] Set execute permission for {self.mediamtx_bin}")
            except Exception as e:
                print(f"[StreamApp] Error setting execute permission for {self.mediamtx_bin}: {e}")
                return False

        print(f"[StreamApp] Starting mediamtx server with config: {self.mediamtx_config}")
        try:
            self.mediamtx_process = subprocess.Popen(
                [self.mediamtx_bin, self.mediamtx_config],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"[StreamApp] mediamtx server starting with PID: {self.mediamtx_process.pid}. Waiting a moment for it to initialize...")
            time.sleep(2) # Give mediamtx some time to start

            if self.mediamtx_process.poll() is not None:
                # Process exited prematurely
                stdout, stderr = self.mediamtx_process.communicate()
                print(f"[StreamApp] Error: mediamtx server failed to start or exited prematurely.")
                print(f"mediamtx stdout:\\n{stdout.decode(errors='ignore')}")
                print(f"mediamtx stderr:\\n{stderr.decode(errors='ignore')}")
                self.mediamtx_process = None
                return False
            else:
                print("[StreamApp] mediamtx server seems to be running.")
                return True
        except Exception as e:
            print(f"[StreamApp] Exception while starting mediamtx server: {e}")
            if self.mediamtx_process: # Ensure cleanup if Popen succeeded but later steps failed
                self.mediamtx_process.terminate()
                self.mediamtx_process.wait()
            self.mediamtx_process = None
            return False

    def _initialize_pusher(self):
        rtsp_url_internal = f'rtsp://127.0.0.1:{self.args.rtsp_port}{self.args.rtsp_path}'
        # Ensure frame_width, frame_height, and fps are valid before passing
        if not all([self.frame_width, self.frame_height, self.fps]):
            print("[StreamApp] Error: Camera properties (width, height, fps) not properly initialized for pusher.")
            self.pusher = None
            return
            
        self.pusher = RTSPPusher(rtsp_url_internal, width=self.frame_width, height=self.frame_height, fps=self.fps)
        
        pi_ip = get_local_ip()
        if pi_ip != "N/A":
            print(f"RTSP Stream available at: rtsp://{pi_ip}:{self.args.rtsp_port}{self.args.rtsp_path}")
        else:
            print(f"Could not determine Raspberry Pi's IP address automatically.")
            print(f"RTSP Stream should be available on port {self.args.rtsp_port} at path {self.args.rtsp_path} on this machine's IP.")

    def run(self):
        print(f"[StreamApp] System running in RTSP STREAMING mode. Press Ctrl+C in terminal to quit.")
        
        if not self._start_mediamtx_server():
            print("[StreamApp] Failed to start mediamtx server. Exiting.")
            return

        self._initialize_pusher()
        if not self.pusher: # Check if pusher was initialized successfully
            print("[StreamApp] Failed to initialize RTSP pusher. Exiting.")
            return

        # Initialize a counter for less frequent checks, e.g., every N frames or X seconds
        check_config_interval_seconds = 5 # Check every 5 seconds
        last_config_check_time = time.time()

        while True:
            if not self.cap or not self.cap.isOpened():
                print("[StreamApp] Error: Camera not available or closed.")
                break
            
            current_time = time.time()
            if current_time - last_config_check_time > check_config_interval_seconds:
                self._check_and_reload_color_config()
                last_config_check_time = current_time

            ret, frame = self.cap.read()
            if not ret:
                print("[StreamApp] Error: Can't receive frame (stream end or camera error?). Exiting ...")
                break

            # Corrected unpacking to match the 3 return values from process_frame_and_control_arm
            result_frame, labels, mask = process_frame_and_control_arm(
                frame, 
                self.state_manager, 
                self.arm_controller,
                current_color_ranges=self.current_color_ranges # Pass the potentially updated ranges
            )
            
            if self.pusher:
                self.pusher.push_frame(result_frame)
            
            # time.sleep(0.001) # Optional delay, consider removing or making configurable if it impacts performance

    def cleanup(self):
        print("[StreamApp] Cleaning up resources...")
        # Pass self.cap and self.arm_controller to the cleanup function from app_core
        app_core_cleanup(self.cap, self.arm_controller) 
        
        if self.pusher:
            self.pusher.release()
            print("[StreamApp] RTSP Pusher released.")

        if self.mediamtx_process and self.mediamtx_process.poll() is None: # Check if process is running
            print(f"[StreamApp] Terminating mediamtx server (PID: {self.mediamtx_process.pid})...")
            self.mediamtx_process.terminate()
            try:
                self.mediamtx_process.wait(timeout=5)
                print("[StreamApp] mediamtx server terminated.")
            except subprocess.TimeoutExpired:
                print("[StreamApp] mediamtx server did not terminate in time, killing...")
                self.mediamtx_process.kill()
                self.mediamtx_process.wait() # Wait for kill
                print("[StreamApp] mediamtx server killed.")
            except Exception as e:
                print(f"[StreamApp] Error during mediamtx termination: {e}")
        elif self.mediamtx_process: # Process already terminated or was never properly started
             print(f"[StreamApp] mediamtx server (PID: {self.mediamtx_process.pid if hasattr(self.mediamtx_process, 'pid') else 'N/A'}) already stopped or failed to start.")
        
        print("[StreamApp] Cleanup finished.")

def main():
    parser = argparse.ArgumentParser(description="ARMCtrl OpenCV Application - RTSP Streaming Mode")
    # Add common arguments using the function from app_core
    parser = add_common_arguments(parser)
    # Add arguments specific to main_stream.py
    parser.add_argument(
        '--rtsp_port',
        type=int,
        default=8554,
        help="Port for the RTSP stream (mediamtx server port)."
    )
    parser.add_argument(
        '--rtsp_path',
        type=str,
        default='/live',
        help="Path for the RTSP stream (e.g., /live, /mystream)."
    )
    args = parser.parse_args()

    app = None
    try:
        app = StreamApplication(args)
        app.run()
    except RuntimeError as e: # Catch RuntimeError from _initialize_components
        print(f"[Main] Runtime error during app initialization or run: {e}")
    except KeyboardInterrupt:
        print("\n[Main] Program interrupted by user (Ctrl+C).")
    except Exception as e:
        print(f"[Main] An unexpected error occurred: {e}")
    finally:
        if app:
            app.cleanup()
        print("[Main] Application terminated.")

if __name__ == "__main__":
    main()
