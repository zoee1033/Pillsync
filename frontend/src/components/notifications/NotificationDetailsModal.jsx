import React, { useEffect, useState } from "react";
import Card from "../common/Card";
import Button from "../common/Button";
import { getReminderById, snoozeReminder } from "../../services/reminderService";
import { createHistory } from "../../services/historyService";
import styles from "./NotificationDetailsModal.module.css";

const NotificationDetailsModal = ({ reminderId, onClose, onRefresh }) => {
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [reminder, setReminder] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!reminderId) {
      setLoading(false);
      return;
    }

    const fetchReminderDetails = async () => {
      setLoading(true);
      setErrorMsg("");
      try {
        const data = await getReminderById(reminderId);
        if (!data || data.status === "Inactive" || data.status === "Completed") {
          setErrorMsg("This reminder is no longer available.");
        } else {
          setReminder(data);
        }
      } catch (err) {
        console.error("Error loading notification reminder:", err);
        setErrorMsg("This reminder is no longer available.");
      } finally {
        setLoading(false);
      }
    };

    fetchReminderDetails();
  }, [reminderId]);

  if (!reminderId) return null;

  const handleAction = async (actionType) => {
    if (!reminder || actionLoading) return;
    setActionLoading(true);

    try {
      const nowIso = new Date().toISOString();
      const medicine = reminder.medicine || {};
      const treatment = medicine.treatment || {};

      if (actionType === "taken") {
        await createHistory({
          treatment_id: treatment.id || medicine.treatment_id,
          medicine_id: medicine.id || reminder.medicine_id,
          reminder_id: reminder.id,
          scheduled_time: reminder.next_trigger_at || nowIso,
          status: "Taken",
          notes: "Marked taken via Notification Details Card",
        });
      } else if (actionType === "snooze") {
        const snoozeMins = reminder.snooze_minutes || 10;
        await snoozeReminder(reminder.id, snoozeMins);
      } else if (actionType === "skip") {
        await createHistory({
          treatment_id: treatment.id || medicine.treatment_id,
          medicine_id: medicine.id || reminder.medicine_id,
          reminder_id: reminder.id,
          scheduled_time: reminder.next_trigger_at || nowIso,
          status: "Skipped",
          skip_reason: "Skipped via Notification Details Card",
          notes: "Occurrence skipped",
        });
      }

      if (onRefresh) {
        await onRefresh();
      }
      onClose();
    } catch (err) {
      console.error(`Error performing ${actionType}:`, err);
      alert(err.response?.data?.detail || `Failed to perform ${actionType}.`);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3>💊 Notification Details</h3>
          <button className={styles.closeBtn} onClick={onClose}>
            ×
          </button>
        </div>

        {loading ? (
          <div className={styles.loadingContainer}>Loading reminder details...</div>
        ) : errorMsg ? (
          <div className={styles.unavailableContainer}>
            <div className={styles.unavailableIcon}>⚠️</div>
            <div className={styles.unavailableText}>{errorMsg}</div>
            <Button variant="outline" onClick={onClose} className={styles.okBtn}>
              OK
            </Button>
          </div>
        ) : reminder ? (
          <div className={styles.cardBody}>
            <div className={styles.medicineBanner}>
              <span className={styles.medIcon}>💊</span>
              <div>
                <h4 className={styles.medName}>
                  {reminder.medicine?.medicine_name || `Medicine #${reminder.medicine_id}`}
                </h4>
                <p className={styles.treatmentName}>
                  Treatment: {reminder.medicine?.treatment?.disease_name || "Prescribed Treatment"}
                </p>
              </div>
            </div>

            <div className={styles.detailsGrid}>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Dosage:</span>
                <span className={styles.detailValue}>{reminder.medicine?.dosage || "1 dose"}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Reminder Time:</span>
                <span className={styles.detailValue}>{reminder.reminder_time || "—"}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Configured Snooze:</span>
                <span className={styles.detailValue}>{reminder.snooze_minutes ? `${reminder.snooze_minutes} mins` : "10 mins"}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Status:</span>
                <span className={styles.statusBadge}>{reminder.status || "Active"}</span>
              </div>
              {reminder.medicine?.instructions && (
                <div className={styles.detailRowFull}>
                  <span className={styles.detailLabel}>Instructions:</span>
                  <span className={styles.detailValue}>{reminder.medicine.instructions}</span>
                </div>
              )}
            </div>

            <div className={styles.actionButtons}>
              <button
                className={`${styles.actionBtn} ${styles.btnTaken}`}
                onClick={() => handleAction("taken")}
                disabled={actionLoading}
              >
                ✅ Taken
              </button>
              <button
                className={`${styles.actionBtn} ${styles.btnSnooze}`}
                onClick={() => handleAction("snooze")}
                disabled={actionLoading}
              >
                😴 Snooze
              </button>
              <button
                className={`${styles.actionBtn} ${styles.btnSkip}`}
                onClick={() => handleAction("skip")}
                disabled={actionLoading}
              >
                ⏭ Skip
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default NotificationDetailsModal;
