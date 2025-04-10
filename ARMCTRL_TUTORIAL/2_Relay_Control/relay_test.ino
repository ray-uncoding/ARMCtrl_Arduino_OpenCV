// 教學用途：控制 4 路繼電器模組輪流開關

int relayPins[] = {8, 9, 10, 11}; // 定義繼電器接腳陣列
const int delayTime = 1000;       // 每個繼電器開關間隔時間 (毫秒)

void setup() {
  for (int i = 0; i < 4; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH); // 初始設為不導通（視模組邏輯）
  }
}

void loop() {
  for (int i = 0; i < 4; i++) {
    digitalWrite(relayPins[i], LOW);   // 啟動該繼電器（LOW = 導通）
    delay(delayTime);
    digitalWrite(relayPins[i], HIGH);  // 關閉該繼電器
  }
}
