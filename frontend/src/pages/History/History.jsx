import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSkeleton from "../../components/ui/LoadingSkeleton";
import {
  getHistory,
  markTaken,
  markSkipped,
  markMissed,
} from "../../services/historyService";
import styles from "./History.module.css";

const History = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [selectedReminder, setSelectedReminder] = useState(null);
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [selectedTreatment, setSelectedTreatment] = useState(null);

  const loadHistory = async (reminderId) => {
    setLoading(true);
    setMessage({ type: "", text: "" });
    try {
      const response = await getHistory();
      const reminderHistory = reminderId
        ? response.filter((item) => item.reminder_id === Number(reminderId))
        : response;
      setHistoryItems(reminderHistory);
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to load history.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const reminderId = params.get("reminder_id");
    const state = location.state || {};

    setSelectedReminder(state.reminder || null);
    setSelectedMedicine(state.medicine || null);
    setSelectedTreatment(state.treatment || null);

    loadHistory(reminderId);
  }, [location.search, location.state]);

  const handleUpdateStatus = async (historyId, action, reason) => {
    setActionLoading(true);
    setMessage({ type: "", text: "" });
    try {
      let response;
      if (action === "taken") {
        response = await markTaken(historyId);
      } else if (action === "skipped") {
        response = await markSkipped(historyId, reason);
      } else if (action === "missed") {
        response = await markMissed(historyId);
      }
      setMessage({ type: "success", text: `History marked ${action}.` });
      setHistoryItems((prev) => prev.map((item) => (item.id === response.id ? response : item)));
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to update history.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSkip = async (historyId) => {
    const reason = window.prompt("Reason for skipping medicine:");
    if (!reason) {
      return;
    }
    await handleUpdateStatus(historyId, "skipped", reason);
  };

  return (
    <div className={styles.historyPage}>
      <div className={styles.controlsRow}>
        <Button variant="outline" onClick={() => navigate(-1)}>
          Back
        </Button>
      </div>

      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.pageTitle}>History</h2>
          <p className={styles.pageSubtitle}>
            {selectedMedicine?.medicine_name && selectedReminder?.reminder_time
              ? `View recorded actions for ${selectedMedicine.medicine_name} / ${selectedReminder.reminder_time}.`
              : "View all recorded history."}
          </p>
        </div>
      </div>

      {selectedReminder ? (
        <div className={styles.detailsGrid}>
          <Card className={styles.detailCard}>
            <div className={styles.cardHeader}>
              <h3>Reminder</h3>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Medicine</span>
              <span>{selectedMedicine?.medicine_name || "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Treatment</span>
              <span>{selectedTreatment?.disease_name || "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Reminder Time</span>
              <span>{selectedReminder?.reminder_time || "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Status</span>
              <span>{selectedReminder?.status || "—"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Next Reminder</span>
              <span>{selectedReminder?.next_trigger_at ? new Date(selectedReminder.next_trigger_at).toLocaleString() : "—"}</span>
            </div>
          </Card>
        </div>
      ) : null}

      <Card className={styles.listCard}>
        <div className={styles.cardHeader}>
          <h3>History Records</h3>
        </div>

        {message.text && (
          <div className={`${styles.alert} ${message.type === "success" ? styles.alertSuccess : styles.alertError}`}>
            {message.text}
          </div>
        )}

        {loading ? (
          <LoadingSkeleton lines={5} />
        ) : historyItems.length === 0 ? (
          <EmptyState
            title="No history yet"
            message="This reminder has no recorded history yet."
          />
        ) : (
          <div className={styles.historyList}>
            {historyItems.map((item) => (
              <div key={item.id} className={styles.historyItem}>
                <div className={styles.historyHeader}>
                  <div>
                    <div className={styles.historyDate}>{new Date(item.scheduled_time).toLocaleDateString()}</div>
                    <div className={styles.historyMeta}>Action: {item.status}</div>
                  </div>
                  <span className={styles.historyStatus}>{item.status}</span>
                </div>

                <div className={styles.historyDetails}>
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Medicine</span>
                    <span>{selectedMedicine?.medicine_name || `Medicine #${item.medicine_id}`}</span>
                  </div>
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Reminder Time</span>
                    <span>{selectedReminder?.reminder_time || `Reminder #${item.reminder_id}`}</span>
                  </div>
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Date</span>
                    <span>{new Date(item.scheduled_time).toLocaleDateString()}</span>
                  </div>
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Timestamp</span>
                    <span>{new Date(item.action_time).toLocaleString()}</span>
                  </div>
                  {item.notes && (
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Notes</span>
                      <span>{item.notes}</span>
                    </div>
                  )}
                </div>

                <div className={styles.itemActions}>
                  <Button variant="outline" onClick={() => handleUpdateStatus(item.id, "taken")} disabled={actionLoading}>
                    Taken
                  </Button>
                  <Button variant="secondary" onClick={() => handleSkip(item.id)} disabled={actionLoading}>
                    Skipped
                  </Button>
                  <Button variant="outline" onClick={() => handleUpdateStatus(item.id, "missed")} disabled={actionLoading}>
                    Missed
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default History;
