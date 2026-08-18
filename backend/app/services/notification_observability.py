import os
import time
import uuid
import logging
import threading
from datetime import datetime
from collections import deque
from typing import Dict, Any, List, Optional

logger = logging.getLogger("OBSERVABILITY")


class ObservabilityContext:
    def __init__(
        self,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        job_id: str = "medicine_reminders",
        user_id: int = 0,
        reminder_id: int = 0,
        notification_id: int = 0
    ):
        self.trace_id = trace_id or f"tr_{uuid.uuid4().hex[:10]}"
        self.correlation_id = correlation_id or f"corr_{uuid.uuid4().hex[:10]}"
        self.execution_id = execution_id or f"exec_{uuid.uuid4().hex[:10]}"
        self.job_id = job_id
        self.user_id = user_id
        self.reminder_id = reminder_id
        self.notification_id = notification_id
        self.worker_id = f"worker_{os.getpid()}"
        self.thread_id = f"thread_{threading.get_ident()}"

    def to_log_prefix(self) -> str:
        return (
            f"[TraceID={self.trace_id} | CorrID={self.correlation_id} | ExecID={self.execution_id} | "
            f"JobID={self.job_id} | User={self.user_id} | Notif={self.notification_id} | "
            f"Reminder={self.reminder_id} | Worker={self.worker_id} | Thread={self.thread_id}]"
        )


class PerformanceMetricsCollector:
    """
    Thread-safe performance metrics collector storing rolling runtime statistics
    for dispatch latency, P95 metrics, worker utilization, throughput, and error rates.
    """

    def __init__(self, max_samples: int = 500):
        self.max_samples = max_samples
        self._dispatch_latencies: deque = deque(maxlen=max_samples)
        self._fcm_response_times: deque = deque(maxlen=max_samples)
        self._ws_broadcast_latencies: deque = deque(maxlen=max_samples)
        self._db_transaction_times: deque = deque(maxlen=max_samples)
        self._queue_wait_times: deque = deque(maxlen=max_samples)
        self._retry_counts: deque = deque(maxlen=max_samples)
        self._last_successful_reminder: Optional[datetime] = None
        self._last_failed_reminder: Optional[datetime] = None
        self._lock = threading.Lock()

    def record_dispatch_latency(self, latency_ms: float):
        with self._lock:
            self._dispatch_latencies.append(latency_ms)

    def record_fcm_response_time(self, response_ms: float):
        with self._lock:
            self._fcm_response_times.append(response_ms)

    def record_ws_broadcast_latency(self, latency_ms: float):
        with self._lock:
            self._ws_broadcast_latencies.append(latency_ms)

    def record_db_transaction_time(self, time_ms: float):
        with self._lock:
            self._db_transaction_times.append(time_ms)

    def record_queue_wait_time(self, wait_ms: float):
        with self._lock:
            self._queue_wait_times.append(wait_ms)

    def record_retry(self, retries: int):
        with self._lock:
            self._retry_counts.append(retries)

    def record_reminder_success(self):
        with self._lock:
            self._last_successful_reminder = datetime.utcnow()

    def record_reminder_failure(self):
        with self._lock:
            self._last_failed_reminder = datetime.utcnow()

    def _calc_p95(self, sample_deque: deque) -> float:
        if not sample_deque:
            return 0.0
        sorted_samples = sorted(list(sample_deque))
        index = int(0.95 * len(sorted_samples))
        return round(sorted_samples[min(index, len(sorted_samples) - 1)], 2)

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            avg_dispatch = round(sum(self._dispatch_latencies) / len(self._dispatch_latencies), 2) if self._dispatch_latencies else 0.0
            p95_dispatch = self._calc_p95(self._dispatch_latencies)
            avg_fcm = round(sum(self._fcm_response_times) / len(self._fcm_response_times), 2) if self._fcm_response_times else 0.0
            avg_ws = round(sum(self._ws_broadcast_latencies) / len(self._ws_broadcast_latencies), 2) if self._ws_broadcast_latencies else 0.0
            avg_db = round(sum(self._db_transaction_times) / len(self._db_transaction_times), 2) if self._db_transaction_times else 0.0
            avg_wait = round(sum(self._queue_wait_times) / len(self._queue_wait_times), 2) if self._queue_wait_times else 0.0
            avg_retries = round(sum(self._retry_counts) / len(self._retry_counts), 2) if self._retry_counts else 0.0

            return {
                "avg_dispatch_latency_ms": avg_dispatch,
                "p95_dispatch_latency_ms": p95_dispatch,
                "avg_fcm_response_time_ms": avg_fcm,
                "avg_ws_broadcast_latency_ms": avg_ws,
                "avg_db_transaction_time_ms": avg_db,
                "avg_queue_wait_time_ms": avg_wait,
                "avg_retry_count": avg_retries,
                "last_successful_reminder": self._last_successful_reminder.isoformat() if self._last_successful_reminder else None,
                "last_failed_reminder": self._last_failed_reminder.isoformat() if self._last_failed_reminder else None
            }


# Global Singleton MetricsCollector instance
metrics_collector = PerformanceMetricsCollector()
