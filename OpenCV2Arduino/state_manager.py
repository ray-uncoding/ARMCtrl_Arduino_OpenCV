# state_manager.py

from collections import deque, Counter

class StateManager:
    def __init__(self, buffer_size=5, stable_threshold=3):
        self.buffer = deque(maxlen=buffer_size)
        self.stable_threshold = stable_threshold
        self.last_sent_label = None
        self.locked = False

    def update(self, new_label):
        self.buffer.append(new_label)

    def get_stable_label(self):
        """ 回傳當前是否有穩定的 label，可以觸發動作 """
        if len(self.buffer) < self.buffer.maxlen:
            return None  # 資料還不夠

        label_counts = Counter(self.buffer)
        most_common, count = label_counts.most_common(1)[0]

        # 若穩定且不同於上一個傳送過的標籤
        if count >= self.stable_threshold and most_common != self.last_sent_label and most_common is not None:
            self.last_sent_label = most_common
            return most_common

        return None
