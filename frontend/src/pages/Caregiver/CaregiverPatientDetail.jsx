import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import PageContainer from "../../components/ui/PageContainer";
import SummaryCard from "../../components/ui/SummaryCard";
import {
  TbUser,
  TbPill,
  TbClock,
  TbHistory,
  TbBell,
  TbArrowLeft,
  TbActivity,
  TbAlertCircle
} from "react-icons/tb";
import { getCaregiverPatientDetail } from "../../services/caregiverService";

const CaregiverPatientDetail = () => {
  const { patientId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getCaregiverPatientDetail(patientId);
        setData(res);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load patient detail or unauthorized.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [patientId]);

  if (loading) {
    return (
      <PageContainer>
        <div className="py-12 text-center text-slate-500 font-medium">Loading patient details...</div>
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <div className="space-y-4">
          <Link to="/caregiver/patients" className="inline-flex items-center gap-1 text-xs font-semibold text-[#0F8B6D] hover:underline">
            <TbArrowLeft size={16} /> Back to My Patients
          </Link>
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        </div>
      </PageContainer>
    );
  }

  const {
    patient_profile = {},
    medication_health = {},
    active_medicines = [],
    today_reminders = [],
    medication_history = [],
    notifications = []
  } = data || {};

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* Back Link & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <Link to="/caregiver/patients" className="inline-flex items-center gap-1 text-xs font-semibold text-[#0F8B6D] hover:underline mb-2">
              <TbArrowLeft size={16} /> Back to Patients List
            </Link>
            <h2 className="text-2xl font-bold tracking-tight text-slate-800">
              {patient_profile.full_name || `Patient #${patientId}`}
            </h2>
            <p className="text-sm text-slate-500">{patient_profile.email} • Assigned Patient Detail Monitoring</p>
          </div>
          <div>
            <span className={`px-3 py-1.5 rounded-full text-xs font-bold ${
              medication_health.medication_status === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
              medication_health.medication_status === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
              'bg-red-50 text-red-700 border border-red-200'
            }`}>
              Overall Status: {medication_health.medication_status}
            </span>
          </div>
        </div>

        {/* Patient Profile & Overview Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Profile Details Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-slate-800 font-bold text-base border-b border-slate-100 pb-3">
              <TbUser className="text-[#0F8B6D]" size={20} /> Patient Health Profile
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div><span className="text-slate-500">Gender:</span> <strong className="text-slate-800">{patient_profile.gender || 'Not specified'}</strong></div>
              <div><span className="text-slate-500">Age:</span> <strong className="text-slate-800">{patient_profile.age || 'N/A'}</strong></div>
              <div><span className="text-slate-500">Blood Group:</span> <strong className="text-slate-800">{patient_profile.blood_group || 'N/A'}</strong></div>
              <div><span className="text-slate-500">Phone:</span> <strong className="text-slate-800">{patient_profile.phone || 'N/A'}</strong></div>
              <div className="col-span-2"><span className="text-slate-500">Conditions:</span> <strong className="text-slate-800">{patient_profile.medical_conditions || 'None listed'}</strong></div>
              <div className="col-span-2"><span className="text-slate-500">Allergies:</span> <strong className="text-slate-800">{patient_profile.allergies || 'None listed'}</strong></div>
              <div className="col-span-2"><span className="text-slate-500">Emergency Contact:</span> <strong className="text-slate-800">{patient_profile.emergency_contact || 'N/A'}</strong></div>
            </div>
          </div>

          {/* Health Stats */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <SummaryCard title="Active Medicines" value={active_medicines.length} hint="Currently prescribed" icon={<TbPill className="text-[#0F8B6D]" />} />
            <SummaryCard title="Today's Progress" value={`${medication_health.today_progress_pct || 0}%`} hint="Dose compliance" icon={<TbActivity className="text-emerald-600" />} />
            <SummaryCard title="Today Missed Doses" value={medication_health.today_missed || 0} hint="Doses missed" icon={<TbAlertCircle className="text-red-500" />} />
          </div>
        </div>

        {/* Active Medicines Section */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
          <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
            <TbPill className="text-[#0F8B6D]" size={22} /> Active Medicines & Refill Countdown
          </h3>

          {active_medicines.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-4">No active medicines currently prescribed for this patient.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {active_medicines.map((m) => (
                <div key={m.medicine_id} className="border border-slate-200 rounded-xl p-4 bg-slate-50">
                  <div className="flex items-start justify-between">
                    <span className="font-bold text-slate-800 text-base">{m.badge_icon} {m.medicine_name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      m.status_category === 'Healthy' ? 'bg-emerald-100 text-emerald-800' :
                      m.status_category === 'Needs Refill' ? 'bg-amber-100 text-amber-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {m.status_category} ({m.remaining_days} Days Left)
                    </span>
                  </div>
                  <div className="mt-3 text-xs text-slate-600 space-y-1">
                    <div>Current Stock: <strong>{m.current_stock} Tablets</strong></div>
                    <div>Daily Usage: <strong>{m.daily_consumption}/day</strong></div>
                    <div>Refill Date: <strong>{m.refill_date}</strong></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Today's Reminders & History Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Today's Reminders (Real Times) */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <TbClock className="text-[#0F8B6D]" size={22} /> Prescribed Reminders
            </h3>

            {today_reminders.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No reminders set for this patient.</p>
            ) : (
              <div className="space-y-3">
                {today_reminders.map((r) => (
                  <div key={r.id} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-xl">
                    <div>
                      <div className="text-sm font-semibold text-slate-800">{r.medicine_name}</div>
                      <div className="text-xs text-slate-500">Repeat: {r.repeat_type}</div>
                    </div>
                    <div className="text-xs font-bold text-indigo-700 bg-indigo-50 px-3 py-1 rounded-lg border border-indigo-100">
                      {r.reminder_time}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Medication History */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
            <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
              <TbHistory className="text-[#0F8B6D]" size={22} /> Medication History Log
            </h3>

            {medication_history.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No history records logged yet.</p>
            ) : (
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {medication_history.map((h) => (
                  <div key={h.id} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs">
                    <div>
                      <div className="font-semibold text-slate-800">{h.medicine_name}</div>
                      <div className="text-slate-500">{h.date} at {h.scheduled_time}</div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full font-bold ${
                      h.status === 'Taken' || h.status === 'Completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {h.status}
                    </span>
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

export default CaregiverPatientDetail;
