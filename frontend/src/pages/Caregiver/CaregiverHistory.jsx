import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbHistory } from "react-icons/tb";
import { getCaregiverHistory } from "../../services/caregiverService";

const CaregiverHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCaregiverHistory();
        setHistory(data);
      } catch (err) {
        setError("Failed to load medication history for assigned patients.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Caregiver Medication History Log</h2>
          <p className="text-sm text-slate-500">Real-time log of dose completions and missed events for assigned patients.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading history logs...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : history.length === 0 ? (
          <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <TbHistory className="mx-auto text-slate-400 mb-2" size={44} />
            <h3 className="text-base font-semibold text-slate-700">No Medication History Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              No dose history records have been logged yet for your assigned patients.
            </p>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Medicine</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4">Time</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-slate-800">{h.patient_name}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">{h.medicine_name}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{h.date}</td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-700">{h.time}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                        h.status === 'Taken' || h.status === 'Completed' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {h.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500">{h.notes || '—'}</td>
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

export default CaregiverHistory;
