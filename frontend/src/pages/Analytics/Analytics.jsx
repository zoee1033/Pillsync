import React, { useState, useEffect } from "react";
import {
  TbChartBar,
  TbFlame,
  TbPercentage,
  TbChecklist,
  TbAlertCircle,
  TbRefresh,
  TbCalendar,
  TbPill,
  TbTrophy,
  TbTrendingUp,
  TbTrendingDown
} from "react-icons/tb";
import api from "../../services/api";
import styles from "./Analytics.module.css";

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();

    const handleGlobalRefresh = () => {
      fetchAnalytics();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/analytics");
      setData(res.data);
    } catch (err) {
      setError("Failed to load medication adherence analytics. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: "center", padding: "4rem 0" }}>
          <div style={{ fontSize: "1.2rem", fontWeight: 600, color: "#64748b" }}>
            Computing Health Insights & Medication Adherence...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div style={{ background: "#fef2f2", border: "1px solid #fecaca", padding: "1.5rem", borderRadius: "12px", color: "#991b1b" }}>
          <TbAlertCircle size={24} style={{ verticalAlign: "middle", marginRight: "0.5rem" }} />
          {error}
          <button
            onClick={fetchAnalytics}
            style={{ marginLeft: "1rem", background: "#ef4444", color: "#fff", border: "none", padding: "0.5rem 1rem", borderRadius: "8px", cursor: "pointer" }}
          >
            <TbRefresh size={16} /> Retry
          </button>
        </div>
      </div>
    );
  }

  const {
    daily_adherence = 100,
    weekly_adherence = 100,
    monthly_adherence = 100,
    overall_adherence = 100,
    average_daily_adherence = 100,
    average_weekly_adherence = 100,
    current_streak = 0,
    longest_streak = 0,
    best_adherence_day = "Today (100%)",
    worst_adherence_day = "None",
    most_missed_medicine = "None",
    highest_missed_rate_medicine = "None",
    medicine_refill_first = "None",
    treatment_closest_completion = "None",
    chart_data = [],
    quick_stats = {}
  } = data || {};

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          <TbChartBar size={28} /> Health Insights & Medication Analytics
        </h1>
        <p className={styles.subtitle}>
          Actionable health analytics computed strictly on demand from PostgreSQL data.
        </p>
      </div>

      {/* Primary Adherence Metrics */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Average Daily Adherence</span>
          <span className={styles.statValue}>{average_daily_adherence}%</span>
          <span className={styles.statSubtext}>Today's dose compliance</span>
        </div>

        <div className={styles.statCard}>
          <span className={styles.statLabel}>Average Weekly Adherence</span>
          <span className={styles.statValue}>{average_weekly_adherence}%</span>
          <span className={styles.statSubtext}>Last 7 days performance</span>
        </div>

        <div className={styles.statCard}>
          <span className={styles.statLabel}>Overall Adherence</span>
          <span className={styles.statValue}>{overall_adherence}%</span>
          <span className={styles.statSubtext}>All-time compliance</span>
        </div>

        <div className={styles.statCard}>
          <span className={styles.statLabel}>Current Streak</span>
          <span className={styles.statValue} style={{ color: "#f59e0b", display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <TbFlame size={28} /> {current_streak} Days
          </span>
          <span className={styles.statSubtext} style={{ color: "#64748b" }}>Longest Streak: {longest_streak} Days</span>
        </div>
      </div>

      {/* Actionable Health Insights Grid */}
      <div style={{ background: "#ffffff", borderRadius: "16px", padding: "1.5rem", border: "1px solid #e2e8f0", marginBottom: "1.5rem", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#0f172a", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <TbTrophy style={{ color: "#f59e0b" }} /> Actionable Health Insights
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #ef4444" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Most Missed Medicine</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#991b1b", marginTop: "0.25rem" }}>{most_missed_medicine}</div>
          </div>

          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #10b981" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Best Adherence Day</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#065f46", marginTop: "0.25rem" }}>{best_adherence_day}</div>
          </div>

          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #f59e0b" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Worst Adherence Day</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#92400e", marginTop: "0.25rem" }}>{worst_adherence_day}</div>
          </div>

          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #3b82f6" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Medicine Needing Refill First</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e40af", marginTop: "0.25rem" }}>{medicine_refill_first}</div>
          </div>

          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #8b5cf6" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Treatment Closest to Completion</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#5b21b6", marginTop: "0.25rem" }}>{treatment_closest_completion}</div>
          </div>

          <div style={{ padding: "1rem", background: "#f8fafc", borderRadius: "12px", borderLeft: "4px solid #ec4899" }}>
            <span style={{ fontSize: "0.85rem", color: "#64748b", fontWeight: 600 }}>Highest Missed Rate Medicine</span>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#9d174d", marginTop: "0.25rem" }}>{highest_missed_rate_medicine}</div>
          </div>
        </div>
      </div>

      {/* Bar Chart Section */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartCard} style={{ width: "100%" }}>
          <div className={styles.chartTitle}>
            <span>Daily Medicine Taken vs Missed (Past 7 Days)</span>
          </div>

          <div className={styles.barChartContainer}>
            {chart_data.map((item, idx) => {
              const maxVal = Math.max(1, ...chart_data.map(d => d.taken + d.missed));
              const takenHeight = (item.taken / maxVal) * 160;
              const missedHeight = (item.missed / maxVal) * 160;

              return (
                <div key={idx} className={styles.barGroup}>
                  <div className={styles.bars}>
                    <div
                      className={styles.barTaken}
                      style={{ height: `${Math.max(8, takenHeight)}px` }}
                      title={`Taken: ${item.taken}`}
                    ></div>
                    <div
                      className={styles.barMissed}
                      style={{ height: `${Math.max(4, missedHeight)}px` }}
                      title={`Missed: ${item.missed}`}
                    ></div>
                  </div>
                  <span className={styles.barLabel}>{item.day}</span>
                </div>
              );
            })}
          </div>

          <div className={styles.legend}>
            <span><span className={styles.legendDotTaken}></span> Taken Doses</span>
            <span><span className={styles.legendDotMissed}></span> Missed Doses</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
