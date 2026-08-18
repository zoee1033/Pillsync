import React, { useState, useEffect } from "react";
import { TbPill, TbRefresh, TbPlus, TbCheck, TbAlertTriangle } from "react-icons/tb";
import api from "../../services/api";
import styles from "./UpcomingRefillsCard.module.css";

const UpcomingRefillsCard = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [restockMedId, setRestockMedId] = useState(null);
  const [restockQty, setRestockQty] = useState(30);
  const [restocking, setRestocking] = useState(false);

  useEffect(() => {
    fetchRefillPredictions();

    const handleGlobalRefresh = () => {
      fetchRefillPredictions();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, []);

  const fetchRefillPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/medicines/refill-predictions");
      const list = res.data || [];
      // Sort by urgency (Critical -> Urgent -> Refill Soon -> Healthy)
      const urgencyMap = { Critical: 0, Urgent: 1, "Refill Soon": 2, Healthy: 3 };
      list.sort((a, b) => (urgencyMap[a.status_category] ?? 4) - (urgencyMap[b.status_category] ?? 4));
      setPredictions(list);
    } catch (err) {
      setError("Unable to load refill predictions.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickRestock = async (medId) => {
    if (!restockQty || restockQty <= 0) return;
    setRestocking(true);
    try {
      await api.put(`/medicines/${medId}`, { quantity: Number(restockQty) });
      setRestockMedId(null);
      await fetchRefillPredictions();
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (err) {
      alert("Failed to update stock: " + (err.response?.data?.detail || err.message));
    } finally {
      setRestocking(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.card}>
        <div className={styles.title}><TbPill className="text-[#0F8B6D]" /> Upcoming Refills</div>
        <p style={{ color: "#64748b", fontSize: "0.9rem", padding: "1rem 0" }}>
          Calculating stock predictions...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.card}>
        <div className={styles.title}><TbPill className="text-[#0F8B6D]" /> Upcoming Refills</div>
        <p style={{ color: "#ef4444", fontSize: "0.875rem", margin: "0.5rem 0" }}>{error}</p>
        <button onClick={fetchRefillPredictions} style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "6px", padding: "0.4rem 0.8rem", cursor: "pointer", fontSize: "0.8rem" }}>
          <TbRefresh /> Retry
        </button>
      </div>
    );
  }

  // Display top tracked medicines (sorted by urgency, including Healthy) up to max 4
  const displayItems = predictions.slice(0, 4);

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.title}>
          <TbPill size={22} style={{ color: "#0F8B6D" }} /> Upcoming Refills
        </div>
        <span style={{ fontSize: "0.78rem", color: "#64748b", fontWeight: 600 }}>
          {predictions.length} Tracked
        </span>
      </div>

      {predictions.length === 0 ? (
        <p style={{ color: "#64748b", fontSize: "0.875rem" }}>
          No active medicines found to calculate refill predictions.
        </p>
      ) : (
        <div className={styles.refillList}>
          {displayItems.map((item) => {
            const isRestockingThis = restockMedId === item.medicine_id;

            return (
              <div key={item.medicine_id} className={styles.refillItem}>
                <div className={styles.itemHeader}>
                  <span className={styles.medName}>
                    {item.badge_icon || "💊"} {item.medicine_name}
                  </span>
                  <span
                    className={styles.statusBadge}
                    style={{
                      backgroundColor: `${item.hex_color || "#0F8B6D"}15`,
                      color: item.hex_color || "#0F8B6D",
                      borderColor: `${item.hex_color || "#0F8B6D"}40`
                    }}
                  >
                    {item.status_category || "Healthy"} ({item.remaining_days} Days Left)
                  </span>
                </div>

                <div className={styles.metaRow}>
                  <span>Stock: <strong>{item.current_stock} Tablets</strong></span>
                  <span>Daily Usage: <strong>{item.daily_consumption || 1}/day</strong></span>
                </div>

                <div className={styles.metaRow} style={{ fontSize: "0.8rem", color: "#64748b" }}>
                  <span>Refill Before: <strong>{item.refill_date || item.refill_recommended_date}</strong></span>
                </div>

                {/* Smart Progress Bar */}
                <div className={styles.progressBarBg}>
                  <div
                    className={styles.progressBarFill}
                    style={{
                      width: `${item.progress_percent || Math.min(100, Math.max(5, (item.remaining_days / 30) * 100))}%`,
                      backgroundColor: item.hex_color || "#10b981"
                    }}
                  ></div>
                </div>

                {/* Restock Inline Form / Action Button */}
                {isRestockingThis ? (
                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
                    <input
                      type="number"
                      min="1"
                      value={restockQty}
                      onChange={(e) => setRestockQty(e.target.value)}
                      style={{ width: "80px", padding: "0.3rem 0.5rem", border: "1px solid #0F8B6D", borderRadius: "6px", fontSize: "0.85rem" }}
                    />
                    <button
                      onClick={() => handleQuickRestock(item.medicine_id)}
                      disabled={restocking}
                      style={{ background: "#0F8B6D", color: "#fff", border: "none", borderRadius: "6px", padding: "0.35rem 0.75rem", fontSize: "0.8rem", cursor: "pointer", fontWeight: 600 }}
                    >
                      {restocking ? "Saving..." : "Confirm Restock"}
                    </button>
                    <button
                      onClick={() => setRestockMedId(null)}
                      style={{ background: "none", border: "none", color: "#64748b", fontSize: "0.8rem", cursor: "pointer" }}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.25rem" }}>
                    <button
                      onClick={() => {
                        setRestockMedId(item.medicine_id);
                        setRestockQty(item.current_stock + 30);
                      }}
                      style={{
                        background: item.remaining_days <= 7 ? "#fef2f2" : "#f8fafc",
                        border: `1px solid ${item.remaining_days <= 7 ? "#fecaca" : "#e2e8f0"}`,
                        color: item.remaining_days <= 7 ? "#dc2626" : "#0F8B6D",
                        borderRadius: "6px",
                        padding: "0.3rem 0.7rem",
                        fontSize: "0.78rem",
                        fontWeight: 700,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.3rem"
                      }}
                    >
                      <TbPlus size={14} /> Restock Stock
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default UpcomingRefillsCard;
