import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSkeleton from "../../components/ui/LoadingSkeleton";
import {
  getNotifications,
  performNotificationAction,
} from "../../services/notificationService";
import styles from "./Notifications.module.css";
import api from "../../services/api";

const Notifications = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const loadNotifications = async () => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      const response = await getNotifications();
      console.log("1. API response:", response);
      console.log(`[TRACE ${new Date().toISOString()}] [STAGE 11: NOTIFICATIONS_JSX_REFRESH] Notifications.jsx loadNotifications() fetched ${response?.length || 0} notifications.`, response);
      const data = response || [];
      setNotifications(data);
      console.log("2. notifications state immediately after setNotifications:", data);
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to load notifications.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();

    const handleGlobalRefresh = () => {
      console.log(`[TRACE ${new Date().toISOString()}] Notifications.jsx handleGlobalRefresh triggered by pillsync_refresh_ui event.`);
      loadNotifications();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, []);

  const handleAction = async (notification, actionType) => {
    setActionLoading(true);
    setMessage({ type: "", text: "" });

    try {
      if (actionType === "delete") {
        const confirmed = window.confirm("Delete this notification?");
        if (!confirmed) {
          setActionLoading(false);
          return;
        }
      }

      const res = await performNotificationAction(notification.id, actionType);

      // Optimistic / immediate state update to prevent stale React UI
      if (actionType === "delete") {
        setNotifications((prev) => prev.filter((n) => n.id !== notification.id));
      } else {
        setNotifications((prev) =>
          prev.map((n) =>
            n.id === notification.id
              ? (res && typeof res === "object" && res.id ? res : { ...n, is_read: true })
              : n
          )
        );
      }

      setMessage({
        type: "success",
        text:
          actionType === "taken"
            ? "Dose marked as taken."
            : actionType === "skipped"
              ? "Dose marked as skipped."
              : actionType === "snooze"
                ? "Reminder snoozed."
                : "Notification deleted.",
      });
      await loadNotifications();
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || `Failed to perform ${actionType}.`,
      });
    } finally {
      setActionLoading(false);
    }
  };

  console.log("3. notifications state during render:", notifications);

  return (
    <div className={styles.notificationsPage}>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.pageTitle}>Notifications</h2>
          <p className={styles.pageSubtitle}>
            View and manage all reminder notifications across your treatments.
          </p>
        </div>
      </div>

      <Card className={styles.notificationSummary}>
        <div className={styles.summaryRow}>
          <div>
            <div className={styles.summaryLabel}>Unread</div>
            <div className={styles.summaryValue}>
              {notifications.filter((item) => !item.is_read).length}
            </div>
          </div>
          <div>
            <div className={styles.summaryLabel}>Total</div>
            <div className={styles.summaryValue}>{notifications.length}</div>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  await api.put("/notifications/read");
                  loadNotifications();
                } catch (e) {
                  console.error(e);
                }
              }}
              disabled={loading}
            >
              Mark All as Read
            </Button>
            <Button variant="outline" onClick={loadNotifications} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      <Card className={styles.listCard}>
        <div className={styles.cardHeader}>
          <h3>Notification Feed</h3>
        </div>

        {message.text && (
          <div className={`${styles.alert} ${message.type === "success" ? styles.alertSuccess : styles.alertError}`}>
            {message.text}
          </div>
        )}

        {loading ? (
          <LoadingSkeleton lines={6} />
        ) : notifications.length === 0 ? (
          <EmptyState
            title="No notifications yet"
            message="Notifications are generated by due reminders. Enable reminders and open this page to see them here."
            action={
              <Button variant="secondary" onClick={() => navigate("/reminders")}>Browse Reminders</Button>
            }
          />
        ) : (
          <div className={styles.notificationList}>
            {notifications.map((notification) => {
              console.log("4. notification.id:", notification.id);
              console.log("5. notification.is_read:", notification.is_read);
              console.log("6. notification.is_sent:", notification.is_sent);
              console.log("7. notification.action_status:", notification.action_status);

              return (
                <div
                  key={notification.id}
                  className={`${styles.notificationItem} ${notification.is_read ? styles.read : ""}`}
                >
                  <div className={styles.notificationHeader}>
                    <div>
                      <div className={styles.notificationTitle}>{notification.title}</div>
                      <div className={styles.notificationType}>{notification.notification_type}</div>
                    </div>
                    <div className={styles.notificationMeta}>
                      <span>{new Date(notification.created_at).toLocaleString()}</span>
                      <span className={notification.is_read ? styles.statusBadgeRead : styles.statusBadgeUnread}>
                        {notification.is_read ? "✓ Action Completed / Read" : notification.is_sent ? "Sent" : "Pending"}
                      </span>
                    </div>
                  </div>

                  <div className={styles.notificationMessage}>{notification.message}</div>

                  <div className={styles.itemActions}>
                    {!notification.is_read && notification.notification_type === "Refill" ? (
                      <Button
                        variant="primary"
                        onClick={() => navigate("/medicines")}
                      >
                        🛒 Restock Now
                      </Button>
                    ) : !notification.is_read ? (
                      <>
                        <Button
                          variant="outline"
                          onClick={() => handleAction(notification, "taken")}
                          disabled={actionLoading}
                        >
                          ✅ Taken
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleAction(notification, "skipped")}
                          disabled={actionLoading}
                        >
                          ⏭ Skipped
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleAction(notification, "snooze")}
                          disabled={actionLoading}
                        >
                          😴 Snooze
                        </Button>
                      </>
                    ) : null}
                    <Button
                      variant="secondary"
                      onClick={() => handleAction(notification, "delete")}
                      disabled={actionLoading}
                    >
                      🗑 Delete
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};

export default Notifications;
