import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PageContainer from "../../components/ui/PageContainer";
import SummaryCard from "../../components/ui/SummaryCard";
import ActionButton from "../../components/ui/ActionButton";
import {
  TbUsers,
  TbUserCheck,
  TbAlertCircle,
  TbAlertTriangle,
  TbPill,
  TbClock,
  TbUserPlus,
  TbChevronRight,
  TbActivity
} from "react-icons/tb";
import { getCaregiverDashboard, linkPatientByEmail } from "../../services/caregiverService";
import useAuth from "../../hooks/useAuth";

const CaregiverDashboard = () => {
  const { user } = useAuth();
  const caregiverName = user?.full_name || "Caregiver";

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [patientEmail, setPatientEmail] = useState("");
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkMsg, setLinkMsg] = useState({ type: "", text: "" });

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCaregiverDashboard();
      setData(res);
    } catch (err) {
      setError("Failed to load caregiver dashboard metrics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleLinkSubmit = async (e) => {
    e.preventDefault();
    if (!patientEmail.trim()) return;

    setLinkLoading(true);
    setLinkMsg({ type: "", text: "" });
    try {
      const res = await linkPatientByEmail(patientEmail);
      setLinkMsg({ type: "success", text: res.message });
      setPatientEmail("");
      fetchDashboard();
      setTimeout(() => setShowLinkModal(false), 1500);
    } catch (err) {
      setLinkMsg({ type: "error", text: err.response?.data?.detail || "Failed to link patient." });
    } finally {
      setLinkLoading(false);
    }
  };

  if (loading) {
    return (
      <PageContainer>
        <div className="p-8 text-center text-slate-500 font-medium">Loading Caregiver Workspace...</div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <div className="p-6 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
      </PageContainer>
    );
  }

  const {
    total_patients = 0,
    healthy_patients = 0,
    needs_attention = 0,
    critical_patients = 0,
    my_patients = [],
    attention_required = [],
    today_activity = [],
    upcoming_reminders = []
  } = data || {};

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-800">
              Good Morning, {caregiverName} 👋
            </h2>
            <p className="text-sm text-slate-500">
              Here's an overview of your patients' medication health and dose tracking.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ActionButton variant="primary" onClick={() => setShowLinkModal(true)}>
              <TbUserPlus className="inline mr-1.5" /> Link Patient
            </ActionButton>
          </div>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard title="Total Patients" value={total_patients} hint="Assigned patients" icon={<TbUsers className="text-[#0F8B6D]" />} />
          <SummaryCard title="Healthy Patients" value={healthy_patients} hint="Medication on track" icon={<TbUserCheck className="text-emerald-600" />} />
          <SummaryCard title="Needs Attention" value={needs_attention} hint="Refill required" icon={<TbAlertTriangle className="text-amber-500" />} />
          <SummaryCard title="Critical Patients" value={critical_patients} hint="Stock low / missed" icon={<TbAlertCircle className="text-red-500" />} />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Left Column: My Patients */}
          <div className="space-y-6 lg:col-span-2">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TbUsers className="text-[#0F8B6D]" size={22} />
                  <h3 className="text-lg font-semibold text-text-primary">My Patients</h3>
                </div>
                <Link to="/caregiver/patients" className="text-sm text-[#0F8B6D] font-semibold hover:underline flex items-center">
                  All Patients <TbChevronRight size={16} />
                </Link>
              </div>

              {my_patients.length === 0 ? (
                <div className="text-center py-10 px-4 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                  <TbUsers className="mx-auto text-slate-400 mb-2" size={40} />
                  <p className="text-sm font-semibold text-slate-700">No Assigned Patients Found</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                    No patients are currently assigned to you. Click 'Link Patient' above to assign a patient by their registered email address.
                  </p>
                  <button
                    onClick={() => setShowLinkModal(true)}
                    className="inline-flex items-center gap-1 text-xs font-bold text-[#0F8B6D] mt-3 hover:underline"
                  >
                    + Link Patient Now
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {my_patients.map((p) => (
                    <div key={p.patient_id} className="border border-slate-200 rounded-xl p-4 bg-white hover:border-[#0F8B6D]/40 transition-all shadow-xs">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-base font-bold text-slate-800">{p.full_name}</h4>
                          <span className="text-xs text-slate-500">{p.active_medicine_count} Active Medicines</span>
                        </div>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                          p.medication_status === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                          p.medication_status === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                          'bg-red-50 text-red-700 border border-red-200'
                        }`}>
                          {p.medication_status === 'Healthy' ? '🟢 Healthy' : p.medication_status === 'Needs Refill' ? '🟡 Needs Refill' : '🔴 Critical'}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-slate-600 mb-1 font-medium">
                          <span>Today's Progress</span>
                          <span className="font-bold text-slate-800">{p.today_progress_pct}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-[#0F8B6D] h-full rounded-full transition-all duration-500"
                            style={{ width: `${p.today_progress_pct}%` }}
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs mt-3 pt-3 border-t border-slate-100">
                        <div>Completed: <strong className="text-slate-800">{p.today_completed}</strong></div>
                        <div>Missed: <strong className="text-slate-800">{p.today_missed}</strong></div>
                        <div className="col-span-2 text-slate-500 truncate">Next: <strong className="text-slate-700">{p.next_reminder}</strong></div>
                      </div>

                      <div className="mt-4 flex justify-end">
                        <Link
                          to={`/caregiver/patients/${p.patient_id}`}
                          className="text-xs font-bold text-[#0F8B6D] hover:underline flex items-center gap-1 bg-[#0F8B6D]/10 px-3 py-1.5 rounded-lg"
                        >
                          View Patient <TbChevronRight size={14} />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Today's Activity */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <TbActivity className="text-[#0F8B6D]" size={22} />
                  <h3 className="text-lg font-semibold text-text-primary">Today's Medication Activity</h3>
                </div>
                <Link to="/caregiver/history" className="text-sm text-[#0F8B6D] font-semibold hover:underline flex items-center">
                  Full History <TbChevronRight size={16} />
                </Link>
              </div>

              {today_activity.length === 0 ? (
                <p className="text-sm text-slate-500 py-4 text-center">No medication activity logged today yet for your assigned patients.</p>
              ) : (
                <div className="space-y-3">
                  {today_activity.map((act) => (
                    <div key={act.id} className="flex items-center justify-between bg-slate-50 border border-slate-100 p-3 rounded-xl">
                      <div>
                        <div className="text-sm font-semibold text-slate-800">{act.patient_name} — {act.medicine_name}</div>
                        <div className="text-xs text-slate-500">{act.time}</div>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                        act.status === 'Completed' || act.status === 'Taken' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {act.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Attention Required & Upcoming Reminders */}
          <aside className="space-y-6">

            {/* Attention Required */}
            <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
              <div className="flex items-center gap-2 text-amber-600 mb-3">
                <TbAlertTriangle size={20} />
                <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary">Attention Required</h4>
              </div>

              {attention_required.length === 0 ? (
                <div className="bg-emerald-50 border border-emerald-100 p-3 rounded-xl text-center">
                  <p className="text-xs font-semibold text-emerald-800">🎉 All assigned patients have healthy medication stock & adherence!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {attention_required.map((att) => (
                    <div key={att.patient_id} className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-amber-900">{att.full_name}</div>
                        <div className="text-[11px] text-amber-700">Status: {att.medication_status} ({att.active_medicine_count} Meds)</div>
                      </div>
                      <Link to={`/caregiver/patients/${att.patient_id}`} className="text-[11px] font-bold text-amber-800 hover:underline">
                        Review →
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming Reminders */}
            <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-indigo-600">
                  <TbClock size={20} />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-text-secondary">Upcoming Reminders</h4>
                </div>
                <Link to="/caregiver/reminders" className="text-xs text-[#0F8B6D] font-semibold hover:underline">
                  All Reminders
                </Link>
              </div>

              {upcoming_reminders.length === 0 ? (
                <p className="text-xs text-slate-500 py-3 text-center">No active upcoming reminders.</p>
              ) : (
                <div className="space-y-2.5">
                  {upcoming_reminders.map((rem) => (
                    <div key={rem.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                      <div>
                        <div className="text-xs font-bold text-slate-800">{rem.patient_name}</div>
                        <div className="text-[11px] text-slate-500">{rem.medicine_name} ({rem.repeat_type})</div>
                      </div>
                      <div className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-1 rounded-lg border border-indigo-100">
                        {rem.reminder_time}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </aside>
        </div>

      </div>

      {/* Link Patient Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-1">Link New Patient</h3>
            <p className="text-xs text-slate-500 mb-4">Enter the registered email address of the patient you want to monitor.</p>

            {linkMsg.text && (
              <div className={`p-3 text-xs rounded-xl mb-3 ${linkMsg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
                {linkMsg.text}
              </div>
            )}

            <form onSubmit={handleLinkSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Patient Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. patient@gmail.com"
                  value={patientEmail}
                  onChange={(e) => setPatientEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:border-[#0F8B6D]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={linkLoading}
                  className="px-4 py-2 text-xs font-semibold text-white bg-[#0F8B6D] hover:bg-[#0D7A60] rounded-xl"
                >
                  {linkLoading ? "Assigning..." : "Assign Patient"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
};

export default CaregiverDashboard;
