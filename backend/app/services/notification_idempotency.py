import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Set

logger = logging.getLogger("IDEMPOTENCY")


class IdempotencyEngine:
    """
    Idempotency Engine for preventing duplicate notification creation, duplicate history entries,
    and duplicate FCM push dispatches across concurrent thread executions.
    """

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self._processed_hashes: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def generate_execution_id(self, user_id: int, reminder_id: int, scheduled_time: datetime) -> str:
        """Generates deterministic execution_id string."""
        time_str = scheduled_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(scheduled_time, datetime) else str(scheduled_time)
        return f"exec_{user_id}_{reminder_id}_{time_str}"

    def generate_notification_hash(self, user_id: int, reminder_id: int, scheduled_time: datetime) -> str:
        """Computes SHA-256 hash derived from (user_id, reminder_id, scheduled_time)."""
        exec_id = self.generate_execution_id(user_id, reminder_id, scheduled_time)
        return hashlib.sha256(exec_id.encode("utf-8")).hexdigest()

    def is_duplicate(self, user_id: int, reminder_id: int, scheduled_time: datetime) -> bool:
        """
        Checks whether the same reminder execution has already processed within the retention window.
        Purges expired hash keys atomically.
        """
        notif_hash = self.generate_notification_hash(user_id, reminder_id, scheduled_time)
        now = datetime.utcnow()

        with self._lock:
            # Purge expired entries
            cutoff = now - timedelta(minutes=self.retention_minutes)
            expired_keys = [k for k, v in self._processed_hashes.items() if v < cutoff]
            for k in expired_keys:
                del self._processed_hashes[k]

            if notif_hash in self._processed_hashes:
                from app.config import settings
                if settings.ENABLE_VERBOSE_NOTIFICATION_LOGS:
                    logger.debug(f"[Notification] Duplicate skipped for User #{user_id}, Reminder #{reminder_id} (Hash: {notif_hash[:8]}...)")
                return True

            return False

    def mark_processed(self, user_id: int, reminder_id: int, scheduled_time: datetime):
        """Registers notification execution hash to prevent future duplicate processing."""
        notif_hash = self.generate_notification_hash(user_id, reminder_id, scheduled_time)
        with self._lock:
            self._processed_hashes[notif_hash] = datetime.utcnow()


# Global Singleton IdempotencyEngine instance
idempotency_engine = IdempotencyEngine()
