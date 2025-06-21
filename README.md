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
