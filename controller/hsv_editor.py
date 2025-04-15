from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QMessageBox
from core.json_storage import load_all_colors, save_color, delete_color, color_exists

COLOR_DB_PATH = "color_db.json"

class HSVEditor:
    def __init__(self, h_slider, s_slider, v_slider,
                 h_label, s_label, v_label,
                 preview_label, name_input,
                 color_list_widget, save_btn, delete_btn):
        self.h_slider = h_slider
        self.s_slider = s_slider
        self.v_slider = v_slider
        self.h_label = h_label
        self.s_label = s_label
        self.v_label = v_label
        self.preview_label = preview_label
        self.name_input = name_input
        self.color_list_widget = color_list_widget
        self.save_btn = save_btn
        self.delete_btn = delete_btn

        self._connect_signals()
        self.update_preview()
        self.refresh_list()

    def _connect_signals(self):
        self.h_slider.valueChanged.connect(self.update_preview)
        self.s_slider.valueChanged.connect(self.update_preview)
        self.v_slider.valueChanged.connect(self.update_preview)
        self.color_list_widget.itemClicked.connect(self._on_item_clicked)
        self.save_btn.clicked.connect(self.save_color)
        self.delete_btn.clicked.connect(self.delete_color)

    def update_preview(self):
        h_low, h_high = self.h_slider.value()
        s_low, s_high = self.s_slider.value()
        v_low, v_high = self.v_slider.value()

        self.h_label.setText(f"H 範圍： [{h_low} ~ {h_high}]")
        self.s_label.setText(f"S 範圍： [{s_low} ~ {s_high}]")
        self.v_label.setText(f"V 範圍： [{v_low} ~ {v_high}]")

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
        self.preview_label.setPixmap(pixmap)

    def save_color(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(None, "名稱錯誤", "請輸入顏色名稱。")
            return
        hsv_data = {
            "H": list(self.h_slider.value()),
            "S": list(self.s_slider.value()),
            "V": list(self.v_slider.value())
        }
        if color_exists(COLOR_DB_PATH, name):
            reply = QMessageBox.question(None, "覆蓋確認", f"{name} 已存在，是否覆蓋？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        save_color(COLOR_DB_PATH, name, hsv_data)
        self.refresh_list()

    def delete_color(self):
        item = self.color_list_widget.currentItem()
        if item:
            name = item.text()
            reply = QMessageBox.question(None, "刪除確認", f"是否刪除 {name}？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                delete_color(COLOR_DB_PATH, name)
                self.refresh_list()

    def load_color(self, name):
        data = load_all_colors(COLOR_DB_PATH)
        if name in data:
            hsv = data[name]
            self.h_slider.setValue(tuple(hsv["H"]))
            self.s_slider.setValue(tuple(hsv["S"]))
            self.v_slider.setValue(tuple(hsv["V"]))
            self.name_input.setText(name)
            self.update_preview()

    def _on_item_clicked(self, item):
        self.load_color(item.text())

    def refresh_list(self):
        self.color_list_widget.clear()
        data = load_all_colors(COLOR_DB_PATH)
        for name in sorted(data.keys()):
            self.color_list_widget.addItem(name)

    def set_enabled(self, enabled: bool):
        self.h_slider.setEnabled(enabled)
        self.s_slider.setEnabled(enabled)
        self.v_slider.setEnabled(enabled)
        self.name_input.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.color_list_widget.setEnabled(enabled)