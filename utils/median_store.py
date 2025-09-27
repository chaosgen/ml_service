import heapq
import statistics
from collections import defaultdict
from line_profiler import profile

from db.events import EventDB


class RollingMedianStore:
    def __init__(self, window_sec=300, db_path="events.db"):
        """
        window_sec = time window in seconds (default = 5 minutes)
        For each user_id:
          - self.data[user_id] = {
                "low": max-heap (store as negative values),
                "high": min-heap,
                "events": list[(timestamp, score)] sorted by arrival
            }
        """
        self.data = defaultdict(lambda: {"low": [], "high": [], "events": []})
        self.window_sec = window_sec
        self.db = EventDB(db_path=db_path)

    # ---- internal helpers ----

    def _rebalance(self, user):
        """Keep len(low) >= len(high) and difference ≤1."""
        low = user["low"]
        high = user["high"]
        if len(low) > len(high) + 1:
            # move one from low to high
            heapq.heappush(high, -heapq.heappop(low))
        elif len(high) > len(low):
            heapq.heappush(low, -heapq.heappop(high))

    def _add_score(self, user, score):
        """Push score to one of the heaps."""
        if not user["low"] or score <= -user["low"][0]:
            heapq.heappush(user["low"], -score)
        else:
            heapq.heappush(user["high"], score)
        self._rebalance(user)

    def _remove_old(self, user, current_ts):
        """Lazy removal: just drop expired from the front if it matches heap tops."""
        window_start = current_ts - self.window_sec
        events = user["events"]

        # Pop from events list while too old
        while events and events[0][0] < window_start:
            old_ts, old_score = events.pop(0)
            # lazy removal: we don't rebuild; just record count
            # if the old_score is at top of a heap, pop it out
            if user["low"] and -user["low"][0] == old_score:
                heapq.heappop(user["low"])
            elif user["high"] and user["high"][0] == old_score:
                heapq.heappop(user["high"])
            # We don't rebalance yet — optional small rebalance here

        self._rebalance(user)


    # ---- public API ----

    @profile
    def add(self, user_ids, scores, timestamps):
        """
        Add a new score for a user at a given timestamp.
        """
        for user_id, score, timestamp in zip(user_ids, scores, timestamps):
            user = self.data[user_id]
            # record event
            user["events"].append((timestamp, score))
            # remove old
            self._remove_old(user, timestamp)
            # add to heaps
            self._add_score(user, score)

        self.db.insert_batch(user_ids, timestamps, scores)

    def median(self, user_id):
        """
        Return the rolling median for a user.
        If no data, return None.
        """
        user = self.data.get(user_id)
        if not user or not user["low"]:
            return None
        low = user["low"]
        high = user["high"]
        if len(low) == len(high):
            return (-low[0] + high[0]) / 2.0
        return float(-low[0])

    def num_users(self):
        """
        Return how many unique users are tracked.
        """
        return len(self.data)

    def median_of_medians(self):
        """
        Return the median of all users' rolling medians.
        If no users, return None.
        """
        medians = [self.median(uid) for uid in self.data if self.median(uid) is not None]
        if not medians:
            return None
        return statistics.median(medians)
