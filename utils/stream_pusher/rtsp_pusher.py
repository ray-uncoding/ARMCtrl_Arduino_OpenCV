import cv2
import subprocess
import numpy as np
import threading
import time

class RTSPPusher:
    def __init__(self, camera_id=0, width=640, height=480, fps=30, rtsp_url="rtsp://0.0.0.0:8554/live"):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.rtsp_url = rtsp_url
        self.ffmpeg_process = None
        self.cap = None
        self._running = False
        self._thread = None

        print(f"[RTSPPusher] Initialized with camera_id={camera_id}, resolution={width}x{height}, fps={fps}, rtsp_url={rtsp_url}")

    def _start_ffmpeg(self):
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',  # OpenCV default pixel format
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',  # Input from stdin
            '-an',  # No audio
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # For low latency
            '-tune', 'zerolatency',
            '-pix_fmt', 'yuv420p', # Common format for H.264
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp', # Use TCP for more reliability over local networks
            self.rtsp_url
        ]
        print(f"[RTSPPusher] Starting FFmpeg with command: {' '.join(command)}")
        try:
            self.ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
            print("[RTSPPusher] FFmpeg process started.")
        except FileNotFoundError:
            print("[RTSPPusher] ERROR: FFmpeg command not found. Please ensure FFmpeg is installed and in your PATH.")
            self.ffmpeg_process = None
        except Exception as e:
            print(f"[RTSPPusher] ERROR: Failed to start FFmpeg: {e}")
            self.ffmpeg_process = None


    def start_capture(self):
        print(f"[RTSPPusher] Attempting to open camera: {self.camera_id}")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"[RTSPPusher] ERROR: Cannot open camera {self.camera_id}")
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[RTSPPusher] Camera opened. Actual resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")
        
        # It's possible the camera doesn't support the exact settings
        # Update width/height/fps if they differ, so FFmpeg gets correct parameters
        self.width = actual_width
        self.height = actual_height
        # Some cameras might not report FPS correctly or allow setting it, use configured if zero
        self.fps = actual_fps if actual_fps > 0 else self.fps

        return True

    def _run(self):
        if not self.start_capture():
            self._running = False
            print("[RTSPPusher] Failed to start camera capture. Stopping.")
            return

        self._start_ffmpeg()
        if not self.ffmpeg_process or self.ffmpeg_process.stdin is None:
            print("[RTSPPusher] FFmpeg process not started correctly. Stopping.")
            self._running = False
            if self.cap.isOpened():
                self.cap.release()
            return

        print("[RTSPPusher] Starting to push frames...")
        while self._running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("[RTSPPusher] Failed to grab frame. End of stream?" )
                time.sleep(0.1) # Wait a bit before retrying or exiting
                # Check if camera is still there
                if not self.cap.isOpened():
                    print("[RTSPPusher] Camera disconnected.")
                    break
                continue

            if self.ffmpeg_process and self.ffmpeg_process.stdin:
                try:
                    # Ensure frame is in the correct dimensions if camera settings changed
                    if frame.shape[1] != self.width or frame.shape[0] != self.height:
                        frame = cv2.resize(frame, (self.width, self.height))
                    
                    self.ffmpeg_process.stdin.write(frame.tobytes())
                except IOError as e:
                    print(f"[RTSPPusher] FFmpeg stdin write error: {e}. FFmpeg might have closed.")
                    break
                except Exception as e:
                    print(f"[RTSPPusher] Error writing frame to FFmpeg: {e}")
                    break
            else:
                print("[RTSPPusher] FFmpeg process not available to write frame.")
                break
        
        print("[RTSPPusher] Frame pushing loop ended.")
        self.stop()


    def start(self):
        if self._running:
            print("[RTSPPusher] Pusher is already running.")
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[RTSPPusher] Pusher thread started.")

    def stop(self):
        print("[RTSPPusher] Attempting to stop pusher...")
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            print("[RTSPPusher] Waiting for pusher thread to join...")
            self._thread.join(timeout=5) # Wait for 5 seconds
            if self._thread.is_alive():
                print("[RTSPPusher] Pusher thread did not join in time.")
        
        if self.cap is not None and self.cap.isOpened():
            print("[RTSPPusher] Releasing camera...")
            self.cap.release()
            self.cap = None
        
        if self.ffmpeg_process is not None:
            print("[RTSPPusher] Terminating FFmpeg process...")
            if self.ffmpeg_process.stdin:
                try:
                    self.ffmpeg_process.stdin.close()
                except Exception as e:
                    print(f"[RTSPPusher] Error closing FFmpeg stdin: {e}")
            try:
                self.ffmpeg_process.terminate() # Send SIGTERM
                self.ffmpeg_process.wait(timeout=5) # Wait for termination
            except subprocess.TimeoutExpired:
                print("[RTSPPusher] FFmpeg did not terminate gracefully, killing...")
                self.ffmpeg_process.kill() # Send SIGKILL
                self.ffmpeg_process.wait()
            except Exception as e:
                print(f"[RTSPPusher] Error terminating FFmpeg: {e}")
            self.ffmpeg_process = None
        print("[RTSPPusher] Pusher stopped.")

# Example usage:
if __name__ == '__main__':
    RTSP_SERVER_IP = '0.0.0.0' # Listen on all available network interfaces on the Pi
    RTSP_PORT = 8554
    RTSP_PATH = '/live'
    rtsp_url = f'rtsp://{RTSP_SERVER_IP}:{RTSP_PORT}{RTSP_PATH}'

    # Attempt to determine a suitable camera index
    camera_index = -1
    for i in range(5): # Try indices 0 through 4
        cap_test = cv2.VideoCapture(i)
        if cap_test.isOpened():
            print(f"Camera found at index {i}")
            camera_index = i
            cap_test.release()
            break
        cap_test.release()

    if camera_index == -1:
        print("Error: No camera found. Please ensure a camera is connected.")
        exit()
        
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera index {camera_index}")
        exit()

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    # Use a common FPS if camera FPS is too low or high, or zero
    fps = fps if 5 <= fps <= 60 else 20


    print(f"Camera opened successfully: {frame_width}x{frame_height} @ {fps} FPS (will be resized for streaming)")
    
    # Initialize pusher with desired streaming resolution
    # Using a smaller resolution for streaming to save bandwidth/CPU
    stream_width = 640
    stream_height = 480
    pusher = RTSPPusher(rtsp_url, width=stream_width, height=stream_height, fps=fps)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Error: Can't receive frame (stream end?). Exiting ...")
                break

            # Display the frame locally on the Pi (if X11 forwarding is working or a display is connected)
            # cv2.imshow('Pushing to RTSP...', frame) # Comment out if no display
            
            pusher.push_frame(frame)

            # Check for 'q' key press to quit (only works if cv2.imshow is active and window is focused)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     print("'q' pressed, stopping.")
            #     break
            # Add a small delay to control frame rate if needed, though ffmpeg -r should handle it
            # time.sleep(1/fps)


    except KeyboardInterrupt:
        print("Streaming stopped by user (KeyboardInterrupt).")
    except Exception as e:
        print(f"An error occurred during streaming: {e}")
    finally:
        print("Releasing resources...")
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        if 'pusher' in locals():
            pusher.release()
        # cv2.destroyAllWindows() # Comment out if no display
        print("Resources released. Exiting.")

