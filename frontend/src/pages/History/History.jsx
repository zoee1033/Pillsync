import React, { useEffect, useState, useCallback } from "react";
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
import { STATUS_META, HISTORY_STATUS } from "../../constants/status";
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

  const loadHistory = useCallback(async (reminderId, treatmentId) => {
    setLoading(true);
    setMessage({ type: "", text: "" });
    try {
      const response = await getHistory();
      let filteredHistory = response || [];

      // Conditional loading logic:
      // if reminder_id exists -> load reminder history
      // else if treatment_id exists -> load treatment history
      // else -> load complete user history
      if (reminderId) {
        filteredHistory = filteredHistory.filter(
          (item) => item.reminder_id === Number(reminderId)
        );
      } else if (treatmentId) {
        filteredHistory = filteredHistory.filter(
          (item) => item.treatment_id === Number(treatmentId)
        );
      }

      setHistoryItems(filteredHistory);
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to load treatment history.",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const reminderId = params.get("reminder_id");
    const state = location.state || {};

    const effectiveTreatment = state.treatment || null;
    const treatmentId = params.get("treatment_id") || effectiveTreatment?.id;

    setSelectedReminder(state.reminder || null);
    setSelectedMedicine(state.medicine || null);
    setSelectedTreatment(effectiveTreatment);

    loadHistory(reminderId, treatmentId);

    const handleGlobalRefresh = () => {
      loadHistory(reminderId, treatmentId);
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, [location.search, location.state, loadHistory]);

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

  const params = new URLSearchParams(location.search);
  const currentReminderId = params.get("reminder_id");
  const currentTreatmentId = params.get("treatment_id") || selectedTreatment?.id;

  return (
    <div className={styles.historyPage}>
      <div className={styles.controlsRow}>
        <Button variant="outline" onClick={() => navigate(-1)}>
          Back
        </Button>
      </div>

      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.pageTitle}>Treatment History</h2>
          <p className={styles.pageSubtitle}>
            {currentReminderId && selectedMedicine?.medicine_name
              ? `View recorded actions for ${selectedMedicine.medicine_name} / ${selectedReminder?.reminder_time || ""}.`
              : currentTreatmentId && selectedTreatment?.disease_name
              ? `View treatment history and milestones for ${selectedTreatment.disease_name}.`
              : "View complete treatment history timeline and milestones."}
          </p>
        </div>
      </div>

      {currentReminderId && selectedReminder ? (
        <div className={styles.detailsGrid}>
          <Card className={styles.detailCard}>
            <div className={styles.cardHeader}>
              <h3>Reminder Overview</h3>
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
          </Card>
        </div>
      ) : currentTreatmentId && selectedTreatment ? (
        <div className={styles.detailsGrid}>
          <Card className={styles.detailCard}>
            <div className={styles.cardHeader}>
              <h3>Treatment Overview</h3>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Disease / Treatment</span>
              <span>{selectedTreatment?.disease_name || "—"}</span>
            </div>
            {selectedTreatment?.doctor_name && (
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Doctor</span>
                <span>{selectedTreatment.doctor_name}</span>
              </div>
            )}
            {selectedTreatment?.start_date && (
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Start Date</span>
                <span>{selectedTreatment.start_date}</span>
              </div>
            )}
            {selectedTreatment?.end_date && (
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>End Date</span>
                <span>{selectedTreatment.end_date}</span>
              </div>
            )}
            {selectedTreatment?.status && (
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Status</span>
                <span>{selectedTreatment.status}</span>
              </div>
            )}
          </Card>
        </div>
      ) : null}

      <Card className={styles.listCard}>
        <div className={styles.cardHeader}>
          <h3>History Timeline</h3>
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
            message="No treatment history or actions recorded yet."
          />
        ) : (
          <div className={styles.historyList}>
            {historyItems.map((item) => {
              const meta = STATUS_META[item.status] || {
                label: item.status,
                icon: "📌",
                className: "statusDefault",
              };

              const medName = item.medicine_name || selectedMedicine?.medicine_name || (item.medicine_id ? `Medicine #${item.medicine_id}` : null);
              const treatName = item.treatment_name || selectedTreatment?.disease_name || `Treatment #${item.treatment_id}`;
              const remTime = item.reminder_time || selectedReminder?.reminder_time;

              const isUserAction = [
                HISTORY_STATUS.TAKEN,
                HISTORY_STATUS.SKIPPED,
                HISTORY_STATUS.MISSED,
                HISTORY_STATUS.SNOOZED,
              ].includes(item.status);

              return (
                <div key={item.id} className={styles.historyItem}>
                  <div className={styles.historyHeader}>
                    <div className={styles.headerLeft}>
                      <span className={styles.statusIcon}>{meta.icon}</span>
                      <div>
                        <div className={styles.historyTitle}>
                          {medName ? `${medName}` : treatName}
                        </div>
                        <div className={styles.historySub}>Treatment: {treatName}</div>
                      </div>
                    </div>
                    <span className={`${styles.statusBadge} ${styles[meta.className] || ""}`}>
                      {meta.label}
                    </span>
                  </div>

                  <div className={styles.historyDetails}>
                    {medName && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Medicine:</span>
                        <span>{medName}</span>
                      </div>
                    )}
                    {item.dosage && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Dosage:</span>
                        <span>{item.dosage}</span>
                      </div>
                    )}
                    {remTime && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Reminder Time:</span>
                        <span>{remTime}</span>
                      </div>
                    )}
                    {item.start_date && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Start Date:</span>
                        <span>{item.start_date}</span>
                      </div>
                    )}
                    {item.end_date && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>End Date:</span>
                        <span>{item.end_date}</span>
                      </div>
                    )}
                    {item.completion_date && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Completion Date:</span>
                        <span>{item.completion_date}</span>
                      </div>
                    )}
                    {item.duration && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Duration:</span>
                        <span>{item.duration}</span>
                      </div>
                    )}
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Event Timestamp:</span>
                      <span>{item.action_time ? new Date(item.action_time).toLocaleString() : "—"}</span>
                    </div>
                    {item.skip_reason && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Skip Reason:</span>
                        <span>{item.skip_reason}</span>
                      </div>
                    )}
                    {item.notes && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Notes:</span>
                        <span>{item.notes}</span>
                      </div>
                    )}
                  </div>

                  {isUserAction && item.medicine_id && item.reminder_id && (
                    <div className={styles.itemActions}>
                      <Button variant="outline" onClick={() => handleUpdateStatus(item.id, "taken")} disabled={actionLoading}>
                        Mark Taken
                      </Button>
                      <Button variant="secondary" onClick={() => handleSkip(item.id)} disabled={actionLoading}>
                        Mark Skipped
                      </Button>
                      <Button variant="outline" onClick={() => handleUpdateStatus(item.id, "missed")} disabled={actionLoading}>
                        Mark Missed
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};

export default History;
