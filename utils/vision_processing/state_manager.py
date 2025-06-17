# utils/vision_processing/state_manager.py

from collections import deque, Counter
import time

class StateManager:
    def __init__(self, buffer_size=5, stable_threshold=3):
        self.buffer = deque(maxlen=buffer_size)
        self.stable_threshold = stable_threshold
        self.last_sent_label = None
        self.action_cooldowns = {}  # Track cooldowns for actions

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

    def can_perform_action(self, action_name, cooldown_seconds):
        current_time = time.time()
        last_time = self.action_cooldowns.get(action_name, 0)

        if current_time - last_time >= cooldown_seconds:
            self.action_cooldowns[action_name] = current_time
            print(f"[StateManager] Action '{action_name}' allowed. Cooldown reset.")
            return True

        remaining_cooldown = cooldown_seconds - (current_time - last_time)
        print(f"[StateManager] Action '{action_name}' on cooldown. Remaining time: {remaining_cooldown:.2f} seconds.")
        return False

    def reset_action_cooldown(self, action_name):
        """Forcefully reset the cooldown for a specific action."""
        self.action_cooldowns[action_name] = time.time()
        print(f"[StateManager] Cooldown for action '{action_name}' has been reset.")
