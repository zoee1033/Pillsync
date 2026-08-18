import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import SummaryCard from "../../components/ui/SummaryCard";
import {
  TbUsers,
  TbUserHeart,
  TbUserCheck,
  TbPill,
  TbClipboardList,
  TbCalendarTime,
  TbAlertCircle,
  TbActivity
} from "react-icons/tb";
import { getAdminDashboard } from "../../services/adminService";

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAdminDash = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getAdminDashboard();
        setData(res);
      } catch (err) {
        setError("Failed to load admin platform metrics.");
      } finally {
        setLoading(false);
      }
    };

    fetchAdminDash();
  }, []);

  if (loading) {
    return (
      <PageContainer>
        <div className="py-12 text-center text-slate-500 font-medium">Loading Platform Overview...</div>
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

  const {
    total_users = 0,
    patients_count = 0,
    caregivers_count = 0,
    admins_count = 0,
    active_medicines = 0,
    active_treatments = 0,
    active_reminders = 0,
    medication_health = {},
    critical_alerts = [],
    activity_feed = []
  } = data || {};

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Admin Dashboard</h2>
          <p className="text-sm text-slate-500">Here's an overview of the PillSync platform statistics and medication health.</p>
        </div>

        {/* System Stats Row 1 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <SummaryCard title="Total Users" value={total_users} hint="Registered users" icon={<TbUsers className="text-purple-600" />} />
          <SummaryCard title="Patients" value={patients_count} hint="Patient accounts" icon={<TbUserHeart className="text-emerald-600" />} />
          <SummaryCard title="Caregivers" value={caregivers_count} hint="Caregiver accounts" icon={<TbUserCheck className="text-teal-600" />} />
          <SummaryCard title="Active Meds" value={active_medicines} hint="Prescribed medicines" icon={<TbPill className="text-[#0F8B6D]" />} />
          <SummaryCard title="Treatments" value={active_treatments} hint="Active treatments" icon={<TbClipboardList className="text-blue-600" />} />
          <SummaryCard title="Reminders" value={active_reminders} hint="Active reminders" icon={<TbCalendarTime className="text-indigo-600" />} />
        </div>

        {/* User Distribution & Medication Health Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* User Distribution */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-base font-bold text-slate-800 mb-4">User Role Distribution</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>Patients ({patients_count})</span>
                  <span>{total_users ? Math.round((patients_count / total_users) * 100) : 0}%</span>
                </div>
                <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${total_users ? (patients_count / total_users) * 100 : 0}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>Caregivers ({caregivers_count})</span>
                  <span>{total_users ? Math.round((caregivers_count / total_users) * 100) : 0}%</span>
                </div>
                <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                  <div className="bg-teal-500 h-full rounded-full" style={{ width: `${total_users ? (caregivers_count / total_users) * 100 : 0}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span>Admins ({admins_count})</span>
                  <span>{total_users ? Math.round((admins_count / total_users) * 100) : 0}%</span>
                </div>
                <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
                  <div className="bg-purple-500 h-full rounded-full" style={{ width: `${total_users ? (admins_count / total_users) * 100 : 0}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Platform Medication Health */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-base font-bold text-slate-800 mb-4">System Medication Stock Health</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                <div className="text-2xl font-bold text-emerald-700">🟢 {medication_health.healthy || 0}</div>
                <div className="text-xs font-bold text-emerald-800 mt-1">Healthy</div>
              </div>
              <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl">
                <div className="text-2xl font-bold text-amber-700">🟡 {medication_health.needs_refill || 0}</div>
                <div className="text-xs font-bold text-amber-800 mt-1">Needs Refill</div>
              </div>
              <div className="p-4 bg-red-50 border border-red-100 rounded-xl">
                <div className="text-2xl font-bold text-red-700">🔴 {medication_health.critical || 0}</div>
                <div className="text-xs font-bold text-red-800 mt-1">Critical</div>
              </div>
            </div>
          </div>

        </div>

        {/* Activity & Critical Alerts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* System Activity Feed */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
              <TbActivity className="text-purple-600" size={20} /> Real-Time Activity Feed
            </h3>

            {activity_feed.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No recent activity logged.</p>
            ) : (
              <div className="space-y-3">
                {activity_feed.map((act) => (
                  <div key={act.id} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs">
                    <div>
                      <span className="font-bold text-slate-800">{act.user_name}</span> — <span className="text-slate-600">{act.action} ({act.target})</span>
                    </div>
                    <span className="text-slate-400 font-medium">{act.timestamp}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Critical Alerts */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2 text-red-600">
              <TbAlertCircle size={20} /> System Critical Alerts
            </h3>

            {critical_alerts.length === 0 ? (
              <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl text-center text-xs font-semibold text-emerald-800">
                🎉 Zero critical medicine stock alerts detected across the platform!
              </div>
            ) : (
              <div className="space-y-2.5">
                {critical_alerts.map((ca, idx) => (
                  <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between text-xs">
                    <div>
                      <div className="font-bold text-red-900">{ca.patient_name}: {ca.medicine_name}</div>
                      <div className="text-red-700">Days Remaining: {ca.days_remaining} Days</div>
                    </div>
                    <span className="px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-800">Critical</span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>
    </PageContainer>
  );
};

export default AdminDashboard;
