char val = 'n';  // 預設值

void setup() {
  Serial.begin(9600);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(13, OUTPUT);  // 內建 LED
  
  resetPins();
}

void loop() {
  if (Serial.available()) {
    val = Serial.read();
    Serial.print("收到指令: ");
    Serial.println(val);

    // 如果收到測試訊號 't'，執行閃燈三下
    if (val == 't') {
      test_led();
      val = 'n';  // 避免干擾
    }
  }

  switch (val) {
    case 'A':  // 紅色三角形
      action_a();
      break;
    case 'B':  // 紅色方形
      action_b();
      break;
    case 'C':  // 黑色三角形
      action_c();
      break;
    case 'D':  // 黑色方形
      action_d();
      break;
    case 'R':
      resetPins();
      break;
  }
  delay(100);
}

void resetPins() {
  digitalWrite(8, 0);
  digitalWrite(9, 0);
  digitalWrite(10, 0);
  digitalWrite(11, 0);
}

void test_led() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(13, 1);
    delay(1000);
    digitalWrite(13, 0);
    delay(1000);
  }
  Serial.println("閃燈完成");
}

// npn IO口訊號要反過來

void action_a() {
  digitalWrite(8, 0);
  digitalWrite(9, 1);
  digitalWrite(10, 1);
  digitalWrite(11, 1);
  Serial.println("動作 A: 1000");
  val = 'n';
}

void action_b() {
  digitalWrite(8, 1);
  digitalWrite(9, 0);
  digitalWrite(10, 1);
  digitalWrite(11, 1);
  Serial.println("動作 B: 0100");
  val = 'n';
}

void action_c() {
  digitalWrite(8, 0);
  digitalWrite(9, 0);
  digitalWrite(10, 1);
  digitalWrite(11, 1);
  Serial.println("動作 C: 1100");
  val = 'n';
}

void action_d() {
  digitalWrite(8, 1);
  digitalWrite(9, 1);
  digitalWrite(10, 0);
  digitalWrite(11, 1);
  Serial.println("動作 D: 0010");
  val = 'n';
}
