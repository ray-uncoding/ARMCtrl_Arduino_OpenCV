# utils/vision_processing/state_manager.py

from collections import deque, Counter

class StateManager:
    def __init__(self, buffer_size=5, stable_threshold=3):
        self.buffer = deque(maxlen=buffer_size)
        self.stable_threshold = stable_threshold
        self.last_sent_label = None
        self.locked = False # This attribute was present but not used, consider if needed

    def update(self, new_label):
        self.buffer.append(new_label)

    def get_stable_label(self):
        if len(self.buffer) < self.buffer.maxlen:
            return None  # Not enough data yet

        label_counts = Counter(self.buffer)
        if not label_counts: # Handle empty buffer case after initialization
            return None
            
        most_common, count = label_counts.most_common(1)[0]

        if count >= self.stable_threshold and most_common != self.last_sent_label and most_common is not None:
            self.last_sent_label = most_common
            return most_common

        return None
