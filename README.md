# ARMCtrl_Arduino_OpenCV 🎯  
簡易色彩與形狀識別機器手臂控制系統

本專案使用 Python + OpenCV 辨識畫面中物件的「顏色 + 形狀」，並透過 Serial 傳送對應指令控制 Arduino 機器手臂。

---

## 🛠 安裝與執行流程（4 步驟）

### 1️⃣ 安裝必要模組
請先安裝以下 Python 套件（建議使用 Python 3.9+）：

```bash
pip install opencv-python pyserial numpy
```

---

### 2️⃣ 使用 `BRG_Bar.py` 拍攝照片並調整 HSV 範圍
運行以下程式，將攝影機畫面靜止，拍攝你想識別的物件：

```bash
python BRG_Bar.py
```

你可以使用滑桿調整 HSV 範圍，觀察遮罩區畫面何時正確框選出目標。  
記錄你理想的 HSV 區間，例如：

```python
'Red':   ([0, 82, 192], [27, 203, 255])
```
按 `q` 可中止程式。
按 `s` 可儲存調整。
---

### 3️⃣ 運行主系統
準備好後，運行主程式：

```bash
python main.py
```

畫面會分成：
- 左邊：原始畫面
- 右邊：辨識後畫面（含框選與文字）
- 並且會自動透過 Serial 傳送指令給 Arduino

按 `q` 可中止程式。

---

## 🧩 常見操作提示

- 📷 請確保攝影機鏡頭亮度充足，避免太暗影響辨識
- 🟥 若辨識不穩定，可調整 HSV 範圍或增加 `cv2.GaussianBlur`
- 🧪 若未偵測到動作不會重複發送（具阻回機制）
- 📦 Arduino 需與 Python 使用相同 baudrate，並選對 COM port

---

## 🙌 作者說明
本專案為展示與實驗用途，可作為物件辨識 + Arduino 控制的入門練習範例。

若有教學需求，建議可加入教學分支，拆分為範例版與完整版。

---
