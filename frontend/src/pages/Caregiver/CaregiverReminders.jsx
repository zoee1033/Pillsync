import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbCalendarTime, TbClock } from "react-icons/tb";
import { getCaregiverReminders } from "../../services/caregiverService";

const CaregiverReminders = () => {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReminders = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCaregiverReminders();
        setReminders(data);
      } catch (err) {
        setError("Failed to load assigned patients' reminders.");
      } finally {
        setLoading(false);
      }
    };

    fetchReminders();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Caregiver Reminders Overview</h2>
          <p className="text-sm text-slate-500">View actual scheduled reminder times for all assigned patients.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading reminders...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : reminders.length === 0 ? (
          <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <TbCalendarTime className="mx-auto text-slate-400 mb-2" size={44} />
            <h3 className="text-base font-semibold text-slate-700">No Reminders Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              No active dose reminders are currently set for your assigned patients.
            </p>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Medicine</th>
                  <th className="py-3.5 px-4">Actual Reminder Time</th>
                  <th className="py-3.5 px-4">Repeat</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {reminders.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-slate-800">{r.patient_name}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">{r.medicine_name}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100 text-xs">
                        <TbClock size={14} /> {r.reminder_time}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{r.repeat_type || "Daily"}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                        {r.status || "Active"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </PageContainer>
  );
};

export default CaregiverReminders;
