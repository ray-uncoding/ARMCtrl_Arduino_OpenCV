import cv2
import subprocess
import numpy as np
import time

class RTSPPusher:
    def __init__(self, rtsp_url, width=640, height=480, fps=20):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None
        print(f"[RTSPPusher] Initializing for RTSP URL: {self.rtsp_url}, Resolution: {self.width}x{self.height}, FPS: {self.fps}")
        self._start_ffmpeg()

    def _start_ffmpeg(self):
        command = [
            'ffmpeg',
            '-y',  # Overwrite output files without asking
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',  # OpenCV uses BGR
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',  # Input from stdin
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'veryfast', # Changed from ultrafast
            '-b:v', '1M', # Added bitrate limit to 1 Mbps, adjust as needed
            '-tune', 'zerolatency',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp', # Prefer TCP for reliability
            self.rtsp_url
        ]
        try:
            # Using stderr=subprocess.PIPE to capture FFmpeg errors
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"FFmpeg process starting for RTSP stream: {self.rtsp_url}")
            print(f"FFmpeg command: {' '.join(command)}")
        except FileNotFoundError:
            print("Error: ffmpeg command not found. Please ensure FFmpeg is installed and in your PATH.")
            self.process = None
        except Exception as e:
            print(f"Error starting FFmpeg: {e}")
            self.process = None

    def push_frame(self, frame):
        if not self.process or self.process.stdin is None:
            # Check if the process has terminated
            if self.process and self.process.poll() is not None:
                print("FFmpeg process has terminated. Attempting to read stderr...")
                self._handle_ffmpeg_errors() # Read errors from terminated process
                print("Attempting to restart FFmpeg...")
                self.release() # Clean up existing process before restarting
                self._start_ffmpeg() # Restart FFmpeg
                if not self.process or self.process.stdin is None:
                    print("Failed to restart FFmpeg. Cannot push frame.")
                    return
            else:
                print("FFmpeg process not running or stdin not available, and not terminated. Cannot push frame.")
                return

        if frame is None:
            print("Received an empty frame. Skipping.")
            return

        try:
            resized_frame = cv2.resize(frame, (self.width, self.height))
            self.process.stdin.write(resized_frame.tobytes())
            self.process.stdin.flush() # Ensure data is sent immediately
        except BrokenPipeError:
            print("BrokenPipeError: FFmpeg process may have terminated unexpectedly.")
            self._handle_ffmpeg_errors()
            print("Attempting to restart FFmpeg due to BrokenPipeError...")
            self.release()
            self._start_ffmpeg()
        except Exception as e:
            print(f"Error writing frame to FFmpeg: {e}")
            # You might want to add more specific error handling or restart logic here

    def _handle_ffmpeg_errors(self):
        if self.process and self.process.stderr:
            try:
                # Non-blocking read if possible, or ensure this doesn't hang
                ffmpeg_errors = self.process.stderr.read()
                if ffmpeg_errors:
                    print(f"FFmpeg stderr output:\n{ffmpeg_errors.decode('utf-8', errors='ignore')}")
            except Exception as e:
                print(f"Error reading FFmpeg stderr: {e}")

    def release(self):
        if self.process:
            print("Stopping FFmpeg process...")
            if self.process.stdin:
                try:
                    self.process.stdin.close()
                except Exception as e:
                    print(f"Error closing FFmpeg stdin: {e}")
            
            # Read any remaining stderr output before terminating
            self._handle_ffmpeg_errors()

            if self.process.poll() is None:  # Check if process is still running
                print("Terminating FFmpeg process...")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    print("FFmpeg process terminated.")
                except subprocess.TimeoutExpired:
                    print("FFmpeg did not terminate gracefully, killing.")
                    self.process.kill()
                    self.process.wait() # Ensure kill is processed
                    print("FFmpeg process killed.")
                except Exception as e:
                    print(f"Exception during FFmpeg process termination: {e}")
                    if self.process.poll() is None:
                        print("FFmpeg still running after exception, attempting kill.")
                        self.process.kill()
                        self.process.wait()
                        print("FFmpeg process killed after exception.")
            else:
                print(f"FFmpeg process already terminated with code: {self.process.poll()}")

            if self.process.stderr: # Ensure stderr is closed
                 try:
                    self.process.stderr.close()
                 except Exception as e:
                    print(f"Error closing FFmpeg stderr: {e}")
            
            self.process = None
            print("FFmpeg resources released.")

# Test block
if __name__ == '__main__':
    RTSP_SERVER_IP = '127.0.0.1'  # Changed from 0.0.0.0 to 127.0.0.1
    RTSP_PORT = 8554
    RTSP_PATH = '/live'
    rtsp_url = f'rtsp://{RTSP_SERVER_IP}:{RTSP_PORT}{RTSP_PATH}'

    camera_index = -1
    print("Searching for camera...")
    for i in range(5):
        cap_test = cv2.VideoCapture(i)
        if cap_test.isOpened():
            print(f"Camera found at index {i}")
            camera_index = i
            cap_test.release()
            break
        cap_test.release()

    if camera_index == -1:
        print("Error: No camera found. Please ensure a camera is connected and permissions are correct (e.g., /dev/video0).")
        exit()
        
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open video stream from camera index {camera_index}")
        exit()

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    raw_fps = cap.get(cv2.CAP_PROP_FPS)
    # Use a common FPS if camera FPS is too low or high, or zero, or invalid
    fps = int(raw_fps if raw_fps and 5 <= raw_fps <= 120 else 20)

    print(f"Camera opened successfully: {frame_width}x{frame_height} @ {fps} FPS (Reported by camera: {raw_fps})")
    
    stream_width = 640
    stream_height = 480
    stream_fps = fps # Use camera's FPS for streaming, or the adjusted one
    
    pusher = RTSPPusher(rtsp_url, width=stream_width, height=stream_height, fps=stream_fps)

    # Check if FFmpeg started successfully
    if pusher.process is None or pusher.process.poll() is not None:
        print("FFmpeg process failed to start or terminated prematurely. Exiting.")
        if pusher.process: # if it exists but terminated, try to get error
             pusher._handle_ffmpeg_errors()
        cap.release()
        exit()

    frame_count = 0
    start_time = time.time()
    pusher_instance = pusher # Keep a reference for the finally block

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Error: Can't receive frame (stream end or camera error?). Exiting ...")
                if not cap.isOpened():
                    print("Camera is no longer opened.")
                break

            pusher_instance.push_frame(frame) # Use the instance here
            frame_count += 1

            if frame_count % (stream_fps * 5) == 0: # Every 5 seconds approx
                elapsed_time = time.time() - start_time
                current_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
                # print(f"Streaming... {frame_count} frames pushed. Actual avg FPS: {current_fps:.2f}")
                # Check FFmpeg process status
                if pusher_instance.process and pusher_instance.process.poll() is not None:
                    print(f"FFmpeg process has terminated unexpectedly with code {pusher_instance.process.poll()}.")
                    pusher_instance._handle_ffmpeg_errors()
                    break


    except KeyboardInterrupt:
        print("Streaming stopped by user (KeyboardInterrupt).")
    except Exception as e:
        print(f"An error occurred during streaming: {e}")
    finally:
        print("Releasing resources...")
        if 'cap' in locals() and cap.isOpened():
            cap.release()
            print("Camera released.")
        # Ensure pusher_instance is used here and it's not None
        if 'pusher_instance' in locals() and pusher_instance is not None:
            pusher_instance.release()
        print("All resources released. Exiting.")

