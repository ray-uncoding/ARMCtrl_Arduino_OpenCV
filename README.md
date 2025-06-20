# ARMCtrl_Arduino_OpenCV

本專案為一套整合影像辨識與 Arduino 控制的機器手臂控制系統，可透過本地端攝影機或遠端影像串流，辨識紅色與藍色的「三角形」與「方形」目標物，並傳送指令給機器手臂執行對應動作。

---

## 📦 安裝必要模組

請先安裝 `requirements.txt` 中列出的必要模組（建議使用 Python 3.8+）

```bash
pip install -r requirements.txt
```

這將會安裝 `opencv-python`, `numpy`, 和 `pyserial`。

---

## 🔧 系統架構

- **`main_local.py`**: 本地端主程式。直接從本機攝影機擷取影像，並提供一個包含 HSV 即時調整功能的圖形化介面，適合用於偵錯與色彩校正。
- **`main_stream.py`**: 串流主程式。接收來自 MediaMTX 伺服器的 RTSP 串流影像，進行辨識後將結果影像推播回去，適合用於遠端或無頭部屬。
- **`utils/`**: 核心功能模組
    - **`app_core.py`**: 包含應用程式共用的核心邏輯，如攝影機初始化、手臂控制器介面、影像處理與控制流程等。
    - **`vision_processing/`**: 視覺辨識相關模組。
        - `detector.py`: 負責從影像中偵測目標物（顏色、形狀）。
        - `config.py`: 載入並管理顏色設定 (`color_config.json`)。
        - `state_manager.py`: 判斷偵測結果的穩定性，避免指令頻繁觸發。
    - **`arm_controller/`**: 機器手臂控制相關模組 (目前為 `pi_gpio_controller.py`，可擴充)。
    - **`stream_pusher/` & `stream_receiver/`**: 處理影像串流的接收與推播。
- **`mediamtx`**: 內建的 MediaMTX 伺服器，用於建立 RTSP 影像串流。

---

## 🎯 目標物偵測邏輯

1.  從本地攝影機 (`main_local.py`) 或 RTSP 串流 (`main_stream.py`) 擷取影像。
2.  轉換至 HSV 色彩空間。
3.  根據 `utils/vision_processing/color_config.json` 中定義的 HSV 門檻產生遮罩。
4.  偵測輪廓並判斷形狀（三角形、方形）。
5.  根據顏色與形狀的組合，從 `action_map` 找出對應的動作指令。
6.  透過 `StateManager` 確認偵測結果穩定後，經由 Serial Port 傳送指令給 Arduino。

---

## 🎮 使用方法

### 1. (可選) 進行 HSV 色彩校正

若需調整顏色辨識的範圍，請執行 `main_local.py`。

```bash
python main_local.py
```

程式啟動後會出現三個視窗：
- **ARMCtrl Demo**: 顯示原始影像、遮罩影像與辨識結果。
- **Controls**: 控制面板。
    - **Tune Red / Tune Blue**: 點擊按鈕以切換要調整的顏色（紅色或藍色）。當前調整的顏色會顯示在面板頂部。
    - **Save Settings**: 儲存當前在 `HSV Adjustments` 視窗中調整好的 HSV 值到 `color_config.json`。
    - **Quit**: 關閉程式。
- **HSV Adjustments**: HSV 滑桿調整視窗。拖動滑桿可即時預覽對應顏色的遮罩效果。

⚠️ **注意：儲存設定時，會根據當前選擇的調整顏色（Tune Red/Blue）覆寫 `color_config.json` 中對應的數值。**

### 2. 啟動主系統

#### 模式一：本地端執行 (含 UI)

直接執行 `main_local.py` 即可啟動，適用於開發與測試。

```bash
python main_local.py --serial_port <你的 COM port>
```
(若不指定 `serial_port`，程式將不會嘗試連接 Arduino)

#### 模式二：串流模式 (無 UI)

此模式需要 MediaMTX 伺服器。

1.  **啟動 MediaMTX 伺服器**:
    (根據你的作業系統執行對應的執行檔)
    ```bash
    ./utils/bin/mediamtx
    ```
2.  **啟動影像來源**:
    你需要一個影像來源將 RTSP 串流推播至 MediaMTX。例如，使用 ffmpeg 或其他攝影機。
3.  **執行 `main_stream.py`**:
    ```bash
    python main_stream.py --serial_port <你的 COM port>
    ```
    程式會從 MediaMTX 接收影像，處理後再將結果畫面推播回去。

---

## 📁 檔案結構

```
ARMCtrl_Arduino_OpenCV/
├── main_local.py             # 本地端主程式 (含UI與HSV調整)
├── main_stream.py            # 串流模式主程式
├── requirements.txt          # Python 依賴模組
├── README.md                 # 本說明文件
└── utils/
    ├── __init__.py
    ├── app_core.py           # 應用程式核心邏輯
    ├── arm_controller/       # 手臂控制模組
    │   └── pi_gpio_controller.py
    ├── bin/                  # 外部執行檔
    │   └── mediamtx
    ├── stream_pusher/        # 串流推播模組
    │   └── rtsp_pusher.py
    ├── stream_receiver/      # 串流接收模組
    │   └── rtsp_receiver.py
    └── vision_processing/    # 視覺處理模組
        ├── __init__.py
        ├── color_config.json # HSV 顏色設定檔
        ├── config.py         # 設定檔讀取
        ├── detector.py       # 目標偵測器
        ├── confidence_scorer.py # 信心分數計算
        ├── feature_validator.py # 輪廓特徵驗證
        ├── state_manager.py  # 狀態穩定管理器
        └── ui_basic.py       # 基礎 UI 顯示
```

---

## 🧠 特殊功能

- **雙模式操作**: 支援本地端即時除錯與遠端串流部署。
- **圖形化校正介面**: 內建於 `main_local.py` 的控制面板與 HSV 滑桿，無需執行額外腳本。
- **狀態穩定機制**: 透過 `StateManager` 避免因畫面閃爍或短暫誤判而傳送錯誤指令。
- **模組化設計**: 將視覺處理、手臂控制、串流管理等功能拆分，易於擴充與維護。
- **整合 MediaMTX**: 內建 RTSP 伺服器，簡化串流部署流程。

---

## 👨‍💻 作者

本專案由 [ray-uncoding](https://github.com/ray-uncoding) 製作。
