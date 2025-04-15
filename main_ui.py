from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QComboBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from qtrangeslider import QRangeSlider
import sys
import numpy as np
import cv2

from core.camera_stream import CameraThread
from controller.hsv_editor import HSVEditor
from controller.auto_runner import AutoRunner
from controller.signal_mapper import get_all_slots, update_slot, init_empty_slot_mapping, get_slot_hsv
from core.serial_sender import init_serial
init_serial()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARMCtrl OpenCV v2")
        self.setGeometry(100, 100, 1500, 900)

        init_empty_slot_mapping()

        self.edit_mode = True
        self.auto_runner = AutoRunner()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.live_view = QLabel("[Live]")
        self.live_view.setFixedSize(640, 360)
        self.filtered_view = QLabel("[Filtered]")
        self.filtered_view.setFixedSize(640, 360)

        self.h_slider = QRangeSlider(Qt.Horizontal)
        self.h_slider.setRange(0, 179)
        self.s_slider = QRangeSlider(Qt.Horizontal)
        self.s_slider.setRange(0, 255)
        self.v_slider = QRangeSlider(Qt.Horizontal)
        self.v_slider.setRange(0, 255)

        self.h_label = QLabel("H 範圍：")
        self.s_label = QLabel("S 範圍：")
        self.v_label = QLabel("V 範圍：")

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(180, 20)

        self.mode_btn = QPushButton("切換至自動模式")
        self.mode_btn.clicked.connect(self.toggle_mode)

        self.editor = HSVEditor(
            self.h_slider, self.s_slider, self.v_slider,
            self.h_label, self.s_label, self.v_label,
            self.color_preview, None, None, None  # 不再需要命名/儲存/刪除控制
        )

        self.camera = CameraThread()
        self.camera.frame_updated.connect(self.update_view)
        self.camera.start()

        self.slot_panel = self.build_slot_editor()

        left = QVBoxLayout()
        left.addWidget(self.mode_btn)
        left.addWidget(self.h_label)
        left.addWidget(self.h_slider)
        left.addWidget(self.s_label)
        left.addWidget(self.s_slider)
        left.addWidget(self.v_label)
        left.addWidget(self.v_slider)
        left.addWidget(self.color_preview)

        mid = QVBoxLayout()
        mid.addWidget(self.live_view)
        mid.addWidget(self.filtered_view)

        right = QVBoxLayout()
        right.addWidget(self.slot_panel)

        top = QHBoxLayout()
        top.addLayout(left)
        top.addLayout(mid)
        top.addLayout(right)

        layout.addLayout(top)

    def build_slot_editor(self):
        group = QGroupBox("🔧 指令槽位對應設定區（A~L 對應 0001~1100）")
        layout = QFormLayout()
        self.slot_entries = {}

        slots = get_all_slots()
        for code in sorted(slots.keys()):
            row = QHBoxLayout()

            label_input = QLineEdit(slots[code].get("label", ""))
            shape_select = QComboBox()
            shape_select.addItems(["square", "triangle"])
            shape_select.setCurrentText(slots[code].get("shape", ""))

            apply_hsv_btn = QPushButton("← 套用 HSV")
            apply_hsv_btn.clicked.connect(lambda _, c=code, li=label_input, ss=shape_select:
                                     self.apply_current_hsv_to_slot(c, li, ss))

            hsv_display = QLabel(self.format_hsv_display(code))
            hsv_display.setStyleSheet("font-size: 11px; color: #555;")

            row.addWidget(label_input)
            row.addWidget(shape_select)
            row.addWidget(apply_hsv_btn)
            row.addWidget(hsv_display)

            layout.addRow(QLabel(f"Slot {code} (指令碼)"), row)
            self.slot_entries[code] = (label_input, shape_select, hsv_display)

        group.setLayout(layout)
        return group

    def apply_current_hsv_to_slot(self, code, label_input, shape_select):
        label = label_input.text()
        shape = shape_select.currentText()

        hsv_range = {
            "H": list(self.h_slider.value()),
            "S": list(self.s_slider.value()),
            "V": list(self.v_slider.value())
        }

        update_slot(code, label, shape, hsv_range)
        if code in self.slot_entries:
            self.slot_entries[code][2].setText(self.format_hsv_display(code))
        print(f"✅ 已儲存至 Slot {code}: {label}, {shape}, HSV={hsv_range}")

    def format_hsv_display(self, code):
        hsv = get_slot_hsv(code)
        return f"H: {hsv['H'][0]}~{hsv['H'][1]}  S: {hsv['S'][0]}~{hsv['S'][1]}  V: {hsv['V'][0]}~{hsv['V'][1]}"

    def toggle_mode(self):
        self.edit_mode = not self.edit_mode
        self.editor.set_enabled(self.edit_mode)
        self.auto_runner.set_enabled(not self.edit_mode)
        self.mode_btn.setText("切換至編輯模式" if not self.edit_mode else "切換至自動模式")

    def update_view(self, qimg):
        pix_live = QPixmap.fromImage(qimg).scaled(self.live_view.size(), Qt.KeepAspectRatio)
        self.live_view.setPixmap(pix_live)

        rgb_img = qimg.convertToFormat(QImage.Format_RGB888)
        w, h = rgb_img.width(), rgb_img.height()
        ptr = rgb_img.bits()
        ptr.setsize(rgb_img.byteCount())
        arr = np.array(ptr).reshape((h, w, 3))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        if self.edit_mode:
            hsv_range = {
                "H": list(self.h_slider.value()),
                "S": list(self.s_slider.value()),
                "V": list(self.v_slider.value())
            }
            from core.hsv_filter import apply_hsv_filter
            mask = apply_hsv_filter(bgr, hsv_range)
            mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
            img_out = mask_rgb
        else:
            img_out = self.auto_runner.process_frame(bgr)

        qimg2 = QImage(img_out.data, img_out.shape[1], img_out.shape[0],
                      img_out.shape[1] * 3, QImage.Format_RGB888)
        pix_filtered = QPixmap.fromImage(qimg2).scaled(self.filtered_view.size(), Qt.KeepAspectRatio)
        self.filtered_view.setPixmap(pix_filtered)

    def closeEvent(self, event):
        self.camera.stop()
        self.auto_runner.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())