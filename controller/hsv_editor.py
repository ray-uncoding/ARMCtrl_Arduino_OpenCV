# hsv_editor.py（修正：允許不帶 name_input, save_btn, delete_btn）

class HSVEditor:
    def __init__(self, h_slider, s_slider, v_slider,
                 h_label, s_label, v_label,
                 color_preview,
                 name_input=None, save_btn=None, delete_btn=None):

        self.h_slider = h_slider
        self.s_slider = s_slider
        self.v_slider = v_slider

        self.h_label = h_label
        self.s_label = s_label
        self.v_label = v_label

        self.color_preview = color_preview

        self.name_input = name_input
        self.save_btn = save_btn
        self.delete_btn = delete_btn

        self._connect()

    def _connect(self):
        self.h_slider.valueChanged.connect(self.update_label_and_preview)
        self.s_slider.valueChanged.connect(self.update_label_and_preview)
        self.v_slider.valueChanged.connect(self.update_label_and_preview)

        if self.save_btn:
            self.save_btn.clicked.connect(self.save_color)
        if self.delete_btn:
            self.delete_btn.clicked.connect(self.delete_color)

    def update_label_and_preview(self):
        h_min, h_max = self.h_slider.value()
        s_min, s_max = self.s_slider.value()
        v_min, v_max = self.v_slider.value()

        self.h_label.setText(f"H 範圍：[{h_min} ~ {h_max}]")
        self.s_label.setText(f"S 範圍：[{s_min} ~ {s_max}]")
        self.v_label.setText(f"V 範圍：[{v_min} ~ {v_max}]")

        avg_h = int((h_min + h_max) / 2)
        avg_s = int((s_min + s_max) / 2)
        avg_v = int((v_min + v_max) / 2)

        import cv2
        import numpy as np

        hsv = np.uint8([[[avg_h, avg_s, avg_v]]])
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0][0]
        r, g, b = bgr[2], bgr[1], bgr[0]

        self.color_preview.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid gray;")

    def set_enabled(self, enabled):
        self.h_slider.setEnabled(enabled)
        self.s_slider.setEnabled(enabled)
        self.v_slider.setEnabled(enabled)
        if self.name_input:
            self.name_input.setEnabled(enabled)
        if self.save_btn:
            self.save_btn.setEnabled(enabled)
        if self.delete_btn:
            self.delete_btn.setEnabled(enabled)

    def save_color(self):
        pass  # 已廢棄舊機制

    def delete_color(self):
        pass  # 已廢棄舊機制
