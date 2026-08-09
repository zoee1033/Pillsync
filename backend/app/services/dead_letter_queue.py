import logging
import threading
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("DEAD_LETTER_QUEUE")


class DeadLetterQueueItem:
    def __init__(
        self,
        dlq_id: str,
        notification_id: int,
        user_id: int,
        error: str,
        retry_count: int,
        timestamp: datetime,
        stack_trace_summary: str = "",
        fcm_response: str = "",
        token_status: str = "UNKNOWN"
    ):
        self.dlq_id = dlq_id
        self.notification_id = notification_id
        self.user_id = user_id
        self.error = error
        self.retry_count = retry_count
        self.timestamp = timestamp
        self.stack_trace_summary = stack_trace_summary
        self.fcm_response = fcm_response
        self.token_status = token_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dlq_id": self.dlq_id,
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "error": self.error,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "stack_trace_summary": self.stack_trace_summary,
            "fcm_response": self.fcm_response,
            "token_status": self.token_status
        }


class DeadLetterQueue:
    """
    Dead Letter Queue (DLQ) for capturing, inspecting, and replaying permanently
    failed notifications without silent data loss.
    """

    def __init__(self, max_capacity: int = 1000):
        self.max_capacity = max_capacity
        self._items: Dict[str, DeadLetterQueueItem] = {}
        self._lock = threading.Lock()

    def push(
        self,
        notification_id: int,
        user_id: int,
        error: str,
        retry_count: int,
        stack_trace_summary: str = "",
        fcm_response: str = "",
        token_status: str = "FAILED"
    ) -> str:
        """Pushes a failed notification into the Dead Letter Queue."""
        dlq_id = f"dlq_{uuid.uuid4().hex[:8]}"
        item = DeadLetterQueueItem(
            dlq_id=dlq_id,
            notification_id=notification_id,
            user_id=user_id,
            error=error,
            retry_count=retry_count,
            timestamp=datetime.utcnow(),
            stack_trace_summary=stack_trace_summary,
            fcm_response=fcm_response,
            token_status=token_status
        )

        with self._lock:
            # Enforce max capacity safety bound
            if len(self._items) >= self.max_capacity:
                oldest_key = next(iter(self._items))
                del self._items[oldest_key]
            self._items[dlq_id] = item

        logger.error(f"[DLQ] Notification #{notification_id} for User #{user_id} moved to DLQ ({dlq_id}). Error: {error}")
        return dlq_id

    def get_all() -> List[Dict[str, Any]]:
        """Returns list of all active items in the DLQ."""
        with self._lock:
            return [item.to_dict() for item in self._items.values()]

    def get_by_id(self, dlq_id: str) -> Optional[DeadLetterQueueItem]:
        """Retrieves a specific DLQ item by ID."""
        with self._lock:
            return self._items.get(dlq_id)

    def size(self) -> int:
        """Returns current DLQ size."""
        with self._lock:
            return len(self._items)

    def replay(self, dlq_id: str, db_session=None) -> bool:
        """
        Replays a failed notification from DLQ by re-submitting to dispatcher pool.
        """
        with self._lock:
            item = self._items.get(dlq_id)
            if not item:
                logger.warning(f"[DLQ] Cannot replay: Item '{dlq_id}' not found.")
                return False

        logger.info(f"[DLQ] Replaying failed Notification #{item.notification_id} from DLQ '{dlq_id}'...")
        try:
            from app.scheduler.dispatcher import submit_async_fcm_dispatch
            submit_async_fcm_dispatch(
                user_id=item.user_id,
                reminder_id=0,
                medicine_id=0,
                notification_id=item.notification_id,
                medicine_name="Replayed Notification"
            )
            with self._lock:
                self._items.pop(dlq_id, None)
            return True
        except Exception as ex:
            logger.error(f"[DLQ] Replay failed for DLQ item '{dlq_id}': {ex}")
            return False


# Global Singleton DeadLetterQueue instance
dead_letter_queue = DeadLetterQueue()
