from .signal_sender import SignalSender
import time

# 初始化 sender（請根據你的實際 port 調整）
sender = SignalSender(port='COM5', baudrate=9600)

# 傳送訊號
test_signal = 'A'
print(f"[Test] Sending: {test_signal}")
sender.send(test_signal)

# 等待 Arduino 回應
time.sleep(0.5)

# 嘗試讀取回傳訊息（最多讀三行）
if sender.ser and sender.ser.in_waiting:
    for _ in range(3):
        response = sender.ser.readline().decode().strip()
        if response:
            print(f"[Arduino Response] {response}")
else:
    print("[Test] No response from Arduino.")

# 關閉連線
sender.close()
