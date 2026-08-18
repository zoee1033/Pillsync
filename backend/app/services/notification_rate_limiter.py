import time
import logging
import threading
from collections import defaultdict, deque
from typing import Dict, Deque

logger = logging.getLogger("RATE_LIMITER")


class NotificationRateLimiter:
    """
    Sliding window rate limiter preventing notification spam per user.
    Enforces max 5 notifications per minute per user.
    If exceeded, delays execution rather than discarding.
    """

    def __init__(self, max_per_minute: int = 5, window_seconds: int = 60):
        self.max_per_minute = max_per_minute
        self.window_seconds = window_seconds
        self._user_windows: Dict[int, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_and_acquire(self, user_id: int) -> float:
        """
        Checks rate limit for user_id using sliding window timestamps.
        Returns delay_seconds (0.0 if allowed immediately, >0.0 if delayed).
        """
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            user_queue = self._user_windows[user_id]

            # Purge timestamps outside sliding window
            while user_queue and user_queue[0] < cutoff:
                user_queue.popleft()

            if len(user_queue) >= self.max_per_minute:
                # Calculate delay until oldest timestamp expires
                oldest = user_queue[0]
                delay_sec = max(0.1, round((oldest + self.window_seconds) - now, 2))
                logger.warning(f"User #{user_id} rate limited. Delaying execution by {delay_sec}s.")

                # Record delayed execution time in sliding window
                user_queue.append(now + delay_sec)
                return delay_sec

            user_queue.append(now)
            return 0.0


# Global Singleton NotificationRateLimiter instance
rate_limiter = NotificationRateLimiter()
