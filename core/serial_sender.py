import serial
import serial.tools.list_ports

PORT = None
BAUD = 9600

ser = None

def init_serial():
    global ser
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "USB" in p.description or "Arduino" in p.description:
            try:
                ser = serial.Serial(p.device, BAUD, timeout=1)
                print(f"✅ 已連接到序列埠：{p.device}")
                return
            except Exception as e:
                print(f"⚠️ 開啟序列埠失敗：{e}")
    print("❌ 找不到可用序列埠")


def send_signal(char_code):
    global ser
    if not ser or not ser.is_open:
        print("❌ 尚未連接序列埠！")
        return
    try:
        ser.write(char_code.encode())
        print(f"📤 已傳送訊號：{char_code}")
    except Exception as e:
        print(f"⚠️ 傳送失敗：{e}")
