from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QListWidget, QGridLayout, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from qtrangeslider import QRangeSlider
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARMCtrl OpenCV UI")
        self.setGeometry(100, 100, 1400, 850)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout()
        self.central_widget.setLayout(main_layout)

        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        main_layout.addLayout(top_layout, 8)
        main_layout.addLayout(bottom_layout, 1)

        # === 左側控制區 ===
        control_layout = QVBoxLayout()

        self.mode_switch_btn = QPushButton("切換至 HSV 編輯模式")
        self.start_btn = QPushButton("開始辨識")
        self.pause_btn = QPushButton("暫停辨識")
        self.help_btn = QPushButton("❓ HSV 說明")
        self.help_btn.clicked.connect(self.show_help_dialog)

        control_layout.addWidget(self.mode_switch_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.help_btn)

        # 即時顏色預覽
        preview_row = QHBoxLayout()
        self.preview_label = QLabel("即時預覽顏色：")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(180, 20)
        preview_row.addWidget(self.preview_label)
        preview_row.addWidget(self.color_preview)
        control_layout.addLayout(preview_row)

        # HSV 控制拉條
        self.h_slider = QRangeSlider(Qt.Horizontal)
        self.h_slider.setRange(0, 179)
        self.h_slider.setValue((0, 179))
        self.h_slider_label = QLabel("H 範圍： [0 ~ 179]")
        self.h_slider.valueChanged.connect(lambda: self.update_range_label(self.h_slider, self.h_slider_label, 'H'))
        self.h_slider.valueChanged.connect(self.update_color_preview)

        self.s_slider = QRangeSlider(Qt.Horizontal)
        self.s_slider.setRange(0, 255)
        self.s_slider.setValue((0, 255))
        self.s_slider_label = QLabel("S 範圍： [0 ~ 255]")
        self.s_slider.valueChanged.connect(lambda: self.update_range_label(self.s_slider, self.s_slider_label, 'S'))
        self.s_slider.valueChanged.connect(self.update_color_preview)

        self.v_slider = QRangeSlider(Qt.Horizontal)
        self.v_slider.setRange(0, 255)
        self.v_slider.setValue((0, 255))
        self.v_slider_label = QLabel("V 範圍： [0 ~ 255]")
        self.v_slider.valueChanged.connect(lambda: self.update_range_label(self.v_slider, self.v_slider_label, 'V'))
        self.v_slider.valueChanged.connect(self.update_color_preview)

        self.name_input = QLineEdit("color_name")
        self.save_btn = QPushButton("✅ 確認紀錄")
        self.delete_btn = QPushButton("❌ 刪除紀錄")

        hsv_layout = QVBoxLayout()
        hsv_layout.addWidget(self.h_slider_label)
        hsv_layout.addWidget(self.h_slider)
        hsv_layout.addWidget(self.s_slider_label)
        hsv_layout.addWidget(self.s_slider)
        hsv_layout.addWidget(self.v_slider_label)
        hsv_layout.addWidget(self.v_slider)
        hsv_layout.addWidget(QLabel("命名："))
        hsv_layout.addWidget(self.name_input)
        hsv_layout.addWidget(self.save_btn)
        hsv_layout.addWidget(self.delete_btn)

        control_group = QVBoxLayout()
        control_group.addLayout(control_layout)
        control_group.addSpacing(20)
        control_group.addLayout(hsv_layout)

        # === 中間畫面顯示區 ===
        self.live_view_label = QLabel("[即時畫面區]")
        self.live_view_label.setFixedSize(640, 360)
        self.live_view_label.setStyleSheet("background-color: #ddd; border: 1px solid black;")

        self.filtered_view_label = QLabel("[過濾畫面區]")
        self.filtered_view_label.setFixedSize(640, 360)
        self.filtered_view_label.setStyleSheet("background-color: #ccc; border: 1px solid black;")

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.live_view_label)
        video_layout.addWidget(self.filtered_view_label)

        # === 右側色彩紀錄欄 ===
        self.color_list = QListWidget()
        self.color_list.setFixedWidth(250)

        # === 提示欄 ===
        self.tip_label = QLabel("🛈 提示：請先切換至 HSV 模式，調整滑條以觀察畫面效果，並輸入名稱後儲存。")
        self.tip_label.setStyleSheet("color: #444; font-size: 14px; padding: 5px;")

        # === 加入到畫面 ===
        top_layout.addLayout(control_group, 1)
        top_layout.addLayout(video_layout, 2)
        top_layout.addWidget(self.color_list, 1)
        bottom_layout.addWidget(self.tip_label)

        self.update_color_preview()

    def update_range_label(self, slider, label, prefix):
        low, high = slider.value()
        label.setText(f"{prefix} 範圍： [{low} ~ {high}]")

    def update_color_preview(self):
        h_low, h_high = self.h_slider.value()
        s_low, s_high = self.s_slider.value()
        v_low, v_high = self.v_slider.value()
        width = 180
        pixmap = QPixmap(width, 20)
        painter = QPainter(pixmap)
        for i in range(width):
            ratio = i / (width - 1)
            h = int(h_low + ratio * (h_high - h_low))
            s = int(s_low + ratio * (s_high - s_low))
            v = int(v_low + ratio * (v_high - v_low))
            color = QColor.fromHsv(h, s, v)
            painter.setPen(color)
            painter.drawLine(i, 0, i, 20)
        painter.end()
        self.color_preview.setPixmap(pixmap)

    def show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("HSV 色彩模型簡介")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setFixedSize(400, 300)
        layout = QVBoxLayout(dialog)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setText("""
[HSV 色彩模型簡介]

- H（Hue 色相）：表示顏色的種類，如紅色、藍色、綠色等，範圍為 0~179。
- S（Saturation 飽和度）：表示顏色的純度，數值越高顏色越鮮豔。
- V（Value 明度）：表示顏色的亮度，數值越高越明亮。

提示：
紅色 ≈ 0~10、藍色 ≈ 100~130、綠色 ≈ 40~80
        """)
        layout.addWidget(help_text)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())