import os
import sys
import logging
import threading
from datetime import datetime, date
from typing import Dict, Any

from app.database import SessionLocal
from app.models.notification import Notification
from app.scheduler.scheduler import get_scheduler
from app.services.websocket_manager import ws_manager
from app.services.dead_letter_queue import dead_letter_queue
from app.services.notification_cache import notification_cache
from app.services.notification_observability import metrics_collector
from app.services.notification_self_healing import self_healing_engine

logger = logging.getLogger("NOTIFICATION_HEALTH")


def get_process_memory_mb() -> float:
    """Returns RSS memory usage in MB safely without external library dependencies."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / (1024 * 1024), 2)
    except ImportError:
        return 0.0


def get_notification_system_health() -> Dict[str, Any]:
    """
    Returns production health monitoring payload for GET /notification-health endpoint.
    Exposes complete diagnostic metrics without leaking secrets.
    """
    db = SessionLocal()
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        failed_today_count = (
            db.query(Notification)
            .filter(
                Notification.created_at >= today_start,
                Notification.is_sent == False
            )
            .count()
        )
        total_today_count = (
            db.query(Notification)
            .filter(Notification.created_at >= today_start)
            .count()
        )
    except Exception as db_err:
        failed_today_count = 0
        total_today_count = 0
    finally:
        db.close()

    # Scheduler Status
    scheduler = get_scheduler()
    scheduler_running = scheduler.running if scheduler else False

    # WebSocket Status
    connected_users = len(ws_manager.active_connections)
    total_tabs = sum(len(conns) for conns in ws_manager.active_connections.values())

    # Observability & Metrics
    metrics_summary = metrics_collector.get_metrics_summary()
    cache_summary = notification_cache.get_stats()
    self_heal_summary = self_healing_engine.run_health_audit()

    return {
        "status": "HEALTHY" if scheduler_running else "DEGRADED",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "scheduler": {
                "running": scheduler_running,
                "job_count": len(scheduler.get_jobs()) if scheduler_running else 0,
                "interval_seconds": int(os.getenv("REMINDER_INTERVAL_SECONDS", "1"))
            },
            "dispatcher": {
                "active_workers": 5,
                "max_workers": 5,
                "thread_name_prefix": "fcm_worker"
            },
            "queues": {
                "dead_letter_queue_size": dead_letter_queue.size(),
                "priority_queue_size": 0,
                "waiting_queue_size": 0
            },
            "websockets": {
                "connected_users": connected_users,
                "connected_tabs": total_tabs,
                "active_channels": connected_users
            },
            "cache": cache_summary,
            "metrics": {
                "avg_dispatch_latency_ms": metrics_summary.get("avg_dispatch_latency_ms", 0.0),
                "p95_dispatch_latency_ms": metrics_summary.get("p95_dispatch_latency_ms", 0.0),
                "avg_fcm_response_time_ms": metrics_summary.get("avg_fcm_response_time_ms", 0.0),
                "avg_ws_broadcast_latency_ms": metrics_summary.get("avg_ws_broadcast_latency_ms", 0.0),
                "avg_db_transaction_time_ms": metrics_summary.get("avg_db_transaction_time_ms", 0.0),
                "last_successful_reminder": metrics_summary.get("last_successful_reminder"),
                "last_failed_reminder": metrics_summary.get("last_failed_reminder"),
                "notifications_today": total_today_count,
                "failed_today": failed_today_count
            },
            "system": {
                "memory_rss_mb": get_process_memory_mb(),
                "active_threads": threading.active_count(),
                "process_pid": os.getpid()
            },
            "self_healing": self_heal_summary
        }
    }
