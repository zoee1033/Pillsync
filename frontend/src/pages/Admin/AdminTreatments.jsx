import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbClipboardList } from "react-icons/tb";
import { getAdminTreatments } from "../../services/adminService";

const AdminTreatments = () => {
  const [treatments, setTreatments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTreatments = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminTreatments();
        setTreatments(data);
      } catch (err) {
        setError("Failed to load platform treatments.");
      } finally {
        setLoading(false);
      }
    };

    fetchTreatments();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">System Treatments Directory</h2>
          <p className="text-sm text-slate-500">View all active and completed treatments across the platform.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading treatments...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Treatment / Disease</th>
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Start Date</th>
                  <th className="py-3.5 px-4">End Date</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {treatments.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-slate-800">{t.disease_name}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-700">{t.patient_name}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{t.start_date || '—'}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{t.end_date || '—'}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        t.status === 'Active' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {t.status}
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

export default AdminTreatments;
