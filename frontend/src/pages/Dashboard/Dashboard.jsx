import React, { useMemo, useState, useEffect } from "react";
import useAuth from "../../hooks/useAuth";
import PageContainer from "../../components/ui/PageContainer";
import SummaryCard from "../../components/ui/SummaryCard";
import StatsCard from "../../components/ui/StatsCard";
import StatusBadge from "../../components/ui/StatusBadge";
import ActionButton from "../../components/ui/ActionButton";
import UpcomingRefillsCard from "../../components/dashboard/UpcomingRefillsCard";
import {
  TbPill,
  TbClock,
  TbPlus,
  TbActivity,
  TbScan,
  TbChartBar,
  TbFlame,
  TbCheck,
  TbAlertCircle,
  TbBell,
  TbCalendarCheck,
  TbSparkles,
  TbChevronRight,
  TbHistory
} from "react-icons/tb";
import { Link } from "react-router-dom";
import api from "../../services/api";

const DashboardContent = () => {
  const { user } = useAuth();
  const currentUser = user || { full_name: "Health Patient", role: "patient" };

  const [analytics, setAnalytics] = useState(null);
  const [reminders, setReminders] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();

    const handleGlobalRefresh = () => {
      fetchDashboardData();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [summaryRes, remindersRes, historyRes] = await Promise.allSettled([
        api.get("/dashboard/summary"),
        api.get("/reminders/"),
        api.get("/history/")
      ]);

      if (summaryRes.status === "fulfilled") {
        setAnalytics(summaryRes.value.data);
      }
      if (remindersRes.status === "fulfilled") {
        setReminders(remindersRes.value.data || []);
      }
      if (historyRes.status === "fulfilled") {
        setHistory(historyRes.value.data || []);
      }
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  const greetingTime = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good Morning";
    if (hour < 18) return "Good Afternoon";
    return "Good Evening";
  }, []);

  const currentDate = useMemo(
    () =>
      new Date().toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      }),
    []
  );

  const stats = analytics || {};

  const completedCount = stats.today_completed || 0;
  const scheduledCount = Math.max(1, stats.today_scheduled || reminders.length || 1);
  const todayProgressPct = Math.min(100, Math.round((completedCount / scheduledCount) * 100));

  const summaries = [
    { title: "Today's Medicines", value: stats.today_scheduled || 0, hint: 'Total scheduled today', icon: <TbPill className="text-[#0F8B6D]" /> },
    { title: "Completed Today", value: stats.today_completed || 0, hint: 'Doses taken', icon: <TbCheck className="text-[#0F8B6D]" /> },
    { title: "Remaining Today", value: stats.remaining_today || 0, hint: 'Doses pending', icon: <TbClock className="text-[#0F8B6D]" /> },
    { title: "Missed Today", value: stats.today_missed || 0, hint: 'Requires attention', icon: <TbAlertCircle className="text-red-500" /> },
    { title: "Current Adherence", value: `${stats.overall_adherence || 100}%`, hint: 'Overall compliance', icon: <TbChartBar className="text-[#0F8B6D]" /> },
    { title: "Current Streak", value: `${stats.current_streak || 0} Days`, hint: '100% adherence streak', icon: <TbFlame className="text-amber-500" /> },
    { title: "Upcoming Refill", value: stats.upcoming_refill_name || 'None', hint: 'First stock low', icon: <TbPill className="text-amber-600" /> },
    { title: "Next Reminder", value: stats.next_reminder || 'None', hint: 'Scheduled time', icon: <TbCalendarCheck className="text-[#0F8B6D]" /> },
    { title: "Unread Notifications", value: stats.unread_notifications || 0, hint: 'Pending alerts', icon: <TbBell className="text-[#0F8B6D]" /> }
  ];

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* 1. Header Section matching PillSync design language */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-800">Dashboard</h2>
            <p className="text-sm text-slate-500">Today's health summary and medication overview.</p>
          </div>
          <div className="flex items-center gap-3">
            <ActionButton as={Link} to="/ocr" variant="primary">
              <TbScan className="inline mr-1.5" /> OCR Scan Prescription
            </ActionButton>
            <ActionButton as={Link} to="/analytics" variant="outline">
              <TbChartBar className="inline mr-1.5" /> Health Analytics
            </ActionButton>
          </div>
        </div>

        {/* 2. Today's Progress Ring & Health Summary Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

          {/* Today's Progress Ring Card */}
          <div className="bg-card border border-border rounded-2xl p-6 flex flex-col items-center justify-center text-center shadow-sm">
            <h3 className="text-sm font-semibold text-text-secondary mb-3">Today's Progress Ring</h3>
            <div className="relative w-36 h-36 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="40" stroke="#e2e8f0" strokeWidth="10" fill="transparent" />
                <circle
                  cx="50" cy="50" r="40"
                  stroke="#0F8B6D" strokeWidth="10"
                  strokeDasharray="251.2"
                  strokeDashoffset={251.2 - (251.2 * todayProgressPct) / 100}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-700 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-2xl font-bold text-text-primary">{todayProgressPct}%</span>
                <span className="text-xs text-text-secondary">{completedCount}/{stats.today_scheduled || reminders.length || 0} Doses</span>
              </div>
            </div>
            <p className="text-xs text-text-secondary mt-3 font-medium">
              {todayProgressPct === 100 ? "🎉 All doses completed today!" : `${stats.remaining_today || 0} doses remaining today`}
            </p>
          </div>

          {/* Summary Cards Grid */}
          <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {summaries.slice(0, 6).map((s) => (
              <SummaryCard key={s.title} title={s.title} value={s.value} hint={s.hint} icon={s.icon} />
            ))}
          </div>
        </div>

        {/* 3. Main Dashboard Body: Left Column (Timeline & Activity) | Right Column (Refills & Next Reminder) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left Column: Medicine Timeline & Activity Feed */}
          <div className="space-y-6 lg:col-span-2">

            {/* 3. Today's Medicine Timeline */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TbClock className="text-[#0F8B6D]" size={22} />
                  <h3 className="text-lg font-semibold text-text-primary">Today's Medicine Timeline</h3>
                </div>
                <Link to="/reminders" className="text-sm text-[#0F8B6D] font-semibold hover:underline flex items-center">
                  Manage Reminders <TbChevronRight size={16} />
                </Link>
              </div>

              {reminders.length === 0 ? (
                /* 7. Meaningful Empty State for Timeline */
                <div className="text-center py-8 px-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <TbPill className="mx-auto text-slate-400 mb-2" size={36} />
                  <p className="text-sm font-semibold text-slate-700">No Reminders Scheduled Today</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    You have no active dose reminders set for today. Add a new treatment or medicine to start tracking.
                  </p>
                  <Link to="/medicines" className="inline-flex items-center gap-1 text-xs font-bold text-[#0F8B6D] mt-3 hover:underline">
                    + Add New Medicine
                  </Link>
                </div>
              ) : (
                <div className="relative pl-6 border-l-2 border-slate-200 space-y-4">
                  {reminders.slice(0, 5).map((item) => (
                    <div key={item.id} className="relative flex items-center justify-between bg-slate-50 border border-slate-100 rounded-xl p-3">
                      <span className="absolute -left-[31px] top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-[#0F8B6D] border-2 border-white" />
                      <div>
                        <div className="text-xs font-semibold text-[#0F8B6D]">{item.reminder_time}</div>
                        <div className="text-sm font-medium text-text-primary">Medicine #{item.medicine_id} ({item.repeat_type})</div>
                      </div>
                      <StatusBadge status={item.status || "Active"} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 6. Recent Activity Timeline Feed */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TbHistory className="text-[#0F8B6D]" size={22} />
                  <h3 className="text-lg font-semibold text-text-primary">Recent Activity Timeline</h3>
                </div>
                <Link to="/history" className="text-sm text-[#0F8B6D] font-semibold hover:underline flex items-center">
                  Full History <TbChevronRight size={16} />
                </Link>
              </div>

              {history.length === 0 ? (
                /* 7. Meaningful Empty State for Activity */
                <div className="text-center py-6 px-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <TbActivity className="mx-auto text-slate-400 mb-2" size={32} />
                  <p className="text-sm font-semibold text-slate-700">No Medication History Logged Yet</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Your recent dose intake logs, stock updates, and reminder events will appear here automatically.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {history.slice(0, 5).map((h) => (
                    <div key={h.id} className="flex items-start gap-3 bg-slate-50 border border-slate-100 rounded-xl p-3">
                      <div className="p-2 bg-[#0F8B6D]/10 text-[#0F8B6D] rounded-lg mt-0.5">
                        <TbActivity size={18} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-text-primary">{h.status}</span>
                          <span className="text-xs text-slate-400">
                            {h.action_time ? new Date(h.action_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </div>
                        <p className="text-xs text-text-secondary mt-0.5">{h.notes || `Log for medicine #${h.medicine_id}`}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Right Column: Next Reminder, Refills & Recommendation Cards */}
          <aside className="space-y-6">

            {/* 5. Enhanced Next Reminder Card */}
            <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
              <div className="flex items-center gap-2 text-indigo-600 mb-2">
                <TbCalendarCheck size={20} />
                <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary">Next Upcoming Reminder</h4>
              </div>
              <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 text-center">
                <div className="text-2xl font-extrabold text-indigo-900">
                  {stats.next_reminder || "None Scheduled"}
                </div>
                <p className="text-xs text-indigo-700 font-medium mt-1">
                  {stats.next_reminder !== "None Scheduled Today" ? "Please take dose with water as prescribed" : "All scheduled reminders for today have passed"}
                </p>
              </div>
            </div>

            {/* Medicine Stock Health Summary Card */}
            <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <TbPill className="text-[#0F8B6D]" size={20} />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary">Medicine Stock Health</h4>
                </div>
                <Link to="/medicines" className="text-xs text-[#0F8B6D] font-semibold hover:underline flex items-center">
                  All Medicines <TbChevronRight size={14} />
                </Link>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <Link
                  to="/medicines"
                  state={{ filterStatus: "Healthy" }}
                  className="p-2.5 bg-emerald-50 border border-emerald-100 rounded-xl hover:bg-emerald-100/60 transition-colors block"
                >
                  <div className="text-lg font-bold text-emerald-700">🟢 {stats.stock_healthy_count || 0}</div>
                  <div className="text-[10px] font-bold text-emerald-800 mt-0.5">Healthy (&gt;15 Days)</div>
                </Link>
                <Link
                  to="/medicines"
                  state={{ filterStatus: "Refill Soon" }}
                  className="p-2.5 bg-amber-50 border border-amber-100 rounded-xl hover:bg-amber-100/60 transition-colors block"
                >
                  <div className="text-lg font-bold text-amber-700">🟡 {stats.stock_needs_refill_count || 0}</div>
                  <div className="text-[10px] font-bold text-amber-800 mt-0.5">Needs Refill (4–15 Days)</div>
                </Link>
                <Link
                  to="/medicines"
                  state={{ filterStatus: "Critical" }}
                  className="p-2.5 bg-red-50 border border-red-100 rounded-xl hover:bg-red-100/60 transition-colors block"
                >
                  <div className="text-lg font-bold text-red-700">🔴 {stats.stock_critical_count || 0}</div>
                  <div className="text-[10px] font-bold text-red-800 mt-0.5">Critical (≤3 Days)</div>
                </Link>
              </div>
            </div>

            {/* 4. Enhanced Upcoming Refill Card */}
            <UpcomingRefillsCard />

            {/* 8. Personalized Recommendation Card */}
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center gap-2 text-amber-700 font-semibold mb-2">
                <TbSparkles size={20} /> Personalized Health Recommendation
              </div>
              <p className="text-xs text-amber-900 leading-relaxed font-medium">
                {stats.current_streak > 3
                  ? `🔥 Excellent discipline! You have maintained a ${stats.current_streak}-day 100% adherence streak. Consistency is key to optimal treatment outcomes!`
                  : stats.today_missed > 0
                  ? `⚠️ You have missed ${stats.today_missed} dose today. Consider setting push notifications or alarm alerts to maintain medication timing accuracy.`
                  : `💡 Tip: Always record your doses promptly after taking them to ensure your refill and adherence metrics stay accurate.`}
              </p>
            </div>

          </aside>
        </div>

      </div>
    </PageContainer>
  );
};

const Dashboard = () => {
  return <DashboardContent />;
};

export default Dashboard;