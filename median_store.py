# median_store.py
from bisect import insort
import statistics
from collections import defaultdict

class RollingMedianStore:
    def __init__(self, window_sec=300):
        """
        window_sec = time window in seconds (default = 5 minutes)
        data = dictionary where each key is a user_id and value is a deque of (timestamp, score)
        """
        self.data = defaultdict(list)
        self.window_sec = window_sec

    def add(self, user_id, score, timestamp):
        """
        Add a new score for a user at a given timestamp.
        """
        insort(self.data[user_id], (timestamp, score))

        # Remove old entries outside the 5-minute window
        idx = 0
        while idx < len(self.data[user_id]) and self.data[user_id][idx][0] < timestamp - self.window_sec:
            idx += 1
        self.data[user_id] = self.data[user_id][idx:]

    def median(self, user_id):
        """
        Return the rolling median for a user.
        If no data, return None.
        """
        scores = [s for _, s in self.data.get(user_id, [])]
        return statistics.median(scores) if scores else None

    def num_users(self):
        """
        Return how many unique users are tracked.
        """
        return len(self.data)
