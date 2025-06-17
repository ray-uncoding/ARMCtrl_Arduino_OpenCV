'''
import cv2
import threading
import time

class RTSPReceiver:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

    def _connect(self):
        """建立與 RTSP 串流的連接"""
        self.cap = cv2.VideoCapture(self.rtsp_url)
        if not self.cap.isOpened():
            print(f"錯誤：無法開啟 RTSP 串流: {self.rtsp_url}")
            self.cap = None
            return False
        print(f"成功連接到 RTSP 串流: {self.rtsp_url}")
        return True

    def _read_frames(self):
        """從串流讀取影像幀"""
        while self.is_running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                print("錯誤：無法從 RTSP 串流讀取影像幀。嘗試重新連接...")
                self.cap.release()
                self.cap = None
                # 等待一段時間後嘗試重新連接
                time.sleep(5)
                if not self._connect():
                    # 如果重新連接失敗，則停止執行緒
                    print("重新連接失敗，停止讀取影像幀。")
                    break
                continue

            with self.lock:
                self.frame = frame

            # 控制幀率，避免 CPU 過度使用 (可選)
            # time.sleep(1/30) # 假設 30 FPS

    def start(self):
        """開始接收影像串流"""
        if self.is_running:
            print("RTSP 接收器已在執行中。")
            return

        if not self._connect():
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._read_frames)
        self.thread.daemon = True  # 設定為守護執行緒，主程式結束時會自動關閉
        self.thread.start()
        print("RTSP 影像串流接收已啟動。")

    def stop(self):
        """停止接收影像串流"""
        if not self.is_running:
            print("RTSP 接收器尚未執行。")
            return

        self.is_running = False
        if self.thread:
            self.thread.join()  # 等待執行緒結束

        if self.cap:
            self.cap.release()
            self.cap = None
        print("RTSP 影像串流接收已停止。")

    def get_frame(self):
        """獲取當前影像幀"""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy() # 回傳幀的副本以避免外部修改

if __name__ == '__main__':
    # RTSP 串流 URL (請替換為您的樹莓派 RTSP 串流 URL)
    # 預設的 rtsp_pusher.py 推流 URL 是 rtsp://localhost:8554/live
    # 如果您在不同機器上執行接收器，請將 localhost 替換為樹莓派的 IP 位址
    RTSP_URL = "rtsp://<樹莓派的IP位址>:8554/live" # 例如 "rtsp://192.168.1.100:8554/live"

    print(f"嘗試從 {RTSP_URL} 接收 RTSP 串流...")
    receiver = RTSPReceiver(RTSP_URL)
    receiver.start()

    if not receiver.is_running:
        print("無法啟動 RTSP 接收器，請檢查 URL 和推流服務是否正常。")
    else:
        print("按 'q' 鍵關閉視窗並停止接收。")
        while True:
            frame = receiver.get_frame()
            if frame is not None:
                cv2.imshow("RTSP Stream Receiver", frame)
            else:
                # 如果一開始就沒有畫面，給一點時間讓串流開始
                print("等待影像幀...")
                time.sleep(0.5)


            # 按 'q' 鍵退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        receiver.stop()
        cv2.destroyAllWindows()
        print("程式結束。")
'''
