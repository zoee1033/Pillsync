import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import SummaryCard from "../../components/ui/SummaryCard";
import { TbChartBar, TbUsers, TbPill, TbActivity } from "react-icons/tb";
import { getAdminAnalytics } from "../../services/adminService";

const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError("Failed to load platform analytics.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <PageContainer>
        <div className="py-12 text-center text-slate-500 font-medium">Loading Platform Analytics...</div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
      </PageContainer>
    );
  }

  const { medication_health = {}, user_growth = [], active_treatments = 0, active_reminders = 0 } = analytics || {};

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Platform Health & Growth Analytics</h2>
          <p className="text-sm text-slate-500">Comprehensive real-time analytics across users, active treatments, and stock health.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <SummaryCard title="Active Treatments" value={active_treatments} hint="System active treatments" icon={<TbActivity className="text-blue-600" />} />
          <SummaryCard title="Active Reminders" value={active_reminders} hint="Active reminder schedules" icon={<TbChartBar className="text-indigo-600" />} />
          <SummaryCard title="Healthy Medicines" value={medication_health.healthy || 0} hint="Stock healthy count" icon={<TbPill className="text-emerald-600" />} />
        </div>

        {/* User Growth Visual */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="text-base font-bold text-slate-800">User Growth Trends</h3>
          <div className="space-y-3">
            {user_growth.map((ug, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                <span className="font-bold text-slate-800 text-sm">{ug.month}</span>
                <div className="flex items-center gap-4 text-xs font-semibold">
                  <span className="text-emerald-700">Patients: {ug.patients}</span>
                  <span className="text-teal-700">Caregivers: {ug.caregivers}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </PageContainer>
  );
};

export default AdminAnalytics;
