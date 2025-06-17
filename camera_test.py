import cv2

def test_camera(source, api_preference=None):
    cap = None
    try:
        if api_preference is not None:
            print(f"Attempting to open camera: {source} with API: {api_preference}")
            cap = cv2.VideoCapture(source, api_preference)
        else:
            print(f"Attempting to open camera: {source}")
            cap = cv2.VideoCapture(source)

        if cap is None or not cap.isOpened():
            print(f"Error: Cannot open camera at source: {source} (API: {api_preference if api_preference is not None else 'default'})")
            return False
        else:
            print(f"Success: Camera {source} (API: {api_preference if api_preference is not None else 'default'}) opened.")
            print(f"  Backend name: {cap.getBackendName()}")
            ret, frame = cap.read()
            if ret:
                print(f"  Frame captured successfully: {frame.shape}")
            else:
                print("  Error: Failed to capture frame.")
            cap.release()
            return True
    except Exception as e:
        print(f"Exception while trying to open camera {source} (API: {api_preference if api_preference is not None else 'default'}): {e}")
        if cap is not None:
            cap.release()
        return False

print("--- Testing camera sources ---")
test_camera(0)
print("-" * 30)
test_camera("/dev/video0")
print("-" * 30)
test_camera(1) # Just in case
print("-" * 30)
test_camera("/dev/video1") # Just in case
print("-" * 30)

# Try with explicit V4L2 backend
print("--- Testing with explicit CAP_V4L2 backend ---")
if hasattr(cv2, 'CAP_V4L2'):
    test_camera(0, cv2.CAP_V4L2)
    print("-" * 30)
    test_camera("/dev/video0", cv2.CAP_V4L2)
    print("-" * 30)
    test_camera(1, cv2.CAP_V4L2) # Just in case
    print("-" * 30)
    test_camera("/dev/video1", cv2.CAP_V4L2) # Just in case
else:
    print("cv2.CAP_V4L2 is not available in this OpenCV build.")

print("--- Test finished ---")
