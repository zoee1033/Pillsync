import logging
import threading
from typing import Dict, List, Callable, Any

logger = logging.getLogger("EVENT_BUS")


class EventType:
    REMINDER_TRIGGERED = "REMINDER_TRIGGERED"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"
    NOTIFICATION_DELIVERED = "NOTIFICATION_DELIVERED"
    NOTIFICATION_READ = "NOTIFICATION_READ"
    NOTIFICATION_FAILED = "NOTIFICATION_FAILED"
    TOKEN_INVALIDATED = "TOKEN_INVALIDATED"
    REMINDER_COMPLETED = "REMINDER_COMPLETED"


class EventBus:
    """
    Lightweight, thread-safe publish-subscribe architecture for notification system events.
    Prevents tight coupling and circular imports across services.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Subscribes a callable handler to a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
        logger.debug(f"[EventBus] Subscribed handler {handler.__name__} to event '{event_type}'")

    def unsubscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Unsubscribes a callable handler from an event type."""
        with self._lock:
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
        logger.debug(f"[EventBus] Unsubscribed handler {handler.__name__} from event '{event_type}'")

    def publish(self, event_type: str, payload: Dict[str, Any]):
        """Publishes an event payload to all registered subscriber callbacks."""
        with self._lock:
            handlers = list(self._subscribers.get(event_type, []))

        if not handlers:
            return

        logger.info(f"[EventBus] Publishing event '{event_type}' to {len(handlers)} handler(s)")
        for handler in handlers:
            try:
                handler(payload)
            except Exception as ex:
                logger.error(f"[EventBus] Handler {handler.__name__} failed processing event '{event_type}': {ex}", exc_info=True)


# Global Singleton EventBus instance
event_bus = EventBus()
