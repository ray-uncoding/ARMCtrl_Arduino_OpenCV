# ARMCtrl_Arduino_OpenCV

本專案為一套整合 Arduino 控制與 OpenCV 影像辨識的自動觸發系統，透過自訂色彩與形狀條件，達到視覺驅動的繼電器控制。

---

## 📦 系統架構總覽

```text
ARMCtrl_Arduino_OpenCV
├── main_ui.py                # 主介面，整合影像顯示、HSV 調整與 Slot 編輯
├── signal_mapping.json       # 12 組槽位對應設定檔（A~L）
├── controller/
│   ├── auto_runner.py        # 自動模式下影像處理與傳送邏輯
│   ├── hsv_editor.py         # HSV 調整與滑條控制模組
│   └── signal_mapper.py      # 讀寫 Slot 設定檔，並轉換條件為對應指令碼
├── core/
│   ├── camera_stream.py      # 攝影機串流執行緒
│   ├── hsv_filter.py         # 運用 HSV 遮罩處理影像
│   ├── object_detector.py    # 輪廓形狀辨識（支援 square / triangle）
│   └── serial_sender.py      # 傳送 A~L 至 Arduino 控制繼電器
└── arduino2arm/
    └── arduino_python.ino    # 接收 A~L 指令碼並控制繼電器
```

---

## 🚀 功能特色

- ✅ 實時 HSV 調整並可套用至任意指令槽位
- ✅ 每組槽位包含：名稱、自訂形狀、HSV 範圍與對應字元（A~L）
- ✅ 自動模式下辨識指定顏色 + 形狀 → 傳送代碼給 Arduino 控制
- ✅ 支援簡易輪廓形狀辨識（方形 / 三角形）
- ✅ 統一資料儲存格式，容易備份與匯出

---

## 🔧 如何啟動

```bash
pip install -r requirements.txt
python main_ui.py
```

系統將：
1. 開啟主視窗
2. 自動初始化 `signal_mapping.json`
3. 自動連接 Arduino（支援自動搜尋序列埠）

---

## 🧪 測試方式

- 點選「切換至自動模式」
- 放入先前設定好的顏色與形狀目標
- 當條件符合，即會透過 Serial 傳送對應信號（如 A~L）

---

## 📌 注意事項

- Arduino 腳位需正確接上四路繼電器模組，並撰寫相應接收程式
- 若序列埠找不到裝置，請確認驅動已安裝且 COM port 無誤
- 每次僅允許最多 12 組設定，對應至指令碼 A~L（0001~1100）

---

## 👨‍💻 作者與貢獻

本專案由 [@ray-uncoding](https://github.com/ray-uncoding) 設計與開發，
如有建議或錯誤回報，歡迎開啟 issue 或提出 pull request 🙌
