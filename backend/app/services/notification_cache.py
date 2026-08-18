import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger("NOTIFICATION_CACHE")


class NotificationCache:
    """
    In-memory thread-safe cache for notification payloads and unread counts per user.
    Designed with a clean interface that remains 100% Redis-ready for multi-instance clusters.
    """

    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._unread_count_cache: Dict[int, Tuple[int, datetime]] = {}
        self._recent_notifications_cache: Dict[int, Tuple[List[Dict[str, Any]], datetime]] = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get_unread_count(self, user_id: int) -> Optional[int]:
        """Gets cached unread count if valid and not expired."""
        now = datetime.utcnow()
        with self._lock:
            if user_id in self._unread_count_cache:
                count, expiry = self._unread_count_cache[user_id]
                if now < expiry:
                    self._hits += 1
                    return count
                else:
                    del self._unread_count_cache[user_id]
            self._misses += 1
            return None

    def set_unread_count(self, user_id: int, count: int, ttl_seconds: Optional[int] = None):
        """Caches unread count for user_id."""
        ttl = ttl_seconds or self.default_ttl
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        with self._lock:
            self._unread_count_cache[user_id] = (count, expiry)

    def get_recent_notifications(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Gets cached recent notifications list for user_id."""
        now = datetime.utcnow()
        with self._lock:
            if user_id in self._recent_notifications_cache:
                data, expiry = self._recent_notifications_cache[user_id]
                if now < expiry:
                    self._hits += 1
                    return data
                else:
                    del self._recent_notifications_cache[user_id]
            self._misses += 1
            return None

    def set_recent_notifications(self, user_id: int, data: List[Dict[str, Any]], ttl_seconds: Optional[int] = None):
        """Caches recent notifications list for user_id."""
        ttl = ttl_seconds or self.default_ttl
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        with self._lock:
            self._recent_notifications_cache[user_id] = (data, expiry)

    def invalidate(self, user_id: int):
        """Invalidates all cached entries for user_id when notification data changes."""
        with self._lock:
            self._unread_count_cache.pop(user_id, None)
            self._recent_notifications_cache.pop(user_id, None)
        logger.debug(f"[NotificationCache] Invalidated cache for User #{user_id}")

    def clear_all(self):
        """Clears all cached entries."""
        with self._lock:
            self._unread_count_cache.clear()
            self._recent_notifications_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache hit/miss statistics and hit ratio."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = round((self._hits / float(total) * 100.0), 1) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_queries": total,
                "hit_ratio_percent": hit_ratio,
                "unread_cache_keys": len(self._unread_count_cache),
                "recent_cache_keys": len(self._recent_notifications_cache)
            }


# Global Singleton NotificationCache instance
notification_cache = NotificationCache()
