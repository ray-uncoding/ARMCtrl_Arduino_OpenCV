import cv2
import numpy as np

print("Attempting to initialize camera...")
cap = None  # Initialize cap to None
try:
    # 嘗試開啟預設鏡頭 (通常是 0)
    # 如果您有多個鏡頭或特定鏡頭，可能需要更改索引
    cap = cv2.VideoCapture(0)

    if cap.isOpened():
        print("Camera initialized successfully.")
        ret, frame = cap.read()
        if ret:
            print(f"Frame captured successfully. Frame shape: {frame.shape}")
            # 您可以在這裡加入其他非 GUI 的影像處理或分析
            # 例如：print(f"Frame dtype: {frame.dtype}")
        else:
            print("Failed to capture frame from camera.")
    else:
        print("Failed to open camera.")

except Exception as e:
    print(f"An error occurred during camera operations: {e}")
finally:
    if cap is not None and cap.isOpened():
        cap.release()
        print("Camera released.")
    print("Exiting test script.")
