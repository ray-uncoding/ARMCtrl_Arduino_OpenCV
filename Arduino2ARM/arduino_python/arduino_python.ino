const int relay_channal_1 = 11;
const int relay_channal_2 = 10;
const int relay_channal_3 = 9;
const int relay_channal_4 = 8;
const int test_ledPin     = 13;

#define BUADRATE 9600

bool INVERSE = true;   
//bool INVERSE = false;

char val;

void setup() {
  Serial.begin(BUADRATE);
  pinMode(relay_channal_1, OUTPUT);
  pinMode(relay_channal_2, OUTPUT);
  pinMode(relay_channal_3, OUTPUT);
  pinMode(relay_channal_4, OUTPUT);
  pinMode(test_ledPin, OUTPUT);
  relay_output(0, 0, 0, 0);   //釋放訊號
  val = 't';
}

void loop() {
  if (Serial.available()) {
    val = Serial.read();
    Serial.print("收到指令: ");
    Serial.println(val);
  }

  switch (val) {
    case 'A':  // 紅色三角形
      Serial.println("動作 A: 0001");

      delay(3000);                //等待手臂穩定
      relay_output(0, 0, 0, 1);   //發送訊號拿取
      delay(3000);                //維持訊號
      relay_output(0, 0, 0, 0);   //釋放訊號

      eat_signal();               //吃掉多餘訊號
      val = 'n';                  //阻回
      break;
    case 'B':  // 紅色方形
      Serial.println("動作 B: 0010");

      delay(3000);                //等待手臂穩定
      relay_output(0, 0, 1, 0);   //發送訊號拿取
      delay(3000);                //維持訊號
      relay_output(0, 0, 0, 0);   //釋放訊號
      eat_signal();               //吃掉多餘訊號
      val = 'n';                  //阻回
      break;
    case 'C':  // 藍色三角形
      Serial.println("動作 C: 0011");

      delay(3000);                //等待手臂穩定
      relay_output(0, 0, 1, 1);   //發送訊號拿取
      delay(3000);                //維持訊號
      relay_output(0, 0, 0, 0);   //釋放訊號
      eat_signal();               //吃掉多餘訊號
      val = 'n';                  //阻回
      break;
    case 'D':  // 藍色方形
      Serial.println("動作 D: 0100");

      delay(3000);                //等待手臂穩定
      relay_output(0, 1, 0, 0);   //發送訊號拿取
      delay(3000);                //維持訊號
      relay_output(0, 0, 0, 0);   //釋放訊號
      eat_signal();               //吃掉多餘訊號
      val = 'n';                  //阻回
      break;
    case 't':  // 測試通訊
      test_led();
      val = 'n';
      break;
    default:
      relay_output(0, 0, 0, 0);   //釋放訊號
      break;
  }
  delay(100);
}

void test_led() {
  Serial.println("測試開始! 準備閃燈");
  for (int i = 0; i < 3; i++) {
    digitalWrite(test_ledPin, 1);
    delay(1000);
    digitalWrite(test_ledPin, 0);
    delay(1000);
  }
  Serial.println("測試完成");
}

void relay_output(int IN_1, int IN_2, int IN_3, int IN_4){
  if (INVERSE){
    IN_1 = !IN_1;
    IN_2 = !IN_2;
    IN_3 = !IN_3;
    IN_4 = !IN_4;
  }
  digitalWrite(relay_channal_1, IN_1);
  digitalWrite(relay_channal_2, IN_2);
  digitalWrite(relay_channal_3, IN_3);
  digitalWrite(relay_channal_4, IN_4);
}

void eat_signal(){
  while (Serial.available()) {
    val = Serial.read();
  }
}