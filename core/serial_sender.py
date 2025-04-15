import serial

class SerialSender:
    def __init__(self, port: str, baudrate: int = 9600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"[SerialSender] 已連接至 {port} @ {baudrate} baudrate")
        except serial.SerialException as e:
            self.ser = None
            print(f"[SerialSender] 無法開啟序列埠：{e}")

    def send_code(self, code: str):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(code.encode('utf-8'))
                print(f"[SerialSender] 傳送指令：{code}")
            except Exception as e:
                print(f"[SerialSender] 傳送失敗：{e}")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SerialSender] 已關閉序列埠")