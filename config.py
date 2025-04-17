# config.py

# HSV 顏色範圍
color_ranges = {
    'Red':   ([0, 6, 185], [18, 255, 255]),
    'Blue': ([90, 85, 196], [116, 217, 255])
}

# 顏色 + 形狀 對應到控制代碼（訊號字元）
action_map = {
    ('Red', 'Triangle'):   'A',
    ('Red', 'Square'):     'B',
    ('Blue', 'Triangle'): 'C',
    ('Blue', 'Square'):   'D'
}
