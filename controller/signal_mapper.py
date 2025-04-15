import json
import os

SIGNAL_PATH = os.path.join(os.path.dirname(__file__), "..", "signal_mapping.json")
SIGNAL_PATH = os.path.abspath(SIGNAL_PATH)


def load_signal_map():
    if not os.path.exists(SIGNAL_PATH):
        return {}
    with open(SIGNAL_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 檢查是否每個 slot 都有 hsv 欄位，若沒有則補上
    modified = False
    for code in data:
        if "hsv" not in data[code]:
            data[code]["hsv"] = {"H": [0, 0], "S": [0, 0], "V": [0, 0]}
            modified = True
    if modified:
        save_signal_map(data)

    return data


def save_signal_map(data):
    with open(SIGNAL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_signal_code(label, shape):
    signal_map = load_signal_map()
    for code, conf in signal_map.items():
        if conf.get("label") == label and conf.get("shape") == shape:
            return code
    return None


def get_all_slots():
    return load_signal_map()


def get_slot_hsv(code):
    data = load_signal_map()
    if code in data and "hsv" in data[code]:
        return data[code]["hsv"]
    return {"H": [0, 0], "S": [0, 0], "V": [0, 0]}


def update_slot(code, label, shape, hsv_range=None):
    data = load_signal_map()
    if code not in data:
        return False
    data[code]["label"] = label
    data[code]["shape"] = shape
    if hsv_range:
        data[code]["hsv"] = hsv_range
    save_signal_map(data)
    return True


def init_empty_slot_mapping():
    if not os.path.exists(SIGNAL_PATH):
        default = {}
        for code in "ABCDEFGHIJKL":
            default[code] = {
                "label": "",
                "shape": "",
                "hsv": {"H": [0, 0], "S": [0, 0], "V": [0, 0]}
            }
        save_signal_map(default)