# median_store.py
from collections import deque
import time
import statistics

class RollingMedianStore:
    def __init__(self, window_sec=300):
        """
        window_sec = time window in seconds (default = 5 minutes)
        data = dictionary where each key is a user_id and value is a deque of (timestamp, score)
        """
        self.data = {}
        self.window_sec = window_sec

    def add(self, user_id, score, timestamp=None):
        """
        Add a new score for a user at a given timestamp.
        """
        if timestamp is None:
            timestamp = int(time.time())

        dq = self.data.setdefault(user_id, deque())
        dq.append((timestamp, score))

        # Remove old entries outside the 5-minute window
        while dq and dq[0][0] < timestamp - self.window_sec:
            dq.popleft()

    def median(self, user_id):
        """
        Return the rolling median for a user.
        If no data, return None.
        """
        dq = self.data.get(user_id, deque())
        if not dq:
            return None
        scores = [s for _, s in dq]
        return statistics.median(scores)

    def num_users(self):
        """
        Return how many unique users are tracked.
        """
        return len(self.data)
