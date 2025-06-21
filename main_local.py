#記錄點

# main_local.py
import cv2
import argparse
import numpy as np
from copy import deepcopy
from PIL import ImageFont, ImageDraw, Image

from utils.app_core import (
    add_common_arguments, 
    initialize_camera, 
    initialize_arm_controller, 
    process_frame_and_control_arm,
    cleanup_resources,
    StateManager 
)
from utils.vision_processing import config as vision_config

# --- 全域變數 ---
current_color_to_adjust = "Red"
current_action_from_buttons = None
live_color_ranges = {}
hsv_values = [[0,0,0],[179,255,255]]
dragging = None  # (idx, min_or_max) or None
ui_enabled = True  # 預設開啟UI

# --- UI 參數 ---
BUTTON_HEIGHT = 30
BUTTON_WIDTH = 180
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (100, 100, 100)
QUIT_BUTTON_COLOR = (50, 50, 150)
buttons_config = [
    {"rect": (20, 50, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "調整紅色", "action": "set_red", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 100, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "調整藍色", "action": "set_blue", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 150, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "調整綠色", "action": "set_green", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 200, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "儲存設定", "action": "save", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 250, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "自動模式", "action": "auto_mode", "color": BUTTON_COLOR, "text_color": TEXT_COLOR},
    {"rect": (20, 300, BUTTON_WIDTH, BUTTON_HEIGHT), "text": "離開", "action": "quit", "color": QUIT_BUTTON_COLOR, "text_color": TEXT_COLOR},
]
# HSV條參數
HSV_BAR_X = 970
HSV_BAR_Y = 60
HSV_BAR_W = 250
HSV_BAR_H = 20
HSV_BAR_GAP = 50

def draw_hsv_panel(hsv_values, current_color):
    panel = np.full((180, 320, 3), 80, dtype=np.uint8)
    cv2.putText(panel, f"HSV Adjust ({current_color})", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
    labels = ["H", "S", "V"]
    for i, l in enumerate(labels):
        y = 60 + i*35
        cv2.putText(panel, f"{l}_min: {hsv_values[0][i]:3d}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
        cv2.putText(panel, f"{l}_max: {hsv_values[1][i]:3d}", (160, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
    return panel

def draw_buttons_panel_img(current_color):
    # 英文顏色對應中文
    color_map = {"Red": "紅色", "Blue": "藍色", "Green": "綠色"}
    btn_count = len(buttons_config)
    btn_h = 40
    btn_gap = 15
    top_margin = 50
    bottom_margin = 20
    panel_h = top_margin + btn_count * btn_h + (btn_count - 1) * btn_gap + bottom_margin
    panel_w = 320
    panel = np.full((panel_h, panel_w, 3), (220, 220, 220), dtype=np.uint8)
    # 中文顏色顯示
    ch_color = color_map.get(current_color, current_color)
    adjust_text = f"調整目標：{ch_color}"
    # 置中計算
    font_size = 28
    font_path = "chinese.ttf"
    # 先用 PIL 計算文字寬度
    from PIL import ImageFont
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(adjust_text)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_x = (panel_w - text_w) // 2
    text_y = 15
    panel = draw_chinese_text(panel, adjust_text, (text_x, text_y), font_size=font_size, color=(0,0,0), font_path=font_path)

    btn_w = int(panel_w * 0.75)
    btn_x = int((panel_w - btn_w) / 2)
    btn_y = top_margin
    for idx, button in enumerate(buttons_config):
        y = btn_y + idx * (btn_h + btn_gap)
        color = button["color"]
        cv2.rectangle(panel, (btn_x, y), (btn_x + btn_w, y + btn_h), color, -1)
        # 置中計算
        font_size_btn = 22
        font_btn = ImageFont.truetype(font_path, font_size_btn)
        bbox_btn = font_btn.getbbox(button["text"])
        text_w_btn, text_h_btn = bbox_btn[2] - bbox_btn[0], bbox_btn[3] - bbox_btn[1]
        text_x_btn = btn_x + (btn_w - text_w_btn) // 2
        text_y_btn = y + (btn_h - text_h_btn) // 2
        panel = draw_chinese_text(
            panel,
            button["text"],
            (text_x_btn, text_y_btn),
            font_size=font_size_btn,
            color=button.get("text_color", (0,0,0)),
            font_path=font_path
        )
    return panel

def draw_chinese_text(img, text, pos, font_size=32, color=(0,0,0), font_path="chinese.ttf"):
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(font_path, font_size)
    draw.text(pos, text, font=font, fill=(color[2], color[1], color[0]))
    return np.array(img_pil)

def draw_combined_ui(main_img, hsv_values, current_color, mask=None):
    canvas_h, canvas_w = 720, 1280
    canvas = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)  # 背景白色

    # 相對位置與大小
    main_x = int(canvas_w * 0.015)
    main_y = int(canvas_h * 0.028)
    main_w = int(canvas_w * 0.7)
    main_h = int(canvas_h * 0.47)

    mask_x = main_x
    mask_y = main_y + main_h + int(canvas_h * 0.02)
    mask_w = main_w
    mask_h = main_h

    hsv_panel_x = int(canvas_w * 0.75)
    hsv_panel_y = int(canvas_h * 0.08)  # 互動區一致
    hsv_panel_w = int(canvas_w * 0.22)
    hsv_panel_h = int(canvas_h * 0.25)

    ctrl_panel_x = hsv_panel_x
    ctrl_panel_y = int(canvas_h * 0.48)

    # 左上主畫面
    main_img_resized = cv2.resize(main_img, (main_w, main_h))
    canvas[main_y:main_y+main_h, main_x:main_x+main_w] = main_img_resized
    canvas = draw_chinese_text(canvas, "攝影機", (main_x+10, main_y+10), font_size=32, color=(255,255,255))

    # 左下mask
    if mask is not None:
        mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) if len(mask.shape)==2 else mask
        mask_resized = cv2.resize(mask_color, (mask_w, mask_h))
        canvas[mask_y:mask_y+mask_h, mask_x:mask_x+mask_w] = mask_resized
        canvas = draw_chinese_text(canvas, "遮罩", (mask_x+10, mask_y+15), font_size=32, color=(255,255,255))

    # 右上HSV panel
    # 將 "HSV調整" 文字往上提 15px
    canvas = draw_chinese_text(canvas, "HSV調整", (hsv_panel_x, hsv_panel_y - 15), font_size=28, color=(0,0,0))
    cv2.rectangle(canvas, (hsv_panel_x, hsv_panel_y+10), (hsv_panel_x+hsv_panel_w, hsv_panel_y+10+hsv_panel_h), (220,220,220), -1)  # 淡灰
    labels = ["H", "S", "V"]
    maxs = [179, 255, 255]
    bar_x = hsv_panel_x + int(hsv_panel_w * 0.07)
    bar_w = int(hsv_panel_w * 0.8)
    bar_h = int(hsv_panel_h * 0.13)
    for i, l in enumerate(labels):
        y = hsv_panel_y + 40 + i*int(hsv_panel_h * 0.28)
        cv2.rectangle(canvas, (bar_x, y), (bar_x+bar_w, y+bar_h), (180,180,180), -1)  # 更淡灰
        vmin = int(hsv_values[0][i]/maxs[i]*bar_w)
        vmax = int(hsv_values[1][i]/maxs[i]*bar_w)
        cv2.rectangle(canvas, (bar_x+vmin, y), (bar_x+vmax, y+bar_h), (0,0,0), -1)  # 黑色區間
        cv2.rectangle(canvas, (bar_x+vmin-5, y-5), (bar_x+vmin+5, y+bar_h+5), (50,50,50), -1)  # 深灰滑塊
        cv2.rectangle(canvas, (bar_x+vmax-5, y-5), (bar_x+vmax+5, y+bar_h+5), (100,100,100), -1)  # 深灰滑塊
        cv2.putText(canvas, f"{l}_min:{hsv_values[0][i]:3d}", (bar_x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1)
        cv2.putText(canvas, f"{l}_max:{hsv_values[1][i]:3d}", (bar_x+int(bar_w*0.6), y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1)

    # 右下Control panel
    ctrl_panel = draw_buttons_panel_img(current_color, panel_w=hsv_panel_w)
    ctrl_h, ctrl_w = ctrl_panel.shape[:2]
    cv2.rectangle(canvas, (ctrl_panel_x, ctrl_panel_y), (ctrl_panel_x+ctrl_w, ctrl_panel_y+ctrl_h), (220,220,220), -1)
    # 將 "控制面板" 文字往上提 15px
    canvas = draw_chinese_text(canvas, "控制面板", (ctrl_panel_x, ctrl_panel_y - 35), font_size=28, color=(0,0,0))
    # 修正：確保不超出 canvas
    y1 = int(ctrl_panel_y)
    y2 = min(y1 + ctrl_h, canvas.shape[0])
    x1 = int(ctrl_panel_x)
    x2 = min(x1 + ctrl_w, canvas.shape[1])
    panel_crop = ctrl_panel[:y2-y1, :x2-x1]
    canvas[y1:y2, x1:x2] = panel_crop

    return canvas

def draw_buttons_panel_img(current_color, panel_w=320, panel_h=None):
    # 英文顏色對應中文
    color_map = {"Red": "紅色", "Blue": "藍色", "Green": "綠色"}
    btn_count = len(buttons_config)
    btn_h = 40
    btn_gap = 15
    top_margin = 50
    bottom_margin = 20
    if panel_h is None:
        panel_h = top_margin + btn_count * btn_h + (btn_count - 1) * btn_gap + bottom_margin
    panel = np.full((panel_h, panel_w, 3), (220, 220, 220), dtype=np.uint8)
    # 中文顏色顯示
    ch_color = color_map.get(current_color, current_color)
    adjust_text = f"調整目標：{ch_color}"
    # 置中計算
    font_size = 28
    font_path = "chinese.ttf"
    # 先用 PIL 計算文字寬度
    from PIL import ImageFont
    font = ImageFont.truetype(font_path, font_size)
    bbox = font.getbbox(adjust_text)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_x = (panel_w - text_w) // 2
    text_y = 15
    panel = draw_chinese_text(panel, adjust_text, (text_x, text_y), font_size=font_size, color=(0,0,0), font_path=font_path)

    btn_w = int(panel_w * 0.75)
    btn_x = int((panel_w - btn_w) / 2)
    btn_y = top_margin
    for idx, button in enumerate(buttons_config):
        y = btn_y + idx * (btn_h + btn_gap)
        color = button["color"]
        cv2.rectangle(panel, (btn_x, y), (btn_x + btn_w, y + btn_h), color, -1)
        # 置中計算
        font_size_btn = 22
        font_btn = ImageFont.truetype(font_path, font_size_btn)
        bbox_btn = font_btn.getbbox(button["text"])
        text_w_btn, text_h_btn = bbox_btn[2] - bbox_btn[0], bbox_btn[3] - bbox_btn[1]
        text_x_btn = btn_x + (btn_w - text_w_btn) // 2
        text_y_btn = y + (btn_h - text_h_btn) // 2
        panel = draw_chinese_text(
            panel,
            button["text"],
            (text_x_btn, text_y_btn),
            font_size=font_size_btn,
            color=button.get("text_color", (0,0,0)),
            font_path=font_path
        )
    return panel

def on_all_in_one_mouse(event, x, y, flags, param):
    global current_action_from_buttons, dragging, hsv_values
    # 與 draw_combined_ui 完全一致的相對座標
    canvas_h, canvas_w = 720, 1280

    # 右下按鈕互動區
    hsv_panel_w = int(canvas_w * 0.22)
    ctrl_panel_x = int(canvas_w * 0.75)
    ctrl_panel_y = int(canvas_h * 0.48)  # 這裡也要同步
    panel_w = hsv_panel_w
    # 與 draw_buttons_panel_img 保持一致
    btn_count = len(buttons_config)
    btn_h = 40
    btn_gap = 15
    top_margin = 50
    bottom_margin = 20
    panel_h = top_margin + btn_count * btn_h + (btn_count - 1) * btn_gap + bottom_margin
    btn_w = int(panel_w * 0.75)
    btn_x = int((panel_w - btn_w) / 2)
    btn_y = top_margin
    for idx, button in enumerate(buttons_config):
        y_btn = btn_y + idx * (btn_h + btn_gap)
        abs_x1 = ctrl_panel_x + btn_x
        abs_y1 = ctrl_panel_y + y_btn
        abs_x2 = abs_x1 + btn_w
        abs_y2 = abs_y1 + btn_h
        if event == cv2.EVENT_LBUTTONDOWN:
            if abs_x1 <= x < abs_x2 and abs_y1 <= y < abs_y2:
                current_action_from_buttons = button["action"]
                return

    # HSV滑動條互動區（完全用相對座標）
    hsv_panel_x = int(canvas_w * 0.75)
    hsv_panel_y = int(canvas_h * 0.08)
    hsv_panel_w = int(canvas_w * 0.22)
    hsv_panel_h = int(canvas_h * 0.25)
    bar_x = hsv_panel_x + int(hsv_panel_w * 0.07)
    bar_w = int(hsv_panel_w * 0.8)
    bar_h = int(hsv_panel_h * 0.13)
    for i in range(3):
        y_bar = hsv_panel_y + 40 + i*int(hsv_panel_h * 0.28)
        min_rect = (bar_x+int(hsv_values[0][i]/[179,255,255][i]*bar_w)-5, y_bar-5,
                    bar_x+int(hsv_values[0][i]/[179,255,255][i]*bar_w)+5, y_bar+bar_h+5)
        max_rect = (bar_x+int(hsv_values[1][i]/[179,255,255][i]*bar_w)-5, y_bar-5,
                    bar_x+int(hsv_values[1][i]/[179,255,255][i]*bar_w)+5, y_bar+bar_h+5)
        if event == cv2.EVENT_LBUTTONDOWN:
            if min_rect[0] <= x <= min_rect[2] and min_rect[1] <= y <= min_rect[3]:
                dragging = (i, 'min')
                return
            if max_rect[0] <= x <= max_rect[2] and max_rect[1] <= y <= max_rect[3]:
                dragging = (i, 'max')
                return
        elif event == cv2.EVENT_LBUTTONUP:
            dragging = None
        elif event == cv2.EVENT_MOUSEMOVE and dragging is not None and flags & cv2.EVENT_FLAG_LBUTTON:
            idx, which = dragging
            rel = x - bar_x
            rel = max(0, min(bar_w, rel))
            value = int(rel/max(1,bar_w)*[179,255,255][idx])
            if which == 'min':
                hsv_values[0][idx] = min(value, hsv_values[1][idx]-1)
            else:
                hsv_values[1][idx] = max(value, hsv_values[0][idx]+1)

def show_auto_mode_confirm(live_color_ranges):
    panel_w, panel_h = 500, 320
    panel = np.full((panel_h, panel_w, 3), 240, dtype=np.uint8)
    panel = draw_chinese_text(panel, "請確認以下各顏色之HSV資訊。", (20, 35), font_size=32, color=(0,0,0))
    y = 70
    for color, hsv in live_color_ranges.items():
        ch_color = color
        if color == "Red":
            ch_color = "紅色"
        elif color == "Blue":
            ch_color = "藍色"
        elif color == "Green":
            ch_color = "綠色"
        panel = draw_chinese_text(
            panel,
            f"{ch_color}: [{hsv[0][0]},{hsv[0][1]},{hsv[0][2]}] ~ [{hsv[1][0]},{hsv[1][1]},{hsv[1][2]}]",
            (20, y), font_size=24, color=(0,0,0)
        )
        y += 35
    panel = draw_chinese_text(panel, "按 Y 確認，N 取消", (20, panel_h-60), font_size=28, color=(0,0,0))
    panel = draw_chinese_text(panel, "確認後 UI畫面即消失!", (20, panel_h-30), font_size=24, color=(255,0,0))
    cv2.imshow("Auto Mode confirm", panel)
    while True:
        key = cv2.waitKey(0)
        if key in [ord('y'), ord('Y')]:
            cv2.destroyWindow("Auto Mode confirm")
            return True
        elif key in [ord('n'), ord('N'), 27]:  # 27=ESC
            cv2.destroyWindow("Auto Mode confirm")
            return False

def main():
    global current_color_to_adjust, current_action_from_buttons, live_color_ranges, hsv_values, ui_enabled
    parser = argparse.ArgumentParser(description="ARMCtrl OpenCV Application - Local Display Mode with HSV Adjustment")
    parser = add_common_arguments(parser)
    parser.add_argument('--show_debug_masks', action=argparse.BooleanOptionalAction, default=False, help="Show individual color mask windows for debugging.")
    args = parser.parse_args()
    cap, frame_width, frame_height, fps = initialize_camera(args.camera_index)
    if not cap:
        return
    arm_controller = initialize_arm_controller(args)
    state_manager = StateManager()
    live_color_ranges = deepcopy(vision_config.color_ranges)
    if not live_color_ranges or current_color_to_adjust not in live_color_ranges:
        initial_hsv_for_trackbar = vision_config.DEFAULT_COLOR_RANGES.get(current_color_to_adjust, [[0,0,0],[179,255,255]])
    else:
        initial_hsv_for_trackbar = live_color_ranges[current_color_to_adjust]
    hsv_values = deepcopy(initial_hsv_for_trackbar)
    cv2.namedWindow("ARMCtrl-ALL-IN-ONE")
    cv2.setMouseCallback("ARMCtrl-ALL-IN-ONE", on_all_in_one_mouse)
    print("[MainLocal] System running. Use UI buttons or press 'q' in the OpenCV window to quit.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # 更新 live_color_ranges
            live_color_ranges[current_color_to_adjust] = deepcopy(hsv_values)
            result_frame, labels, mask = process_frame_and_control_arm(
                frame, state_manager, arm_controller, live_color_ranges,
                show_debug_windows=args.show_debug_masks
            )
            if ui_enabled:
                combined = draw_combined_ui(result_frame, hsv_values, current_color_to_adjust, mask)
                cv2.imshow("ARMCtrl-ALL-IN-ONE", combined)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
            # 按鈕動作
            if current_action_from_buttons == "save":
                vision_config.save_color_ranges(live_color_ranges)
                print("[MainLocal] Saved current HSV values for ALL colors to config.")
                current_action_from_buttons = None
            elif current_action_from_buttons == "set_red":
                current_color_to_adjust = "Red"
                hsv_values = deepcopy(live_color_ranges.get("Red", [[0,0,0],[179,255,255]]))
                current_action_from_buttons = None
            elif current_action_from_buttons == "set_blue":
                current_color_to_adjust = "Blue"
                hsv_values = deepcopy(live_color_ranges.get("Blue", [[100,100,100],[120,255,255]]))
                current_action_from_buttons = None
            elif current_action_from_buttons == "set_green":
                current_color_to_adjust = "Green"
                hsv_values = deepcopy(live_color_ranges.get("Green", [[40,100,100],[80,255,255]]))  # 預設綠色範圍
                current_action_from_buttons = None
            elif current_action_from_buttons == "quit":
                print("[MainLocal] Quit button pressed.")
                break
            elif current_action_from_buttons == "auto_mode":
                if show_auto_mode_confirm(live_color_ranges):
                    ui_enabled = False
                    cv2.destroyAllWindows()
                    print("[MainLocal] Entering headless (auto) mode, UI closed.")
                else:
                    print("[MainLocal] 取消進入自動模式。")
                current_action_from_buttons = None
            if not ui_enabled:
                # 無頭模式下可加自動退出條件或其他自動流程
                pass
    except KeyboardInterrupt:
        print("\n[MainLocal] Program interrupted by user (Ctrl+C).")
    finally:
        print("[MainLocal] Cleaning up resources...")
        cleanup_resources(cap, arm_controller)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
