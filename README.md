# ARMCtrl_OpenCV

本專案為一套基於 OpenCV 的機械手臂視覺控制系統，支援 HSV 顏色遮罩調整、形狀辨識、中文 UI 顯示、鏡頭切換，以及可切換 Arduino/樹莓派控制器，方便於不同硬體平台測試與部署。

---

## 主要功能

- **即時攝影機影像顯示與辨識**
- **HSV 遮罩調整 UI**（滑鼠拖曳調整 H/S/V 範圍）
- **遮罩單色顯示**（只顯示目前調整的顏色遮罩）
- **形狀辨識與中文標註**（紅色/藍色/綠色，方形/三角形，信心度）
- **UI 按鈕操作**（調整顏色、儲存設定、自動模式、鏡頭切換、離開）
- **滑鼠 hover 按鈕高亮效果**
- **鏡頭即時切換**
- **自動模式/無頭模式**
- **支援 Arduino/樹莓派控制機械手臂**（可切換控制器）
- **中文顯示（需字型檔 chinese.ttf）**

---

## 安裝需求

- **Python： 3.9.0 ~ 3.11.9**
- OpenCV (`opencv-python`)
- Pillow (`pillow`)
- numpy
- pyserial（如需 Arduino 控制）
- 需有中文字型檔（如 `chinese.ttf`，放在專案根目錄）

安裝所有需求：
```bash
pip install -r requirements.txt
```

---

## 使用方式

### 1.請先確認工作目錄是在"ARMCtrl_OpenCV"底下。

### 2. 啟動主程式

```bash
python main_local.py
```

### 3. UI 操作

- 透過右側按鈕調整紅/藍/綠色 HSV 範圍
- 可即時切換鏡頭
- 可儲存 HSV 設定
- 可進入自動模式（無 UI 持續辨識）

---

## 硬體整合與接線

本專案可透過樹莓派的 GPIO 控制四路繼電器模組，以觸發外部裝置（如 Arduino 或其他微控制器）執行對應動作。

### 繼電器控制協議

系統採用**編碼觸發協議**，使用 1 個繼電器作為觸發信號，另外 3 個作為數據信號。

- **R1 (繼電器1):** 作為**觸發信號 (Trigger Signal)**。當 R1 由 OFF 轉 ON 時，代表一次有效指令的開始。
- **R2, R3, R4 (繼電器2-4):** 作為**數據信號 (Data Signals)**。它們的 ON/OFF 組合構成 3-bit 二進位碼，代表不同動作。

#### 標籤與繼電器狀態對應表

| 影像辨識標籤 | 觸發函式 | R2 (Data) | R3 (Data) | R4 (Data) | 3-bit 編碼 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **'A'** | `trigger_action_A()` | `OFF` | `OFF` | `ON` | **001** |
| **'B'** | `trigger_action_B()` | `OFF` | `ON` | `OFF` | **010** |
| **'C'** | `trigger_action_C()` | `OFF` | `ON` | `ON` | **011** |
| **'D'** | `trigger_action_D()` | `ON` | `OFF` | `OFF` | **100** |
| **'E'** | `trigger_action_E()` | `ON` | `OFF` | `ON` | **101** |
| **'F'** | `trigger_action_F()` | `ON` | `ON` | `OFF` | **110** |

### 硬體接線建議

以下接線圖以 `pi_gpio_controller.py` 中用於測試的預設腳位為例。

- **Relay 1 (Trigger):** GPIO 17
- **Relay 2 (Data):** GPIO 27
- **Relay 3 (Data):** GPIO 22
- **Relay 4 (Data):** GPIO 23

```text
      Raspberry Pi 4B
+--------------------------+                          +------------------------+
|      (GPIO Header)       |                          |  4-Channel Relay Module|
|                          |                          |                        |
| 3.3V [ ]      [ ] 5V     |--------------------------o VCC                    |
|      [ ]      [ ] 5V     |                          |                        |
|      [ ]      [ ] GND    |--------------------------o GND                    |
|      [ ]      [ ] GPIO14 |                          |                        |
| GND  [ ]      [ ] GPIO15 |                          |                        |
|      [ ]      [ ] GPIO18 |                          |                        |
|GPIO17[ ]o-----[ ]        |                          o IN1 (To Arduino/Device)|
|      [ ]      [ ] GND    |                          |                        |
|GPIO27[ ]o-----[ ]        |                          o IN2 (To Arduino/Device)|
|GPIO22[ ]o-----[ ]        |                          o IN3 (To Arduino/Device)|
| 3.3V [ ]      [ ] GPIO23 o--------------------------o IN4 (To Arduino/Device)|
|      [ ]      [ ] GPIO24 |                          |                        |
|      ...                 |                          +------------------------+
+--------------------------+
```

**接線說明:**
1.  **繼電器供電:** 將繼電器模組的 `VCC` 接至樹莓派的 `5V`，`GND` 接至 `GND`。
2.  **信號線:** 將樹莓派的 GPIO 腳位 (17, 27, 22, 23) 分別連接到繼電器模組的 `IN1`, `IN2`, `IN3`, `IN4`。
3.  **繼電器輸出:** 繼電器模組的輸出端 (COM, NO, NC) 則連接到下游設備的對應輸入腳位。
4.  **腳位修改:** 您可以在程式中呼叫 `initialize_arm_controller` 時，傳入自訂的 GPIO 腳位列表。
5.  **邏輯電位:** 程式預設使用**低電位觸發** (`inverse_logic=True`) 的繼電器模組。如果您的模組為高電位觸發，請修改此參數。


---

## 注意事項

- 若出現中文亂碼，請確認 `chinese.ttf` 字型檔存在於專案目錄。
- 若要切換控制器，請依照註解啟用/註解對應區塊。
- 若要新增顏色或形狀，請修改 `utils/vision_processing/detector.py` 及 `color_config.json`。

---

## 專案結構簡介

```
ARMCtrl_OpenCV/
├─ main_local.py                # 主程式
├─ requirements.txt
├─ chinese.ttf                  # 中文字型檔
├─ utils/
│  ├─ app_core.py
│  ├─ arm_controller/
│  │  ├─ pi_gpio_controller.py  # 樹莓派/Arduino 控制器
│  ├─ vision_processing/
│     ├─ detector.py
│     ├─ ui_basic.py            # draw_chinese_text 等 UI 工具
│     ├─ color_config.json
│     └─ ...
└─ ...
```

---

## 聯絡/貢獻

如有問題或建議，歡迎開 issue 或 PR！
