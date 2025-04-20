# signal_sender.py

import serial
import time
import threading

class SignalSender:
    def __init__(self, port='COM5', baudrate=9600):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)
            print(f"[SignalSender] Connected to {port} at {baudrate} baud.")
            self.running = True
            threading.Thread(target=self.listen_to_serial, daemon=True).start()
        except serial.SerialException as e:
            print(f"[SignalSender] Error: {e}")
            self.ser = None
            self.running = False

    def send(self, signal: str):
        if self.ser and self.ser.is_open:
            self.ser.write(signal.encode())
            print(f"[SignalSender] Sent: {signal}")

    def send_async(self, signal: str):
        threading.Thread(target=self.send, args=(signal,), daemon=True).start()

    def listen_to_serial(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    if line:
                        print(f"[Arduino Response] {line}")
            except Exception as e:
                print(f"[SignalSender] Serial read error: {e}")
                break

    def close(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SignalSender] Serial closed.")
