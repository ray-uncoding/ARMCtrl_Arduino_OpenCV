import json
import os


def load_all_colors(filepath):
    """載入整份 HSV 色彩資料（dict 格式）"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_color(filepath, name, hsv_data):
    """儲存單筆 HSV 色彩（如已存在則覆蓋）"""
    data = load_all_colors(filepath)
    data[name] = hsv_data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_color(filepath, name):
    """刪除指定色彩紀錄"""
    data = load_all_colors(filepath)
    if name in data:
        del data[name]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def color_exists(filepath, name):
    """檢查指定顏色是否已存在"""
    data = load_all_colors(filepath)
    return name in data


# 測試用範例（可刪除）
if __name__ == "__main__":
    test_path = "color_db.json"
    sample_data = {"H": [0, 10], "S": [150, 255], "V": [150, 255]}
    save_color(test_path, "red_box", sample_data)
    print(load_all_colors(test_path))
    print("是否存在 red_box:", color_exists(test_path, "red_box"))
    delete_color(test_path, "red_box")
    print("刪除後:", load_all_colors(test_path))