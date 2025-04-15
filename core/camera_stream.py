import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage


class CameraThread(QThread):
    frame_updated = pyqtSignal(QImage)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        self.running = True
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_updated.emit(qt_image)
        cap.release()

    def stop(self):
        self.running = False
        self.wait()
