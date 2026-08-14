import React, { useState, useEffect } from "react";
import { TbX, TbChartPie, TbClock, TbCheck, TbAlertTriangle } from "react-icons/tb";
import api from "../../services/api";
import styles from "./DosageAnalysisModal.module.css";

const DosageAnalysisModal = ({ medicineId, onClose }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (medicineId) {
      fetchAnalysis();
    }
  }, [medicineId]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/medicines/${medicineId}/dosage-analysis`);
      setData(res.data);
    } catch (err) {
      setError("Failed to load dosage analysis.");
    } finally {
      setLoading(false);
    }
  };

  if (!medicineId) return null;

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <button className={styles.closeBtn} onClick={onClose}>
          <TbX size={20} />
        </button>

        {loading ? (
          <div style={{ textAlign: "center", padding: "2rem 0" }}>
            <p style={{ color: "#64748b", fontWeight: 600 }}>Loading Dosage Analysis...</p>
          </div>
        ) : error ? (
          <div style={{ color: "#ef4444", padding: "1.5rem", textAlign: "center" }}>
            <TbAlertTriangle size={32} />
            <p>{error}</p>
          </div>
        ) : (
          <div>
            <h2 className={styles.title}>
              <TbChartPie size={24} style={{ color: "#2563eb", verticalAlign: "middle" }} />{" "}
              {data.medicine_name} Dosage Analysis
            </h2>
            <p className={styles.subtitle}>
              Detailed breakdown of prescribed doses, execution history, and visual schedule timeline.
            </p>

            <div className={styles.statsGrid}>
              <div className={styles.statItem}>
                <span className={styles.statLabel}>Prescribed Doses</span>
                <span className={styles.statValue}>{data.total_prescribed_doses}</span>
              </div>

              <div className={styles.statItem}>
                <span className={styles.statLabel}>Completed Doses</span>
                <span className={styles.statValue} style={{ color: "#10b981" }}>
                  {data.completed_doses}
                </span>
              </div>

              <div className={styles.statItem}>
                <span className={styles.statLabel}>Missed Doses</span>
                <span className={styles.statValue} style={{ color: "#ef4444" }}>
                  {data.missed_doses}
                </span>
              </div>

              <div className={styles.statItem}>
                <span className={styles.statLabel}>Skipped Doses</span>
                <span className={styles.statValue} style={{ color: "#f59e0b" }}>
                  {data.skipped_doses}
                </span>
              </div>
            </div>

            <div className={styles.timelineSection}>
              <div className={styles.timelineTitle}>
                <TbClock size={18} style={{ verticalAlign: "middle", marginRight: "0.4rem" }} />
                Visual Daily Dosage Timeline
              </div>

              <div className={styles.timelineSlots}>
                {data.visual_timeline && data.visual_timeline.length > 0 ? (
                  data.visual_timeline.map((slot, idx) => (
                    <div key={idx} className={`${styles.slotCard} ${slot.status ? styles[slot.status] : ''}`}>
                      <div>
                        <strong style={{ color: "#0f172a" }}>
                          {slot.slot && slot.time && slot.slot !== slot.time ? `${slot.slot} (${slot.time})` : (slot.time || slot.slot)}
                        </strong>
                      </div>

                      {slot.status === "Completed" && (
                        <span className={styles.badgeCompleted}>
                          <TbCheck size={14} style={{ verticalAlign: "middle" }} /> Completed
                        </span>
                      )}

                      {slot.status === "Missed" && (
                        <span className={styles.badgeMissed}>
                          <TbAlertTriangle size={14} style={{ verticalAlign: "middle" }} /> Missed
                        </span>
                      )}

                      {slot.status === "Skipped" && (
                        <span className={styles.badgeMissed}>
                          <TbAlertTriangle size={14} style={{ verticalAlign: "middle" }} /> Skipped
                        </span>
                      )}

                      {slot.status === "Upcoming" && (
                        <span className={styles.badgeUpcoming}>
                          <TbClock size={14} style={{ verticalAlign: "middle" }} /> Upcoming
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <p style={{ color: "#64748b", fontStyle: "italic", padding: "0.5rem 0" }}>
                    No active reminders configured for this medicine.
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DosageAnalysisModal;
