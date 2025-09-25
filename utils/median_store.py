# median_store.py
from bisect import insort
import statistics
from collections import defaultdict

from db.events import EventDB

class RollingMedianStore:
    def __init__(self, window_sec=300, db_path="events.db"):
        """
        window_sec = time window in seconds (default = 5 minutes)
        data = dictionary where each key is a user_id and value is a deque of (timestamp, score)
        """
        self.data = defaultdict(list)
        self.window_sec = window_sec
        self.db = EventDB(db_path=db_path)

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

        self.db.insert({"user_id": user_id, "timestamp": timestamp, "score": score})

    def median(self, user_id):
        """
        Return the rolling median for a user.
        If no data, return None.
        """
        scores = [s for _, s in self.data.get(user_id, [])]
        return statistics.median(scores)

    def num_users(self):
        """
        Return how many unique users are tracked.
        """
        return len(self.data)
    
    def median_of_median(self):
        """
        Return the median of all users' rolling medians.
        If no users, return None.
        """
        medians = [self.median(user_id) for user_id in self.data if self.median(user_id) is not None]
        if not medians:
            return None
        return statistics.median(medians)
    
